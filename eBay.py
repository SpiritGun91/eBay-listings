import configparser
import csv
import re
import time
import random
import requests
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from bs4 import BeautifulSoup

# Read credentials from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

APP_ID = config['eBayAPI']['APP_ID']
DEV_ID = config['eBayAPI']['DEV_ID']
CERT_ID = config['eBayAPI']['CERT_ID']
USER_TOKEN = config['eBayAPI']['USER_TOKEN']

def strip_html_tags(text):
    return BeautifulSoup(text, "html.parser").get_text()

def retry(exceptions, tries=4, delay=3, backoff=2, jitter=0.1):
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = f"{e}, Retrying in {mdelay} seconds..."
                    print(msg)
                    time.sleep(mdelay + random.uniform(0, jitter))
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry

@retry((ConnectionError, requests.exceptions.ReadTimeout), tries=4, delay=3, backoff=2)
def get_item_details(api, item_id):
    try:
        item_response = api.execute('GetItem', {
            'ItemID': item_id,
            'DetailLevel': 'ReturnAll'
        })
        item_data = item_response.dict().get('Item', {})
        
        # Extract brand from ProductListingDetails -> BrandMPN
        brand_info = item_data.get('ProductListingDetails', {}).get('BrandMPN', {})
        brand = ''
        if isinstance(brand_info, dict):
            brand = brand_info.get('Brand', '')

        # Strip HTML tags from description
        description = strip_html_tags(item_data.get('Description', ''))

        # Construct listing URL
        listing_url = f"https://www.ebay.com/itm/{item_id}"

        # Extract image URLs
        image_urls = item_data.get('PictureDetails', {}).get('PictureURL', [])
        if isinstance(image_urls, str):
            image_urls = [image_urls]

        return {
            'ItemID': item_data.get('ItemID', ''),
            'Title': item_data.get('Title', ''),
            'Price': item_data.get('SellingStatus', {}).get('CurrentPrice', {}).get('value', ''),
            'Currency': item_data.get('SellingStatus', {}).get('CurrentPrice', {}).get('_currencyID', ''),
            'CategoryID': item_data.get('PrimaryCategory', {}).get('CategoryID', ''),
            'CategoryName': item_data.get('PrimaryCategory', {}).get('CategoryName', ''),
            'Description': description,
            'Quantity': item_data.get('Quantity', ''),
            'Brand': brand,
            'ListingURL': listing_url,
            'ImageURLs': ', '.join(image_urls)
        }
    except ConnectionError as e:
        print(f"Error fetching details for item {item_id}: {e}")
        return None

try:
    api = Trading(
        appid=APP_ID,
        devid=DEV_ID,
        certid=CERT_ID,
        token=USER_TOKEN,
        config_file=None,
        timeout=60  # Increase the timeout duration
    )

    item_ids = []
    page_number = 1
    entries_per_page = 200

    while True:
        # Get active listings for the current page
        response = api.execute('GetMyeBaySelling', {
            'ActiveList': {
                'Include': True,
                'Pagination': {
                    'EntriesPerPage': entries_per_page,
                    'PageNumber': page_number
                }
            }
        })

        # Extract item IDs from the response
        items = response.dict().get('ActiveList', {}).get('ItemArray', {}).get('Item', [])
        if not items:
            break

        item_ids.extend([item['ItemID'] for item in items])

        # Check if there are more pages
        if len(items) < entries_per_page:
            break

        page_number += 1

    # Fetch item details
    item_details_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_item_details, api, item_id): item_id for item_id in item_ids}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching item details"):
            item_details = future.result()
            if item_details:
                item_details_list.append(item_details)

    # Open a CSV file to write the item details
    with open('eBay_items.csv', mode='w', newline='') as file:
        writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Write the header
        header = ['ItemID', 'Title', 'Price', 'Currency', 'CategoryID', 'CategoryName', 'Description', 'Quantity', 'Brand', 'ListingURL', 'ImageURLs']
        writer.writerow(header)

        # Write the item details
        for item in item_details_list:
            row = [
                item['ItemID'], 
                item['Title'], 
                item['Price'], 
                item['Currency'], 
                item['CategoryID'], 
                item['CategoryName'],
                item['Description'],
                item['Quantity'],
                item['Brand'],
                item['ListingURL'],
                item['ImageURLs']
            ]
            writer.writerow(row)

except ConnectionError as e:
    print(e)
    print(e.response.dict())