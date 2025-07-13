"""
MLSGrid API Client
Implements MLSGrid's RESO Web API v2 for MLS data access
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.reso_web_api import RESOWebAPIClient
from core.api_key_manager import api_key_manager

logger = logging.getLogger(__name__)

class MLSGridClient(RESOWebAPIClient):
    """MLSGrid specific implementation of RESO Web API v2"""
    
    DEFAULT_BASE_URL = "https://api.mlsgrid.com/v2"
    
    # MLSGrid specific rate limits
    RATE_LIMITS = {
        'requests_per_second': 2,
        'requests_per_hour': 7200,
        'requests_per_day': 40000,
        'download_gb_per_hour': 4
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize MLSGrid client
        
        Args:
            api_key: MLSGrid API key (OAuth2 token)
            **kwargs: Additional configuration options
        """
        # Get API key from manager if not provided
        if not api_key:
            api_key = api_key_manager.get_api_key('mlsgrid')
            
        if not api_key:
            logger.error("MLSGrid API key not configured")
            raise ValueError("MLSGrid API key required")
            
        # MLSGrid specific configuration
        base_url = kwargs.pop('base_url', self.DEFAULT_BASE_URL)
        
        # MLSGrid rate limits: max 2 requests per second
        kwargs.setdefault('rate_limit_delay', 0.5)
        
        # MLSGrid recommends smaller page sizes when using expand
        kwargs.setdefault('page_size', 100)
        
        super().__init__(base_url, api_key, **kwargs)
        
        # Track usage for rate limiting
        self.request_count = {
            'hourly': 0,
            'daily': 0,
            'hour_start': datetime.now(),
            'day_start': datetime.now()
        }
        
        logger.info("Initialized MLSGrid client")
        
    def _setup_auth(self):
        """Set up MLSGrid OAuth2 authentication"""
        # MLSGrid uses Bearer token (OAuth2)
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'RealEstateCommandCenter/1.0'
        })
        
    def _check_rate_limits(self):
        """Check and update rate limit counters"""
        now = datetime.now()
        
        # Reset hourly counter
        if (now - self.request_count['hour_start']).seconds >= 3600:
            self.request_count['hourly'] = 0
            self.request_count['hour_start'] = now
            
        # Reset daily counter
        if (now - self.request_count['day_start']).days >= 1:
            self.request_count['daily'] = 0
            self.request_count['day_start'] = now
            
        # Check limits
        if self.request_count['hourly'] >= self.RATE_LIMITS['requests_per_hour']:
            logger.warning("Hourly rate limit reached")
            return False
        if self.request_count['daily'] >= self.RATE_LIMITS['requests_per_day']:
            logger.warning("Daily rate limit reached")
            return False
            
        return True
        
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Optional[Dict]:
        """Make request with MLSGrid specific handling"""
        # Check rate limits
        if not self._check_rate_limits():
            logger.error("Rate limit exceeded")
            return None
            
        # Update counters
        self.request_count['hourly'] += 1
        self.request_count['daily'] += 1
        
        return super()._make_request(method, endpoint, params, data)
        
    def search_properties(self, filters: Dict[str, Any], 
                         originating_system: str,
                         select: Optional[List[str]] = None,
                         expand: Optional[List[str]] = None,
                         orderby: Optional[str] = None,
                         top: Optional[int] = None,
                         skip: Optional[int] = None) -> Optional[Dict]:
        """
        Search properties with MLSGrid specific requirements
        
        MLSGrid requires OriginatingSystemName in every query
        """
        # MLSGrid requires OriginatingSystemName
        filters['OriginatingSystemName'] = originating_system
        
        # Adjust page size if using expand (MLSGrid limit: 1000 with expand)
        if expand and top and top > 1000:
            logger.warning("MLSGrid limits results to 1000 when using expand")
            top = 1000
            
        return super().search_properties(filters, select, expand, orderby, top, skip)
        
    def get_active_listings(self, 
                           originating_system: str,
                           city: Optional[str] = None,
                           state: Optional[str] = None,
                           min_price: Optional[float] = None,
                           max_price: Optional[float] = None,
                           property_type: Optional[str] = None,
                           min_beds: Optional[int] = None,
                           min_baths: Optional[float] = None,
                           modified_since: Optional[datetime] = None,
                           limit: int = 100) -> List[Dict]:
        """Get active property listings"""
        filters = {
            'StandardStatus': 'Active'
        }
        
        # Add optional filters
        if city:
            filters['City'] = city
        if state:
            filters['StateOrProvince'] = state
        if property_type:
            filters['PropertyType'] = property_type
        if min_beds:
            filters['BedroomsTotal'] = {'gte': min_beds}
        if min_baths:
            filters['BathroomsFull'] = {'gte': min_baths}
        if min_price and max_price:
            filters['ListPrice'] = {'gte': min_price, 'lte': max_price}
        elif min_price:
            filters['ListPrice'] = {'gte': min_price}
        elif max_price:
            filters['ListPrice'] = {'lte': max_price}
            
        # MLSGrid supports modification timestamp filtering
        if modified_since:
            filters['ModificationTimestamp'] = {
                'gt': modified_since.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
            
        # Search with filters
        result = self.search_properties(
            filters=filters,
            originating_system=originating_system,
            orderby='ModificationTimestamp desc',
            top=limit,
            expand=['Media', 'Rooms']  # Include photos and room details
        )
        
        if result and 'value' in result:
            properties = []
            for prop in result['value']:
                standard = self.convert_to_standard_format(prop)
                
                # Add media if available
                if 'Media' in prop and prop['Media']:
                    standard['media'] = [{
                        'url': media.get('MediaURL'),
                        'caption': media.get('ShortDescription', ''),
                        'type': media.get('MediaCategory', 'Photo'),
                        'order': media.get('Order', 0)
                    } for media in prop['Media']]
                    
                # Add rooms if available
                if 'Rooms' in prop and prop['Rooms']:
                    standard['rooms'] = [{
                        'name': room.get('RoomType', ''),
                        'dimensions': room.get('RoomDimensions', ''),
                        'features': room.get('RoomFeatures', [])
                    } for room in prop['Rooms']]
                    
                properties.append(standard)
                
            return properties
            
        return []
        
    def get_systems(self) -> List[str]:
        """Get list of available originating systems"""
        # This would typically require a specific endpoint or metadata query
        # For now, return common systems
        return [
            'mls_pin',    # Midwest Real Estate Data
            'actris',     # Austin Board of REALTORS
            'harmls',     # Houston Association of REALTORS
            'ntreis',     # North Texas Real Estate Information Systems
            'maris',      # MetroList
            'rmls',       # Regional Multiple Listing Service (Portland)
            'gamls',      # Georgia MLS
            'fmls',       # First Multiple Listing Service (Atlanta)
            'bright',     # Bright MLS (Mid-Atlantic)
            'crmls'       # California Regional MLS
        ]
        
    def get_property_types(self, originating_system: str) -> List[str]:
        """Get available property types for a system"""
        # Query for distinct property types
        result = self.search_properties(
            filters={'OriginatingSystemName': originating_system},
            originating_system=originating_system,
            select=['PropertyType'],
            top=1000
        )
        
        if result and 'value' in result:
            types = set()
            for prop in result['value']:
                if prop.get('PropertyType'):
                    types.add(prop['PropertyType'])
            return sorted(list(types))
            
        return []
        
    def replicate_data(self, 
                      originating_system: str,
                      resource: str = 'Property',
                      modified_since: Optional[datetime] = None,
                      callback=None) -> int:
        """
        Replicate data from MLSGrid (for building local database)
        
        Args:
            originating_system: MLS system to replicate from
            resource: Resource type to replicate
            modified_since: Only get records modified after this time
            callback: Function to call with each batch of records
            
        Returns:
            Total number of records processed
        """
        total_processed = 0
        skip = 0
        
        filters = {}
        if modified_since:
            filters['ModificationTimestamp'] = {
                'gt': modified_since.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
            
        while True:
            # Get batch of records
            result = self._make_request(
                'GET',
                resource,
                params={
                    '$filter': f"OriginatingSystemName eq '{originating_system}'",
                    '$orderby': 'ModificationTimestamp',
                    '$top': self.page_size,
                    '$skip': skip
                }
            )
            
            if not result or 'value' not in result:
                break
                
            records = result['value']
            if not records:
                break
                
            # Process batch
            if callback:
                callback(records)
                
            total_processed += len(records)
            skip += len(records)
            
            # Check if more records available
            if '@odata.nextLink' not in result:
                break
                
            logger.info(f"Processed {total_processed} records...")
            
        return total_processed
        
    def test_connection(self) -> bool:
        """Test the API connection"""
        try:
            # Try a simple query
            result = self._make_request(
                'GET',
                'Property',
                params={
                    '$top': 1,
                    '$select': 'ListingKey'
                }
            )
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
            
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            'hourly_requests': self.request_count['hourly'],
            'daily_requests': self.request_count['daily'],
            'limits': self.RATE_LIMITS,
            'hour_reset': self.request_count['hour_start'].isoformat(),
            'day_reset': self.request_count['day_start'].isoformat()
        }