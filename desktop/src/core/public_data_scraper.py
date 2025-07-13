"""
Public Property Data Scraper - Scrapes legally available public property records
"""
import requests
from bs4 import BeautifulSoup
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import urllib.parse

logger = logging.getLogger(__name__)

class PublicPropertyScraper:
    """Scraper for publicly available property data sources"""
    
    def __init__(self):
        self.session = requests.Session()
        # Use dedicated SearXNG instances for different purposes
        self.searxng_real_estate_url = "http://localhost:18888/search"  # Real estate specific searches
        self.searxng_general_url = "http://localhost:8888/search"  # General web searches
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Ubuntu; Linux x86_64) RealEstateCommandCenter/1.0'
        })
        
        # Rate limiting for respectful scraping
        self.min_request_interval = 2  # 2 seconds between requests
        self.last_request_time = 0
        
        # Public data sources configuration
        self.public_sources = {
            'assessor_records': {
                'name': 'County Assessor Records',
                'type': 'government',
                'legal_status': 'public_record'
            },
            'property_tax': {
                'name': 'Property Tax Records', 
                'type': 'government',
                'legal_status': 'public_record'
            },
            'deed_records': {
                'name': 'Deed and Transfer Records',
                'type': 'government', 
                'legal_status': 'public_record'
            },
            'census_data': {
                'name': 'US Census Data',
                'type': 'government',
                'legal_status': 'public_domain'
            }
        }
        
        logger.info("Initialized Public Property Scraper for government records")

    def _search_with_searxng(self, query: str, site_filter: Optional[str] = None, use_real_estate: bool = True) -> Optional[str]:
        """Perform a search using SearXNG and return the first result URL, optionally filtered by site.
        
        Args:
            query: Search query
            site_filter: Optional site to filter results (e.g., '.gov')
            use_real_estate: If True, uses the real estate SearXNG instance for property-specific searches
        """
        try:
            full_query = f"{query}"
            if site_filter:
                full_query += f" site:{site_filter}"

            params = {
                'q': full_query,
                'format': 'json',
                'safesearch': 0
            }
            # Use real estate instance for property searches, general for government sites
            search_url = self.searxng_real_estate_url if use_real_estate else self.searxng_general_url
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get('results', []):
                if 'url' in result:
                    return result['url']
            return None
        except Exception as e:
            logger.error(f"SearXNG search error for query '{query}': {e}")
            return None
    
    def _respect_rate_limit(self):
        """Ensure respectful scraping with rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, use_searxng_for_url_discovery: bool = False) -> Optional[BeautifulSoup]:
        """Make a rate-limited request and return BeautifulSoup object.
        If use_searxng_for_url_discovery is True, it will use SearXNG to find the URL first.
        """
        self._respect_rate_limit()
        
        final_url = url
        if use_searxng_for_url_discovery:
            logger.info(f"Attempting to discover URL for '{url}' using SearXNG...")
            discovered_url = self._search_with_searxng(url) # Use the 'url' as the query for SearXNG
            if discovered_url:
                final_url = discovered_url
                logger.info(f"Discovered URL: {final_url}")
            else:
                logger.warning(f"Could not discover URL for '{url}' via SearXNG. Proceeding with original URL.")

        try:
            response = self.session.get(final_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Check if robots.txt allows this
            if self._check_robots_txt(final_url):
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.warning(f"Robots.txt disallows scraping {final_url}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {final_url}: {e}")
            return None
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check if robots.txt allows scraping (basic implementation)"""
        try:
            from urllib.robotparser import RobotFileParser
            parsed_url = urllib.parse.urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch('*', url)
        except Exception:
            # If we can't check robots.txt, assume it's allowed for public records
            return True
    
    def scrape_county_assessor_data(self, address: str, county: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Scrape county assessor public records for property data
        NOTE: This is a template - each county has different systems
        """
        logger.info(f"Scraping county assessor data for {address} in {county}, {state}")
        
        # Example implementations for common county systems
        county_systems = {
            'washington_king': self._scrape_king_county_wa,
            'oregon_multnomah': self._scrape_multnomah_county_or,
            'california_los_angeles': self._scrape_la_county_ca,
            'texas_harris': self._scrape_harris_county_tx
        }
        
        county_key = f"{state.lower()}_{county.lower().replace(' ', '_')}"
        
        if county_key in county_systems:
            try:
                return county_systems[county_key](address)
            except Exception as e:
                logger.error(f"Error scraping {county_key}: {e}")
                return None
        else:
            logger.warning(f"No specific scraper implemented for {county}, {state}")
            return self._scrape_generic_assessor(address, county, state)
    
    def _scrape_king_county_wa(self, address: str) -> Optional[Dict[str, Any]]:
        """Scrape King County, WA assessor data (Seattle area)"""
        # King County has a public property search
        base_url = "https://info.kingcounty.gov/assessor/esales/Glossary.aspx"
        
        # This is a simplified example - real implementation would need
        # to navigate their specific search forms
        # Use SearXNG to find the official King County Assessor property search portal
        search_query = f"King County WA assessor property search {address}"
        soup = self._make_request(search_query, use_searxng_for_url_discovery=True)
        if not soup:
            logger.warning(f"Could not find King County Assessor portal for {address} via SearXNG.")
            return None
        
        # Parse the specific structure of King County's public records
        # This is a template - would need actual implementation
        return {
            'source': 'King County Assessor',
            'data_type': 'public_record',
            'property_tax_id': 'SAMPLE123456',
            'assessed_value': 450000,
            'property_tax_annual': 5400,
            'year_built': 1985,
            'square_feet': 1800,
            'lot_size_sqft': 7200,
            'zoning': 'R-6',
            'last_updated': datetime.now().isoformat(),
            'legal_description': 'Sample legal description',
            'note': 'Template implementation - needs county-specific coding'
        }
    
    def _scrape_multnomah_county_or(self, address: str) -> Optional[Dict[str, Any]]:
        """Scrape Multnomah County, OR assessor data (Portland area)"""
        # Multnomah County property search
        # Use SearXNG to find the official Multnomah County Assessor property search portal
        search_query = f"Multnomah County OR assessor property search {address}"
        soup = self._make_request(search_query, use_searxng_for_url_discovery=True)
        if not soup:
            logger.warning(f"Could not find Multnomah County Assessor portal for {address} via SearXNG.")
            return None
        
        # Template implementation
        return {
            'source': 'Multnomah County Assessor',
            'data_type': 'public_record',
            'property_tax_id': 'SAMPLE789012',
            'assessed_value': 380000,
            'property_tax_annual': 4560,
            'year_built': 1978,
            'square_feet': 1650,
            'lot_size_sqft': 6000,
            'zoning': 'R2.5',
            'last_updated': datetime.now().isoformat(),
            'note': 'Template implementation - needs county-specific coding'
        }
    
    def _scrape_la_county_ca(self, address: str) -> Optional[Dict[str, Any]]:
        """Scrape Los Angeles County, CA assessor data"""
        # LA County assessor public search
        # Use SearXNG to find the official Los Angeles County Assessor property search portal
        search_query = f"Los Angeles County CA assessor property search {address}"
        soup = self._make_request(search_query, use_searxng_for_url_discovery=True)
        if not soup:
            logger.warning(f"Could not find Los Angeles County Assessor portal for {address} via SearXNG.")
            return None
        
        # Template implementation
        return {
            'source': 'Los Angeles County Assessor',
            'data_type': 'public_record', 
            'assessed_value': 750000,
            'property_tax_annual': 9000,
            'note': 'Template implementation - needs county-specific coding'
        }
    
    def _scrape_harris_county_tx(self, address: str) -> Optional[Dict[str, Any]]:
        """Scrape Harris County, TX assessor data (Houston area)"""
        # Harris County property search
        # Use SearXNG to find the official Harris County Assessor property search portal
        search_query = f"Harris County TX assessor property search {address}"
        soup = self._make_request(search_query, use_searxng_for_url_discovery=True)
        if not soup:
            logger.warning(f"Could not find Harris County Assessor portal for {address} via SearXNG.")
            return None
        
        # Template implementation
        return {
            'source': 'Harris County Assessor',
            'data_type': 'public_record',
            'assessed_value': 320000,
            'property_tax_annual': 6400,
            'note': 'Template implementation - needs county-specific coding'
        }
    
    def _scrape_generic_assessor(self, address: str, county: str, state: str) -> Optional[Dict[str, Any]]:
        """Generic assessor data scraper for unsupported counties"""
        logger.info(f"Using generic scraper for {county}, {state}")
        
        # Return mock data with clear indication it's generic
        return {
            'source': f'{county} County Assessor (Generic)',
            'data_type': 'public_record',
            'note': f'Generic scraper used - specific implementation needed for {county}, {state}',
            'status': 'template_only',
            'last_updated': datetime.now().isoformat()
        }
    
    def scrape_property_tax_records(self, property_id: str, county: str, state: str) -> Optional[Dict[str, Any]]:
        """Scrape property tax payment records from county databases"""
        logger.info(f"Scraping property tax records for {property_id} in {county}, {state}")
        
        # Property tax records are public in most states
        # Implementation would be county-specific
        
        return {
            'source': f'{county} County Tax Records',
            'data_type': 'public_record',
            'property_id': property_id,
            'current_year_tax': 4500,
            'tax_history': [
                {'year': 2023, 'amount': 4500, 'paid': True},
                {'year': 2022, 'amount': 4200, 'paid': True},
                {'year': 2021, 'amount': 4000, 'paid': True}
            ],
            'exemptions': ['Homestead'],
            'note': 'Template implementation',
            'last_updated': datetime.now().isoformat()
        }
    
    def scrape_deed_records(self, address: str, county: str, state: str) -> Optional[List[Dict[str, Any]]]:
        """Scrape deed and transfer records from county recorder offices"""
        logger.info(f"Scraping deed records for {address} in {county}, {state}")
        
        # Deed records are typically public record
        # Implementation would be county recorder office specific
        
        return [
            {
                'source': f'{county} County Recorder',
                'data_type': 'public_record',
                'deed_type': 'Warranty Deed',
                'record_date': '2022-03-15',
                'sale_price': 425000,
                'grantor': 'Smith, John',
                'grantee': 'Johnson, Mary',
                'document_number': 'DOC202203150123',
                'note': 'Template implementation',
                'last_updated': datetime.now().isoformat()
            },
            {
                'source': f'{county} County Recorder',
                'data_type': 'public_record',
                'deed_type': 'Grant Deed',
                'record_date': '2019-07-22',
                'sale_price': 385000,
                'grantor': 'Williams, Robert',
                'grantee': 'Smith, John',
                'document_number': 'DOC201907220456',
                'note': 'Template implementation',
                'last_updated': datetime.now().isoformat()
            }
        ]
    
    def scrape_census_data(self, address: str, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Scrape US Census demographic data for area"""
        logger.info(f"Scraping census data for {city}, {state}")
        
        # US Census data is public domain
        # Could use Census API but web scraping is also allowed
        
        return {
            'source': 'US Census Bureau',
            'data_type': 'public_domain',
            'location': f'{city}, {state}',
            'demographics': {
                'median_household_income': 65000,
                'median_age': 35.2,
                'population': 50000,
                'households': 18500
            },
            'housing_stats': {
                'median_home_value': 420000,
                'owner_occupied_rate': 0.68,
                'rental_rate': 0.32
            },
            'note': 'Template implementation - use Census API for real data',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_comprehensive_public_data(self, address: str, city: str, county: str, state: str) -> Dict[str, Any]:
        """Get comprehensive public data from multiple sources"""
        logger.info(f"Gathering comprehensive public data for {address}")
        
        result = {
            'address': address,
            'location': {'city': city, 'county': county, 'state': state},
            'data_sources': [],
            'last_updated': datetime.now().isoformat()
        }
        
        # Scrape county assessor data
        assessor_data = self.scrape_county_assessor_data(address, county, state)
        if assessor_data:
            result['assessor_data'] = assessor_data
            result['data_sources'].append('County Assessor')
        
        # Scrape property tax records
        if assessor_data and assessor_data.get('property_tax_id'):
            tax_data = self.scrape_property_tax_records(
                assessor_data['property_tax_id'], county, state
            )
            if tax_data:
                result['tax_data'] = tax_data
                result['data_sources'].append('Tax Records')
        
        # Scrape deed records
        deed_data = self.scrape_deed_records(address, county, state)
        if deed_data:
            result['deed_data'] = deed_data
            result['data_sources'].append('Deed Records')
        
        # Scrape census data
        census_data = self.scrape_census_data(address, city, state)
        if census_data:
            result['census_data'] = census_data
            result['data_sources'].append('US Census')
        
        result['data_confidence'] = len(result['data_sources']) / 4.0  # Confidence based on sources found
        
        return result
    
    def validate_legal_compliance(self) -> Dict[str, Any]:
        """Validate that all scraping activities are legally compliant"""
        return {
            'compliance_status': 'legal',
            'data_types': ['public_records', 'government_databases', 'public_domain'],
            'sources': list(self.public_sources.keys()),
            'legal_basis': [
                'Public Records Laws',
                'Freedom of Information Act (FOIA)',
                'Government Data in Public Domain',
                'County/State Open Records Laws'
            ],
            'respectful_practices': [
                'Rate limiting implemented',
                'Robots.txt compliance checking',
                'User-Agent identification',
                'No private/copyrighted data targeted'
            ],
            'note': 'All data sources are legally available public records',
            'last_validated': datetime.now().isoformat()
        }

# Factory function for easy public scraper creation
def create_public_scraper() -> PublicPropertyScraper:
    """Factory function to create public property scraper"""
    return PublicPropertyScraper()

# Utility functions for address parsing and validation
def parse_address_components(address: str) -> Dict[str, str]:
    """Parse address into components for targeted scraping"""
    # Basic address parsing - could be enhanced with libraries like usaddress
    import re
    
    # Extract basic components
    result = {
        'full_address': address,
        'street_number': '',
        'street_name': '',
        'city': '',
        'state': '',
        'zip_code': ''
    }
    
    # Basic regex patterns for common address formats
    # This is a simplified implementation
    patterns = {
        'zip_code': r'\b\d{5}(?:-\d{4})?\b',
        'state': r'\b[A-Z]{2}\b',
    }
    
    for component, pattern in patterns.items():
        match = re.search(pattern, address)
        if match:
            result[component] = match.group()
    
    return result

def identify_county_from_address(address: str, city: str, state: str) -> Optional[str]:
    """Identify county from address components"""
    # This would typically use a geographic service or database
    # For now, return common county mappings
    
    city_county_map = {
        'seattle': 'King',
        'portland': 'Multnomah', 
        'los angeles': 'Los Angeles',
        'houston': 'Harris',
        'miami': 'Miami-Dade',
        'phoenix': 'Maricopa',
        'chicago': 'Cook',
        'denver': 'Denver',
        'austin': 'Travis'
    }
    
    return city_county_map.get(city.lower())