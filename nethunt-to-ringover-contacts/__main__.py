import enum
import os
import re
import csv
import json
import dotenv
import requests

# Load environment variables
dotenv.load_dotenv()
HOST = "https://nethunt.com/api"
USER = os.environ.get('NH_USER')
PASS = os.environ.get('NH_PASS')
FOLDER_ID = os.environ.get('NH_FOLDER_ID')
KEY = os.environ.get('RO_KEY')

# Create session for nethunt
client_nethunt = requests.Session()
client_nethunt.auth = (USER, PASS)
client_nethunt.headers.update({'accept': 'application/json'})

# Create session for ringover
client_ringover = requests.Session()
client_ringover.headers.update({'Authorization': KEY})
client_ringover.headers.update({"Content-Type": "application/json"})


def nethunt_to_ringover_customer():
    nethunt_customers = get_nethunt_customers()

    csv_file = open("nethunt-to-ringover-dump.csv", "w", newline="")
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(["id", "nethunt_phone", "ringover_phone", "status"])

    for idx, nethunt_customer in enumerate(nethunt_customers):
        synced = False
        nethunt_meta = {
            "id": nethunt_customer["recordId"],
            "first": nethunt_customer["fields"]["Prénom"],
            "last": nethunt_customer["fields"]["Nom"],
            "phone": nethunt_customer["fields"]["Téléphone"]
        }

        ringover_meta = {
            "company": "",
            "numbers": [],
            "is_shared": False,
            "firstname": nethunt_meta["first"],
            "lastname": nethunt_meta["last"]
        }

        for nethunt_phone in nethunt_meta['phone']:
            ringover_phone = convert_phone_eu(nethunt_phone.strip())
            contact_exists = get_ringover_contact_by_number(
                phone=ringover_phone
            )
            if len(contact_exists):
                synced = True
                break
            ringover_meta["numbers"].append({
                "number": ringover_phone,
                "type": "mobile"
            })

        if not synced:
            print(f"PO {idx}: {nethunt_customer['recordId']}")
            post_ringover_customer(data={"contacts": [ringover_meta]})
            csv_writer.writerow([
                nethunt_meta["id"],
                nethunt_phone,
                ringover_phone,
                "PO"
            ])
        else:
            print(f"SY {idx}: {nethunt_customer['recordId']}")
            csv_writer.writerow([
                nethunt_meta["id"],
                nethunt_phone,
                ringover_phone,
                "SY"
            ])

    csv_file.close()


def get_nethunt_customers():
    response = client_nethunt.get(
        url=f"{HOST}/v1/zapier/searches/find-record/{FOLDER_ID}",
        params={"query": "Prénom: Nom: Téléphone:", "limit": "5000"}
    )
    return json.loads(response.text)


def convert_phone_eu(phone):
    digits = [x.strip() for x in re.findall('..', phone)]
    new_digits = []
    for idx, digit in enumerate(digits):
        if idx == 0:
            retain_digit = re.findall('.', digit)[1]
            if digit in [f"0{x}" for x in range(1, 8)]:
                new_digits.append(f"33{retain_digit}")
            else:
                new_digits.append(digit)
        else:
            new_digits.append(digit)

    joined_digits = "".join(new_digits)
    return int(joined_digits.strip())


def post_ringover_customer(data):
    response = client_ringover.post(
        url="https://public-api.ringover.com/v2/contacts",
        json=data
    )
    return response.text


def get_ringover_contact_by_number(phone):
    response = client_ringover.post(
        url="https://public-api.ringover.com/v2/contacts",
        json={"search": str(phone)}
    )
    if response.status_code == 200:
        return response.json()["contact_list"]
    else:
        return []


if __name__ == '__main__':
    nethunt_to_ringover_customer()
