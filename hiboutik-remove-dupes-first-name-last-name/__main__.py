import os
import csv
import json
import dotenv
import requests

# Load environment variables
dotenv.load_dotenv()
HOST = os.environ.get('HB_HOST')
USER = os.environ.get('HB_USER')
PASS = os.environ.get('HB_PASS')

# Create session for hiboutik requests
client = requests.Session()
client.auth = (USER, PASS)
client.headers.update({'accept': 'application/json'})

# CSV
csv_file = open(
    "hiboutik-remove-dupes-first-name-last-name.csv", "w", newline="")
csv_writer = csv.writer(csv_file, delimiter=",")
csv_writer.writerow([
    "name",
    "id",
    "sales",
    "email",
    "phone",
    "priority"
])


def dump_first_name_last_name_dupe(file="./hiboutik-first-name-and-last-name-dupe-dump.csv"):
    customers = {}
    with open(file, 'r') as f:
        for idx, line in enumerate(f.readlines()):
            if idx > 0:
                values = line.split(',')
                fname = values[1].replace('\n', '')
                hid = values[0]

                if fname not in customers.keys():
                    customers[fname] = []

                customers[fname].append(hid)

    for idx, customer in enumerate(customers):
        print(f"{idx} of {len(customers)}")
        metas = []
        ids = customers[customer]

        for id in ids:
            meta = get_customer(id)
            metas.append(meta)

        get_dumps(customer, metas)
        csv_writer.writerow([])

    csv_file.close()


def get_customer(id=False):
    if id == False:
        return False
    response = client.get(f"{HOST}/customer/{id}")
    return response.json()[0]


def get_dumps(customer, metas):
    # name
    # id
    # sales: Integer
    # sales valid: Boolean
    # email: Boolean
    # phone: Boolean
    # status: OK / NH / DEL
    dumps = []

    for meta in metas:
        dump = {}
        dump['name'] = customer
        dump['id'] = meta['customers_id']
        dump['sales'] = [x['sale_id'] for x in meta['sales']]
        dump['email'] = 'email' in meta.keys()
        dump['phone'] = 'phone' in meta.keys()
        dumps.append(dump)

    for dump in dumps:
        # record has a validated sale_id
        if len(dump['sales']):
            dump['priority'] = 3
            for sale_id in dump["sales"]:
                dump["priority"] = is_valid_sale(sale_id)
                if dump["priority"] == 4:
                    break

            # both dupes have validated sale_id

        # retain one that has email or phone
        elif dump['email'] or dump['phone']:
            dump['priority'] = 2
        else:
            dump['priority'] = 1

        csv_writer.writerow(dump.values())

    return dumps


def is_valid_sale(sale_id=False):
    sale = get_sale(sale_id)
    if len(sale["line_items"]):
        return 4
    else:
        return 3


def get_sale(sale_id=False):
    response = client.get(f"{HOST}/sales/{sale_id}")
    return response.json()[0]


if __name__ == '__main__':
    dump_first_name_last_name_dupe()
