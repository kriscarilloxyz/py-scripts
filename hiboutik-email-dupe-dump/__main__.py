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


def get_customer_dupes():
    """[Summary]
    """
    # {Array} current customers collected from GET request /customers
    customers = [1]

    # {Array} collection of customers from GET request /customers
    collection = []

    # {Integer} page to collect customers from GET request /customers?p={page}
    current_page = 0

    # While request returns customers
    while len(customers):
        # increase current page
        current_page += 1
        # call GET {HOST}/customers/?p={current_page}
        customers = get_customers_by_page(page=current_page)

        # if customers return array
        if len(customers):
            # append each customer to collection
            for customer in customers:
                collection.append(customer)
            # Debug log
            print(f"+{len(collection)} customers on page {current_page}")

    # create the dump
    dump_customer_dupes_by_first_name_and_last_name(collection)


def get_customers_by_page(page=1):
    """GET request to hiboutik to return customers by page

    Args:
        page (int, optional): page number. Defaults to 1.

    Returns:
        [Array]: Array of customers from hiboutik
    """
    response = client.get(f"{HOST}/customers/?p={page}")
    return response.json()


def dump_customer_dupes_by_first_name_and_last_name(collection=[]):
    """[summary]

    Args:
        collection (list, optional): [description]. Defaults to [].

    Returns:
        [Array]: collection of duplicates by first name and last name
    """
    # {Array} items to dump in CSV
    dump = []

    # {Array} items the have been processed
    processed = []

    for customer in collection:
        # {String} customer id in hiboutik
        id = customer['customers_id']

        # {String} customer email
        email = customer['email']

        # Skip if email is non exist
        if email == '':
            continue

        # {Object} meta data of customer for dupe checking
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

    csv_file = open("hiboutik-email-dupe-dump.csv", "w", newline="")
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(["id", "email"])

    for d in dump:
        csv_writer.writerow([d["id"], d["email"]])

    csv_file.close()


if __name__ == '__main__':
    get_customer_dupes()
