"""
RESO Web API Base Client
Implements the RESO Web API standard for real estate data access
Used by Bridge Interactive, MLSGrid, and other RESO-compliant providers
"""
import requests
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from urllib.parse import urlencode, quote
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class RESOWebAPIClient(ABC):
    """Base client for RESO Web API compliant services"""
    
    # Standard RESO resources
    RESOURCES = {
        'Property': 'Property listings for sale or lease',
        'Member': 'Agent/broker information',
        'Office': 'Brokerage information',
        'Media': 'Photos and other media',
        'OpenHouse': 'Open house events',
        'Team': 'Team information',
        'TeamMembers': 'Team member associations'
    }
    
    # Common RESO fields for Property resource
    PROPERTY_FIELDS = [
        'ListingKey', 'ListingId', 'StandardStatus', 'ListPrice',
        'StreetNumber', 'StreetName', 'StreetSuffix', 'City', 'StateOrProvince', 'PostalCode',
        'UnparsedAddress', 'Latitude', 'Longitude',
        'PropertyType', 'PropertySubType', 'BedroomsTotal', 'BathroomsFull', 'BathroomsHalf',
        'LivingArea', 'LotSizeAcres', 'YearBuilt', 'ListingContractDate',
        'CloseDate', 'ClosePrice', 'PublicRemarks', 'ListingTerms',
        'PhotosCount', 'PhotosChangeTimestamp', 'ModificationTimestamp'
    ]
    
    def __init__(self, base_url: str, api_key: str, **kwargs):
        """
        Initialize RESO Web API client
        
        Args:
            base_url: Base URL for the API (e.g., https://api.bridgeinteractive.com)
            api_key: API key or access token
            **kwargs: Additional configuration options
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set up authentication
        self._setup_auth()
        
        # Rate limiting configuration
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.5)  # Default 500ms between requests
        self.last_request_time = 0
        
        # Request configuration
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        self.page_size = kwargs.get('page_size', 100)  # RESO recommends 100-500
        
    @abstractmethod
    def _setup_auth(self):
        """Set up authentication headers - implemented by subclasses"""
        pass
        
    def _respect_rate_limit(self):
        """Ensure we respect rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Optional[Dict]:
        """Make an API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                self._respect_rate_limit()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )
                
                # Log request details for debugging
                logger.debug(f"API Request: {method} {url}")
                logger.debug(f"Params: {params}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("Authentication failed - check API key")
                    return None
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited - waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
            # Exponential backoff for retries
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)
                
        return None
        
    def search_properties(self, filters: Dict[str, Any], 
                         select: Optional[List[str]] = None,
                         expand: Optional[List[str]] = None,
                         orderby: Optional[str] = None,
                         top: Optional[int] = None,
                         skip: Optional[int] = None) -> Optional[Dict]:
        """
        Search properties using OData query parameters
        
        Args:
            filters: Dictionary of filters (will be converted to OData $filter)
            select: List of fields to return ($select)
            expand: List of resources to expand ($expand)
            orderby: Sort order ($orderby)
            top: Maximum number of results ($top)
            skip: Number of results to skip ($skip)
            
        Returns:
            Dictionary with results and metadata
        """
        # Build OData query parameters
        params = {}
        
        # Build filter string
        if filters:
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} eq '{value}'")
                elif isinstance(value, (int, float)):
                    filter_parts.append(f"{key} eq {value}")
                elif isinstance(value, dict):
                    # Handle complex filters like date ranges
                    if 'gte' in value:
                        filter_parts.append(f"{key} ge {value['gte']}")
                    if 'lte' in value:
                        filter_parts.append(f"{key} le {value['lte']}")
                    if 'gt' in value:
                        filter_parts.append(f"{key} gt {value['gt']}")
                    if 'lt' in value:
                        filter_parts.append(f"{key} lt {value['lt']}")
                        
            if filter_parts:
                params['$filter'] = ' and '.join(filter_parts)
                
        # Add other OData parameters
        if select:
            params['$select'] = ','.join(select)
        if expand:
            params['$expand'] = ','.join(expand)
        if orderby:
            params['$orderby'] = orderby
        if top:
            params['$top'] = top
        if skip:
            params['$skip'] = skip
            
        # Make the request
        return self._make_request('GET', 'Property', params=params)
        
    def get_property(self, listing_key: str, expand: Optional[List[str]] = None) -> Optional[Dict]:
        """Get a single property by ListingKey"""
        endpoint = f"Property('{listing_key}')"
        params = {}
        
        if expand:
            params['$expand'] = ','.join(expand)
            
        return self._make_request('GET', endpoint, params=params)
        
    def search_members(self, filters: Dict[str, Any], 
                      select: Optional[List[str]] = None) -> Optional[Dict]:
        """Search for agents/brokers"""
        params = {}
        
        if filters:
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} eq '{value}'")
                elif isinstance(value, (int, float)):
                    filter_parts.append(f"{key} eq {value}")
                    
            if filter_parts:
                params['$filter'] = ' and '.join(filter_parts)
                
        if select:
            params['$select'] = ','.join(select)
            
        return self._make_request('GET', 'Member', params=params)
        
    def get_metadata(self) -> Optional[Dict]:
        """Get API metadata (field definitions, etc.)"""
        return self._make_request('GET', '$metadata')
        
    def get_media(self, listing_key: str) -> Optional[List[Dict]]:
        """Get media/photos for a property"""
        params = {
            '$filter': f"ResourceRecordKey eq '{listing_key}'",
            '$orderby': 'Order'
        }
        
        result = self._make_request('GET', 'Media', params=params)
        if result and 'value' in result:
            return result['value']
        return None
        
    def convert_to_standard_format(self, reso_property: Dict) -> Dict:
        """Convert RESO property data to our standard format"""
        # Map RESO fields to our standard format
        standard = {
            'mls_id': reso_property.get('ListingId'),
            'listing_key': reso_property.get('ListingKey'),
            'status': reso_property.get('StandardStatus'),
            'list_price': reso_property.get('ListPrice'),
            'address': {
                'street_number': reso_property.get('StreetNumber'),
                'street_name': reso_property.get('StreetName'),
                'street_suffix': reso_property.get('StreetSuffix'),
                'city': reso_property.get('City'),
                'state': reso_property.get('StateOrProvince'),
                'postal_code': reso_property.get('PostalCode'),
                'unparsed': reso_property.get('UnparsedAddress'),
                'latitude': reso_property.get('Latitude'),
                'longitude': reso_property.get('Longitude')
            },
            'property_details': {
                'type': reso_property.get('PropertyType'),
                'sub_type': reso_property.get('PropertySubType'),
                'bedrooms': reso_property.get('BedroomsTotal'),
                'bathrooms_full': reso_property.get('BathroomsFull'),
                'bathrooms_half': reso_property.get('BathroomsHalf'),
                'square_feet': reso_property.get('LivingArea'),
                'lot_size_acres': reso_property.get('LotSizeAcres'),
                'year_built': reso_property.get('YearBuilt')
            },
            'listing_details': {
                'list_date': reso_property.get('ListingContractDate'),
                'close_date': reso_property.get('CloseDate'),
                'close_price': reso_property.get('ClosePrice'),
                'description': reso_property.get('PublicRemarks'),
                'listing_terms': reso_property.get('ListingTerms'),
                'photos_count': reso_property.get('PhotosCount'),
                'last_modified': reso_property.get('ModificationTimestamp')
            },
            'raw_data': reso_property  # Keep original for reference
        }
        
        return standard