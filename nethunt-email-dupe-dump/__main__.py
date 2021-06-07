import os
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

# Create session for requests
client = requests.Session()
client.auth = (USER, PASS)
client.headers.update({'accept': 'application/json'})


def get_customer_dupes():
    collection = get_customers()
    dump_customer_dupes_by_email(collection)


def get_customers():
    response = client.get(
        url=f"{HOST}/v1/zapier/searches/find-record/{FOLDER_ID}",
        params={"query": "id:", "limit": "5000"}
    )
    return json.loads(response.text)


def dump_customer_dupes_by_email(collection=[]):
    # {Array} items to dump in CSV
    dump = []

    # {Array} items the have been processed
    processed = []

    for customer in collection:
        if 'Email' not in customer['fields'].keys():
            continue

        id = customer['recordId']
        emails = customer['fields']['Email']

        for email in emails:
            email = email \
                .replace('>', '') \
                .replace('<', '')

            dupe_meta = {
                'id': id,
                'email': email
            }

            # if email is in already in processed items
            if email in [x['email'] for x in processed]:
                # push current customer to dump
                dump.append(dupe_meta)
                for p_meta in [x for x in processed if x['email'] == email]:
                    # push processed customer to dump if not already in dump collection
                    if p_meta['id'] not in [x['id'] for x in dump]:
                        dump.append(p_meta)
            # push duplicate customer in processed dump
            else:
                # push current customer to processed items
                processed.append(dupe_meta)

    csv_file = open("nethunt-email-dupe-dump.csv", "w", newline="")
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(["id", "email"])

    for d in dump:
        csv_writer.writerow([d["id"], d["email"]])

    csv_file.close()


if __name__ == '__main__':
    get_customer_dupes()
