import os
import csv
import requests
from urllib.parse import urlparse
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Function to create directory if it doesn't exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Function to download an image from a URL with retry logic
def download_image(url, save_path):
    if not url:
        return
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

# Function to sanitize folder names
def sanitize_folder_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# Function to process items and download images
def process_items(csv_file):
    base_dir = 'images'
    create_directory(base_dir)
    no_brand_dir = os.path.join(base_dir, 'no_brand')
    create_directory(no_brand_dir)

    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for row in tqdm(rows, desc="Processing items"):
                brand = row['Brand'].strip().lower() if row['Brand'].strip() else 'no_brand'
                item_title = sanitize_folder_name(row['Title'].strip())
                brand_dir = os.path.join(base_dir, brand)
                item_dir = os.path.join(brand_dir, item_title)
                create_directory(item_dir)

                # Split image URLs by comma and newline
                image_urls = re.split(r'[\n,]+', row['ImageURLs'])
                for idx, image_url in enumerate(image_urls):
                    image_url = image_url.strip()
                    if image_url:  # Check if the URL is not empty
                        image_ext = os.path.splitext(urlparse(image_url).path)[1]
                        image_name = f"{item_title}_{idx}{image_ext}"
                        save_path = os.path.join(item_dir, image_name)
                        futures.append(executor.submit(download_image, image_url, save_path))

            for future in tqdm(as_completed(futures), desc="Downloading images", total=len(futures)):
                future.result()

# Example usage
csv_file = 'eBay_items.csv'
process_items(csv_file)