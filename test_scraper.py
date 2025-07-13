
import sys
import os
from pprint import pprint

# Add the desktop/src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'desktop', 'src')))

from core.property_scraper import PropertyScraper

def test_zillow_scraper():
    scraper = PropertyScraper()
    test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
    print(f"Attempting to scrape Zillow for: {test_address}")
    try:
        data = scraper.search_zillow(test_address)
        pprint(data)
    except Exception as e:
        print(f"An error occurred during Zillow scraping test: {e}")

if __name__ == "__main__":
    test_zillow_scraper()
