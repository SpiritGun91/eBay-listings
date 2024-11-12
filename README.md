# eBay-Listings

This project fetches and stores details of active eBay listings into a CSV file. It uses the eBay Trading API to retrieve item details such as item ID, title, price, currency, category ID, category name, description, quantity, brand, listing URL, and image URLs. Additionally, it downloads and organizes item images by brand and title.

## Features

- Fetches active eBay listings.
- Retrieves detailed information for each listing.
- Strips HTML tags from item descriptions.
- Constructs listing URLs.
- Extracts and lists image URLs.
- Stores all information in a CSV file.
- Downloads and organizes item images by brand and title.
- Implements retry logic and timeout for robust image downloading.
- Ensures unique filenames for images to prevent overwriting.

## Requirements

- Python 3.x
- `ebaysdk`
- `tqdm`
- `beautifulsoup4`
- `requests`

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/SpiritGun91/eBay-listings.git
   cd eBay-listings
   ```

2. Install the required libraries:

   ```sh
   pip install -r requirements.txt
   ```

3. Create a `config.ini` file with your eBay API credentials:

   ```ini
   [eBayAPI]
   APP_ID = your_app_id
   DEV_ID = your_dev_id
   CERT_ID = your_cert_id
   USER_TOKEN = your_user_token
   ```

## Usage

1. Run the script to fetch eBay listings and store them in a CSV file:

   ```sh
   python eBay.py
   ```

2. The script will create a file named `eBay_items.csv` with the following columns:

   - ItemID
   - Title
   - Price
   - Currency
   - CategoryID
   - CategoryName
   - Description
   - Quantity
   - Brand
   - ListingURL
   - ImageURLs

3. Run the script to download and organize images:

   ```sh
   python images.py
   ```

This will create an images directory with subdirectories for each brand, containing item-specific folders named after the item titles, and items without a brand are grouped in a no_brand folder.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
