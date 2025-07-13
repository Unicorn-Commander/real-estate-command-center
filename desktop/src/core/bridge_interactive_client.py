"""
Bridge Interactive API Client
Implements Bridge Interactive's RESO Web API for MLS data access
"""
import logging
from typing import Dict, List, Optional, Any
from core.reso_web_api import RESOWebAPIClient
from core.api_key_manager import api_key_manager

logger = logging.getLogger(__name__)

class BridgeInteractiveClient(RESOWebAPIClient):
    """Bridge Interactive specific implementation of RESO Web API"""
    
    DEFAULT_BASE_URL = "https://api.bridgedataoutput.com/api/v2"
    
    def __init__(self, api_key: Optional[str] = None, server_id: Optional[str] = None, **kwargs):
        """
        Initialize Bridge Interactive client
        
        Args:
            api_key: Bridge Interactive API key (will check env/settings if not provided)
            server_id: Server ID for the specific MLS (required for Bridge)
            **kwargs: Additional configuration options
        """
        # Get API key from manager if not provided
        if not api_key:
            api_key = api_key_manager.get_api_key('bridge')
            
        if not api_key:
            logger.error("Bridge Interactive API key not configured")
            raise ValueError("Bridge Interactive API key required")
            
        self.server_id = server_id
        
        # Bridge Interactive specific configuration
        base_url = kwargs.pop('base_url', self.DEFAULT_BASE_URL)
        
        # Bridge has specific rate limits
        kwargs.setdefault('rate_limit_delay', 0.5)  # 2 requests per second max
        
        super().__init__(base_url, api_key, **kwargs)
        
        logger.info(f"Initialized Bridge Interactive client for server: {server_id}")
        
    def _setup_auth(self):
        """Set up Bridge Interactive authentication"""
        # Bridge uses Bearer token authentication
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Bridge requires server ID in some endpoints
        if self.server_id:
            self.session.headers['X-Server-ID'] = self.server_id
            
    def search_properties(self, filters: Dict[str, Any], 
                         select: Optional[List[str]] = None,
                         expand: Optional[List[str]] = None,
                         orderby: Optional[str] = None,
                         top: Optional[int] = None,
                         skip: Optional[int] = None) -> Optional[Dict]:
        """
        Search properties with Bridge Interactive specific handling
        
        Bridge requires OriginatingSystemName in filters
        """
        # Ensure we have the required filter
        if self.server_id and 'OriginatingSystemName' not in filters:
            filters['OriginatingSystemName'] = self.server_id
            
        # Bridge recommends specific field selection for performance
        if not select:
            select = self.PROPERTY_FIELDS
            
        return super().search_properties(filters, select, expand, orderby, top, skip)
        
    def get_active_listings(self, 
                           city: Optional[str] = None,
                           min_price: Optional[float] = None,
                           max_price: Optional[float] = None,
                           property_type: Optional[str] = None,
                           min_beds: Optional[int] = None,
                           min_baths: Optional[float] = None,
                           limit: int = 100) -> List[Dict]:
        """Get active property listings with filters"""
        filters = {
            'StandardStatus': 'Active'
        }
        
        # Add optional filters
        if city:
            filters['City'] = city
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
            
        # Search with filters
        result = self.search_properties(
            filters=filters,
            orderby='ListPrice desc',
            top=limit,
            expand=['Media']  # Include photos
        )
        
        if result and 'value' in result:
            # Convert to standard format
            properties = []
            for prop in result['value']:
                standard = self.convert_to_standard_format(prop)
                
                # Add media if available
                if 'Media' in prop and prop['Media']:
                    standard['media'] = [{
                        'url': media.get('MediaURL'),
                        'caption': media.get('ShortDescription'),
                        'order': media.get('Order', 0)
                    } for media in prop['Media']]
                    
                properties.append(standard)
                
            return properties
            
        return []
        
    def get_comparable_sales(self, 
                            latitude: float, 
                            longitude: float,
                            radius_miles: float = 1.0,
                            property_type: Optional[str] = None,
                            days_back: int = 180,
                            limit: int = 20) -> List[Dict]:
        """Get comparable sold properties near a location"""
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        filters = {
            'StandardStatus': 'Closed',
            'CloseDate': {
                'gte': start_date.strftime('%Y-%m-%dT00:00:00Z'),
                'lte': end_date.strftime('%Y-%m-%dT23:59:59Z')
            }
        }
        
        if property_type:
            filters['PropertyType'] = property_type
            
        # Note: Bridge doesn't support direct geo queries in OData
        # Would need to fetch properties and filter by distance client-side
        # or use a specific Bridge endpoint if available
        
        result = self.search_properties(
            filters=filters,
            select=self.PROPERTY_FIELDS + ['ClosePrice'],
            orderby='CloseDate desc',
            top=limit * 3  # Get extra to filter by distance
        )
        
        if result and 'value' in result:
            # Filter by distance client-side
            comparables = []
            for prop in result['value']:
                prop_lat = prop.get('Latitude')
                prop_lon = prop.get('Longitude')
                
                if prop_lat and prop_lon:
                    # Calculate distance (simple approximation)
                    import math
                    lat_diff = prop_lat - latitude
                    lon_diff = prop_lon - longitude
                    distance = math.sqrt(lat_diff**2 + lon_diff**2) * 69  # Rough miles conversion
                    
                    if distance <= radius_miles:
                        standard = self.convert_to_standard_format(prop)
                        standard['distance_miles'] = round(distance, 2)
                        comparables.append(standard)
                        
                        if len(comparables) >= limit:
                            break
                            
            # Sort by distance
            comparables.sort(key=lambda x: x['distance_miles'])
            return comparables
            
        return []
        
    def get_market_statistics(self, 
                             city: str,
                             property_type: Optional[str] = None,
                             days_back: int = 90) -> Dict[str, Any]:
        """Get market statistics for an area"""
        from datetime import datetime, timedelta
        import statistics
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get active listings
        active_filters = {
            'StandardStatus': 'Active',
            'City': city
        }
        if property_type:
            active_filters['PropertyType'] = property_type
            
        active_result = self.search_properties(
            filters=active_filters,
            select=['ListPrice', 'DaysOnMarket', 'PropertyType'],
            top=500
        )
        
        # Get sold properties
        sold_filters = {
            'StandardStatus': 'Closed',
            'City': city,
            'CloseDate': {
                'gte': start_date.strftime('%Y-%m-%dT00:00:00Z'),
                'lte': end_date.strftime('%Y-%m-%dT23:59:59Z')
            }
        }
        if property_type:
            sold_filters['PropertyType'] = property_type
            
        sold_result = self.search_properties(
            filters=sold_filters,
            select=['ListPrice', 'ClosePrice', 'DaysOnMarket'],
            top=500
        )
        
        # Calculate statistics
        stats = {
            'city': city,
            'property_type': property_type or 'All',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'active_listings': 0,
            'sold_properties': 0,
            'average_list_price': 0,
            'median_list_price': 0,
            'average_sale_price': 0,
            'median_sale_price': 0,
            'average_days_on_market': 0,
            'price_to_list_ratio': 0
        }
        
        # Process active listings
        if active_result and 'value' in active_result:
            active = active_result['value']
            stats['active_listings'] = len(active)
            
            if active:
                list_prices = [p['ListPrice'] for p in active if p.get('ListPrice')]
                if list_prices:
                    stats['average_list_price'] = statistics.mean(list_prices)
                    stats['median_list_price'] = statistics.median(list_prices)
                    
        # Process sold properties
        if sold_result and 'value' in sold_result:
            sold = sold_result['value']
            stats['sold_properties'] = len(sold)
            
            if sold:
                sale_prices = [p['ClosePrice'] for p in sold if p.get('ClosePrice')]
                if sale_prices:
                    stats['average_sale_price'] = statistics.mean(sale_prices)
                    stats['median_sale_price'] = statistics.median(sale_prices)
                    
                # Calculate days on market
                dom_values = [p['DaysOnMarket'] for p in sold if p.get('DaysOnMarket')]
                if dom_values:
                    stats['average_days_on_market'] = statistics.mean(dom_values)
                    
                # Calculate price to list ratio
                ratios = []
                for p in sold:
                    if p.get('ClosePrice') and p.get('ListPrice') and p['ListPrice'] > 0:
                        ratios.append(p['ClosePrice'] / p['ListPrice'])
                if ratios:
                    stats['price_to_list_ratio'] = statistics.mean(ratios)
                    
        return stats
        
    def test_connection(self) -> bool:
        """Test the API connection"""
        try:
            # Try to get metadata
            result = self.get_metadata()
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False