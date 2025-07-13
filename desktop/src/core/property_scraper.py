"""
Property Web Scraper - Real estate data from multiple sources
"""
import requests
import json
import re
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlencode, quote
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyScraper:
    """Web scraper for real estate data from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    import requests
import json
import re
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlencode, quote, urlparse
import logging
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyScraper:
    """Web scraper for real estate data from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        # Use dedicated SearXNG instances for different purposes
        self.searxng_real_estate_url = "http://localhost:18888/search"  # Real estate specific searches
        self.searxng_general_url = "http://localhost:8888/search"  # General web searches
        self.searxng_url = self.searxng_real_estate_url  # Default to real estate for backward compatibility
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _search_with_searxng(self, query: str, site: str, use_real_estate: bool = True) -> Optional[str]:
        """Perform a search using SearXNG and return the first result URL for a specific site.
        
        Args:
            query: Search query
            site: Site to filter results (e.g., 'zillow.com')
            use_real_estate: If True, uses the real estate SearXNG instance, otherwise uses general instance
        """
        try:
            params = {
                'q': f"{query} site:{site}",
                'format': 'json',
                'safesearch': 0
            }
            search_url = self.searxng_real_estate_url if use_real_estate else self.searxng_general_url
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get('results', []):
                if 'url' in result and site in result['url']:
                    return result['url']
            return None
        except Exception as e:
            logger.error(f"SearXNG search error for {site}: {e}")
            return None

    def _fetch_and_parse_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch HTML content from a URL and parse it with BeautifulSoup."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching or parsing HTML from {url}: {e}")
            return None

    def search_zillow(self, address: str) -> Dict[str, Any]:
        """Search Zillow for property information using SearXNG and BeautifulSoup"""
        try:
            search_query = f"{address} zillow"
            zillow_url = self._search_with_searxng(search_query, "zillow.com")
            
            if not zillow_url:
                return {"error": "No Zillow URL found via SearXNG"}
            
            soup = self._fetch_and_parse_html(zillow_url)
            if not soup:
                return {"error": "Failed to fetch or parse Zillow page"}
            
            # --- Zillow Parsing Logic (Highly dependent on Zillow's HTML structure) ---
            # This is a simplified example and will likely need significant refinement
            # based on actual Zillow page structure.
            
            property_data = {
                'bedrooms': None,
                'bathrooms': None,
                'square_feet': None,
                'estimated_value': None,
                'property_type': 'House', # Default
                'last_sale_price': None,
                'last_sale_date': None,
            }

            # Example: Try to find estimated value
            # Look for meta tags or specific divs/spans that contain the data
            # This is a very fragile approach and will break if Zillow changes its HTML
            value_tag = soup.find('meta', attrs={'name': 'zillow_zestimate'})
            if value_tag and 'content' in value_tag.attrs:
                try:
                    property_data['estimated_value'] = int(float(value_tag['content']))
                except ValueError:
                    pass

            # More robust parsing would involve looking for specific data attributes or JSON-LD
            # For a real application, consider using a dedicated Zillow API or a more advanced scraping framework

            logger.info(f"Scraped Zillow data for {address}: {property_data}")
            return property_data
            
        except Exception as e:
            logger.error(f"Zillow scraping error: {e}")
            return {'error': str(e)}
    
    def search_redfin(self, address: str) -> Dict[str, Any]:
        """Search Redfin for property information using SearXNG and BeautifulSoup"""
        try:
            search_query = f"{address} redfin"
            redfin_url = self._search_with_searxng(search_query, "redfin.com")
            
            if not redfin_url:
                return {"error": "No Redfin URL found via SearXNG"}
            
            soup = self._fetch_and_parse_html(redfin_url)
            if not soup:
                return {"error": "Failed to fetch or parse Redfin page"}
            
            # --- Redfin Parsing Logic (Highly dependent on Redfin's HTML structure) ---
            property_data = {
                'bedrooms': None,
                'bathrooms': None,
                'square_feet': None,
                'estimated_value': None,
                'property_type': 'House', # Default
                'last_sale_price': None,
                'last_sale_date': None,
            }

            # Example: Try to find data from script tags containing JSON-LD or similar
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if '@graph' in json_data:
                        for item in json_data['@graph']:
                            if item.get('@type') == 'Residence':
                                if 'numberOfBedrooms' in item: property_data['bedrooms'] = item['numberOfBedrooms']
                                if 'numberOfBathroomsTotal' in item: property_data['bathrooms'] = item['numberOfBathroomsTotal']
                                if 'floorSize' in item and 'value' in item['floorSize']: property_data['square_feet'] = item['floorSize']['value']
                                if 'value' in item and 'valueReference' in item['value'] and item['value']['valueReference'] == 'ListPrice':
                                    property_data['estimated_value'] = item['value']['value']
                            elif item.get('@type') == 'SingleFamilyResidence':
                                if 'yearBuilt' in item: property_data['year_built'] = item['yearBuilt']
                    elif json_data.get('@type') == 'RealEstateListing':
                        if 'price' in json_data: property_data['estimated_value'] = json_data['price']
                        if 'floorSize' in json_data and 'value' in json_data['floorSize']: property_data['square_feet'] = json_data['floorSize']['value']

                except json.JSONDecodeError:
                    continue

            logger.info(f"Scraped Redfin data for {address}: {property_data}")
            return property_data
            
        except Exception as e:
            logger.error(f"Redfin scraping error: {e}")
            return {'error': str(e)}
    
    def search_realtor_com(self, address: str) -> Dict[str, Any]:
        """Search Realtor.com for property information using SearXNG and BeautifulSoup"""
        try:
            search_query = f"{address} realtor.com"
            realtor_url = self._search_with_searxng(search_query, "realtor.com")
            
            if not realtor_url:
                return {"error": "No Realtor.com URL found via SearXNG"}
            
            soup = self._fetch_and_parse_html(realtor_url)
            if not soup:
                return {"error": "Failed to fetch or parse Realtor.com page"}
            
            # --- Realtor.com Parsing Logic (Highly dependent on Realtor.com's HTML structure) ---
            property_data = {
                'bedrooms': None,
                'bathrooms': None,
                'square_feet': None,
                'estimated_value': None,
                'property_type': 'House', # Default
                'last_sale_price': None,
                'last_sale_date': None,
            }

            # Realtor.com often uses a __NEXT_DATA__ script tag with a JSON payload
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if next_data_script and next_data_script.string:
                try:
                    json_data = json.loads(next_data_script.string)
                    # Navigate through the JSON structure to find property data
                    # This path is an educated guess and may need adjustment
                    listing_data = json_data.get('props', {}).get('pageProps', {}).get('initialReduxState', {}).get('property', {}).get('property', {})
                    
                    if listing_data:
                        property_data['bedrooms'] = listing_data.get('beds')
                        property_data['bathrooms'] = listing_data.get('baths')
                        property_data['square_feet'] = listing_data.get('sqft')
                        property_data['estimated_value'] = listing_data.get('price')
                        property_data['year_built'] = listing_data.get('yearBuilt')
                        property_data['property_type'] = listing_data.get('propType')
                        
                        # Last sale info might be in a different part of the JSON
                        last_sale = listing_data.get('lastSoldPrice')
                        if last_sale: property_data['last_sale_price'] = last_sale
                        last_sale_date = listing_data.get('lastSoldDate')
                        if last_sale_date: property_data['last_sale_date'] = last_sale_date

                except json.JSONDecodeError:
                    pass

            logger.info(f"Scraped Realtor.com data for {address}: {property_data}")
            return property_data
            
        except Exception as e:
            logger.error(f"Realtor.com scraping error: {e}")
            return {'error': str(e)}
    
    def get_property_comprehensive(self, address: str) -> Dict[str, Any]:
        """Get comprehensive property data from multiple sources"""
        logger.info(f"Fetching comprehensive data for: {address}")
        
        results = {
            'address': address,
            'sources': {},
            'consolidated': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # Try multiple sources with delays to be respectful
        sources = [
            ('zillow', self.search_zillow),
            ('redfin', self.search_redfin),
            ('realtor', self.search_realtor_com)
        ]
        
        for source_name, search_func in sources:
            try:
                logger.info(f"Searching {source_name}...")
                data = search_func(address)
                results['sources'][source_name] = data
                
                # Add delay between requests
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.error(f"Error with {source_name}: {e}")
                results['sources'][source_name] = {'error': str(e)}
        
        # Consolidate data from all sources
        results['consolidated'] = self._consolidate_property_data(results['sources'])
        
        return results
    
    def _consolidate_property_data(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate property data from multiple sources"""
        consolidated = {
            'bedrooms': None,
            'bathrooms': None,
            'square_feet': None,
            'lot_size': None,
            'year_built': None,
            'property_type': None,
            'estimated_value': None,
            'last_sale_price': None,
            'last_sale_date': None,
            'photos': [],
            'description': '',
            'features': [],
            'neighborhood': '',
            'school_district': '',
            'walkability_score': None,
            'confidence_score': 0.0
        }
        
        # Simple consolidation logic - take first non-null value
        for source_name, source_data in sources.items():
            if 'error' in source_data:
                continue
                
            for key in consolidated.keys():
                if key in source_data and source_data[key] is not None:
                    # Prioritize data from certain sources if needed
                    # For now, just take the first available non-None value
                    if consolidated[key] is None:
                        consolidated[key] = source_data[key]
                        # Adjust confidence based on source reliability
                        if source_name == 'zillow':
                            consolidated['confidence_score'] += 0.3
                        elif source_name == 'redfin':
                            consolidated['confidence_score'] += 0.25
                        elif source_name == 'realtor':
                            consolidated['confidence_score'] += 0.25
        
        return consolidated
    
    def search_area_listings(self, city: str, state: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for active listings in an area using SearXNG and parsing results."""
        logger.info(f"Searching listings in {city}, {state}")
        
        all_listings = []
        search_sites = ["zillow.com", "redfin.com", "realtor.com"]
        
        for site in search_sites:
            try:
                query = f"homes for sale {city}, {state} site:{site}"
                if filters:
                    if 'min_price' in filters: query += f" {filters['min_price']}k"
                    if 'max_price' in filters: query += f" {filters['max_price']}k"
                    if 'bedrooms' in filters: query += f" {filters['bedrooms']} beds"
                
                searxng_results = self._search_with_searxng(query, site)
                
                if searxng_results:
                    # For area listings, we might get multiple URLs. Fetch and parse each.
                    # This is a simplified approach; a real scraper would paginate and handle more complex results.
                    for result_url in searxng_results.split(' '): # Assuming space-separated URLs for simplicity
                        if result_url.startswith('http'):
                            soup = self._fetch_and_parse_html(result_url)
                            if soup:
                                # This part needs to be highly customized per site
                                # Example: try to find listing cards or data from the page
                                # For now, just a placeholder for actual listing extraction
                                logger.info(f"Attempting to parse listings from {result_url}")
                                # Placeholder: extract basic info if possible
                                title_tag = soup.find('title')
                                if title_tag and "for sale" in title_tag.text.lower():
                                    all_listings.append({
                                        'address': title_tag.text.split('|')[0].strip(),
                                        'source_url': result_url,
                                        '_data_source': site.replace('.com', ''),
                                        'price': None, # To be extracted
                                        'beds': None, # To be extracted
                                        'baths': None, # To be extracted
                                        'sqft': None, # To be extracted
                                    })
                                    
                time.sleep(random.uniform(1.0, 3.0)) # Be respectful
            except Exception as e:
                logger.error(f"Error searching {site} for area listings: {e}")
        
        return all_listings


class PropertyDataEnhancer:
    """Enhance property data with additional information"""
    
    def __init__(self):
        self.scraper = PropertyScraper()
    
    def enhance_property_data(self, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance basic property data with scraped information"""
        
        if 'address' not in basic_data:
            return basic_data
        
        # Get comprehensive data from multiple sources
        scraped_data = self.scraper.get_property_comprehensive(basic_data['address'])
        
        # Merge with existing data if scraping was successful
        enhanced = basic_data.copy()
        if scraped_data and not scraped_data.get('error'):
            enhanced['scraped_sources'] = scraped_data['sources']
            enhanced['consolidated_data'] = scraped_data['consolidated']
            
            # Override with more accurate scraped data where available
            consolidated = scraped_data['consolidated']
            for key, value in consolidated.items():
                if value is not None and key not in ['confidence_score']:
                    enhanced[key] = value
            
            enhanced['data_confidence'] = consolidated.get('confidence_score', 0.0)
            enhanced['last_scraped'] = scraped_data['last_updated']
        else:
            enhanced['scraped_sources'] = {"error": "Web scraping not active or failed"}
            enhanced['consolidated_data'] = {}
            enhanced['data_confidence'] = 0.0
            enhanced['last_scraped'] = datetime.now().isoformat()
        
        return enhanced
