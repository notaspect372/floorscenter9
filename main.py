import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import cloudscraper

def scrape_properties(base_url, output_file, base, start_page, end_page):
    scraper = cloudscraper.create_scraper()  # Create a session with Cloudflare bypass
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    property_data = []

    for page in range(start_page, end_page + 1):
        print(f"Scraping page {page}...")
        try:
            response = scraper.get(f"{base_url}?p={page}", headers=headers)
            if response.status_code != 200:
                print(f"Failed to load page {page}. HTTP Status: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            properties = soup.select("div.add-details")

            if not properties:
                print("No more properties found. Exiting...")
                break

            for prop in properties:
                link = prop.select_one("h4 a")
                if not link or not link.get("href"):
                    continue
                property_url = base + link["href"]

                property_details = scrape_property_details(scraper, property_url, headers)
                if property_details:
                    property_data.append(property_details)

            time.sleep(2)

        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            break

    df = pd.DataFrame(property_data)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_excel(output_file, index=False)
    
    print(f"Scraping completed. Data saved to {output_file}")

def scrape_property_details(scraper, url, headers):
    try:
        response = scraper.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to load property details: {url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.select_one("h1")
        if not title:
            return None
        title_text = title.get_text(strip=True)
        try:
            name, address = re.split(r'\sin\s', title_text, maxsplit=1)
        except ValueError:
            name = title_text.strip()
            address = "N/A"

        price = soup.select_one("div.listing-detail span[style*='color:#e53000']")
        price_text = price.get_text(strip=True) if price else "N/A"

        description = soup.select_one("div[style*='font-size:larger']")
        description_text = description.get_text(strip=True) if description else "N/A"

        data = {
            "URL": url,
            "Name": name.strip(),
            "Address": address.strip() if address != "N/A" else "Djibouti",
            "Price": price_text,
            "Description": description_text,
        }
        print(f"Scraped: {data}")

        return data

    except Exception as e:
        print(f"Error scraping property details from {url}: {e}")
        return None

if __name__ == "__main__":
    base = os.getenv("BASE_URL", "https://www.dahaboo.com/")
    BASE_URL = os.getenv("SCRAPER_TARGET_URL", "https://www.dahaboo.com/locaux-commerciaux-10/")
    OUTPUT_FILE = "output/properties.xlsx"
    START_PAGE = int(os.getenv("START_PAGE", 1))
    END_PAGE = int(os.getenv("END_PAGE", 1))

    scrape_properties(BASE_URL, OUTPUT_FILE, base, START_PAGE, END_PAGE)
