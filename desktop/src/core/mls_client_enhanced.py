import requests
import os
import json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class MLSClient:
    """Enhanced MLS Client supporting multiple providers"""
    
    def __init__(self, provider: str = 'bridge', settings: Dict[str, Any] = None):
        """Initialize MLS client with specified provider
        
        Supported providers:
        - 'bridge': Bridge Interactive (free, requires MLS approval)
        - 'mlsgrid': MLS Grid (RESO compliant)
        - 'rentspree': RentSpree API 
        - 'estated': Estated Public Records API (free tier available)
        - 'attom': ATTOM Data API
        """
        self.provider = provider.lower()
        self.api_configs = self._get_api_configurations()
        self.settings = settings or {}
        
        # Set up provider-specific configuration
        config = self.api_configs.get(self.provider, {})
        api_key_env_name = config.get('api_key_env', 'MLS_API_KEY')
        self.api_key = self.settings.get('mls_providers', {}).get(api_key_env_name.lower(), '')
        
        if not self.api_key:
            # Fallback to environment variable if not in settings
            self.api_key = os.getenv(api_key_env_name)

        self.base_url = config.get('base_url', '')
        self.headers = config.get('headers', {})
        
        # Add API key to headers if available
        if self.api_key:
            auth_header = config.get('auth_header', 'Authorization')
            auth_format = config.get('auth_format', 'Bearer {}')
            self.headers[auth_header] = auth_format.format(self.api_key)
        else:
            logger.warning(f"{config.get('api_key_env', 'MLS_API_KEY')} not set. {self.provider} integration may not function.")
            
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = config.get('rate_limit_seconds', 1)
        
        logger.info(f"Initialized MLS client for provider: {self.provider}")
    
    def _get_api_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all supported MLS providers"""
        return {
            'bridge': {
                'name': 'Bridge Interactive',
                'base_url': 'https://api.bridgeinteractive.com/v2',
                'api_key_env': 'BRIDGE_API_KEY',
                'auth_header': 'Authorization',
                'auth_format': 'Bearer {}',
                'headers': {'Accept': 'application/json', 'Content-Type': 'application/json'},
                'rate_limit_seconds': 1,
                'data_key': 'value',  # Bridge returns data in 'value' key
                'reso_compliant': True
            },
            'mlsgrid': {
                'name': 'MLS Grid',
                'base_url': 'https://api.mlsgrid.com/v2',
                'api_key_env': 'MLSGRID_API_KEY',
                'auth_header': 'Authorization',
                'auth_format': 'Bearer {}',
                'headers': {'Accept': 'application/json'},
                'rate_limit_seconds': 1,
                'data_key': 'value',
                'reso_compliant': True
            },
            'rentspree': {
                'name': 'RentSpree',
                'base_url': 'https://api.rentspree.com/v1',
                'api_key_env': 'RENTSPREE_API_KEY',
                'auth_header': 'X-API-Key',
                'auth_format': '{}',
                'headers': {'Accept': 'application/json'},
                'rate_limit_seconds': 0.5,
                'data_key': 'data'
            },
            'estated': {
                'name': 'Estated Public Records',
                'base_url': 'https://apis.estated.com/v4',
                'api_key_env': 'ESTATED_API_KEY',
                'auth_header': 'Authorization',
                'auth_format': 'Bearer {}',
                'headers': {'Accept': 'application/json'},
                'rate_limit_seconds': 1,
                'data_key': 'data',
                'free_tier': True  # Has free tier
            },
            'attom': {
                'name': 'ATTOM Data',
                'base_url': 'https://api.gateway.attomdata.com/propertyapi/v1.0.0',
                'api_key_env': 'ATTOM_API_KEY',
                'auth_header': 'apikey',
                'auth_format': '{}',
                'headers': {'Accept': 'application/json'},
                'rate_limit_seconds': 1,
                'data_key': 'property'
            }
        }
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = 'GET') -> Optional[Dict[str, Any]]:
        """Enhanced helper to make authenticated API requests with rate limiting"""
        if not self.base_url:
            logger.error(f"No base URL configured for provider: {self.provider}")
            return {'error': 'Provider not configured', 'provider': self.provider}
            
        self._respect_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=params, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"Authentication failed for {self.provider}: Check API key")
                return {'error': 'Authentication failed', 'status_code': 401}
            elif e.response.status_code == 403:
                logger.error(f"Access forbidden for {self.provider}: Check permissions/subscription")
                return {'error': 'Access forbidden', 'status_code': 403}
            elif e.response.status_code == 429:
                logger.error(f"Rate limit exceeded for {self.provider}")
                return {'error': 'Rate limit exceeded', 'status_code': 429}
            else:
                logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
                return {'error': f'HTTP Error: {e.response.status_code}', 'details': e.response.text}
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            return {'error': 'Connection Error', 'details': str(e)}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            return {'error': 'Timeout Error', 'details': str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return {'error': 'Request Error', 'details': str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {url}: Invalid response format")
            return {'error': 'Invalid JSON response', 'details': str(e)}

    def _transform_search_params(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform search parameters for provider-specific format"""
        if self.provider in ['bridge', 'mlsgrid']:  # RESO compliant
            # RESO standard field mappings
            transformed = {}
            
            if 'city' in query_params:
                transformed['City'] = query_params['city']
            if 'state' in query_params:
                transformed['StateOrProvince'] = query_params['state']
            if 'min_price' in query_params:
                transformed['ListPrice'] = f"ge{query_params['min_price']}"
            if 'max_price' in query_params:
                if 'ListPrice' in transformed:
                    transformed['ListPrice'] += f",le{query_params['max_price']}"
                else:
                    transformed['ListPrice'] = f"le{query_params['max_price']}"
            if 'bedrooms' in query_params:
                transformed['BedroomsTotal'] = f"ge{query_params['bedrooms']}"
            if 'property_type' in query_params:
                transformed['PropertyType'] = query_params['property_type']
                
            # Add standard filters
            transformed['$filter'] = 'StandardStatus eq \'Active\''
            transformed['$top'] = query_params.get('limit', 50)
            
            return transformed
            
        elif self.provider == 'estated':
            # Estated parameter format
            return {
                'address': query_params.get('address', ''),
                'city': query_params.get('city', ''),
                'state': query_params.get('state', ''),
                'zip_code': query_params.get('zip_code', '')
            }
            
        else:
            # Default format for other providers
            return query_params

    def search_properties(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for properties based on query parameters"""
        if not self.api_key:
            logger.warning(f"No API key available for {self.provider}, returning empty results")
            return []
            
        logger.info(f"Searching {self.provider} properties with: {query_params}")
        
        # Provider-specific endpoint mapping
        endpoint_map = {
            'bridge': 'Property',
            'mlsgrid': 'Property', 
            'rentspree': 'listings',
            'estated': 'property',
            'attom': 'property/search'
        }
        
        endpoint = endpoint_map.get(self.provider, 'properties')
        
        # Transform query parameters for provider-specific format
        transformed_params = self._transform_search_params(query_params)
        
        response = self._make_request(endpoint, params=transformed_params)
        if response and not response.get('error'):
            config = self.api_configs[self.provider]
            data_key = config.get('data_key', 'data')
            
            if data_key in response:
                return response[data_key] if isinstance(response[data_key], list) else [response[data_key]]
            elif isinstance(response, list):
                return response
            else:
                return [response]  # Single property result
        
        if response and response.get('error'):
            logger.error(f"Search failed for {self.provider}: {response['error']}")
            
        return []

    def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific property by ID"""
        if not self.api_key:
            logger.warning(f"No API key available for {self.provider}")
            return None
            
        logger.info(f"Fetching {self.provider} details for property ID: {property_id}")
        
        # Provider-specific endpoint format
        if self.provider in ['bridge', 'mlsgrid']:
            endpoint = f"Property('{property_id}')"
        elif self.provider == 'estated':
            endpoint = f"property/{property_id}"
        else:
            endpoint = f"properties/{property_id}"
            
        response = self._make_request(endpoint)
        if response and not response.get('error'):
            config = self.api_configs[self.provider]
            data_key = config.get('data_key', 'data')
            
            if data_key in response:
                return response[data_key]
            else:
                return response
                
        return None

    def get_comparable_sales(self, property_id: str, radius_miles: int = 5, limit: int = 5) -> List[Dict[str, Any]]:
        """Get comparable sales for a given property"""
        if not self.api_key:
            logger.warning(f"No API key available for {self.provider}, comparables unavailable")
            return []
            
        logger.info(f"Fetching comparable sales from {self.provider} for property ID: {property_id}")
        
        try:
            # First get the subject property details to find location
            subject_property = self.get_property_details(property_id)
            if not subject_property:
                logger.warning("Could not fetch subject property details for comparables")
                return []
            
            # Extract location and property characteristics
            lat = subject_property.get('Latitude') or subject_property.get('lat')
            lon = subject_property.get('Longitude') or subject_property.get('lon')
            bedrooms = subject_property.get('BedroomsTotal') or subject_property.get('bedrooms')
            bathrooms = subject_property.get('BathroomsTotal') or subject_property.get('bathrooms')
            sqft = subject_property.get('LivingArea') or subject_property.get('square_feet')
            
            if not (lat and lon):
                logger.warning("No coordinates available for comparable search")
                return []
            
            # Build comparable search parameters
            if self.provider in ['bridge', 'mlsgrid']:  # RESO compliant
                params = {
                    '$filter': f"StandardStatus eq 'Closed' and geo.distance(geography'POINT({lon} {lat})', location) le {radius_miles * 1609.34}",  # Convert miles to meters
                    '$orderby': 'CloseDate desc',
                    '$top': limit
                }
                
                # Add property characteristic filters if available
                if bedrooms:
                    params['$filter'] += f" and BedroomsTotal ge {max(1, bedrooms-1)} and BedroomsTotal le {bedrooms+1}"
                if sqft:
                    sqft_range = int(sqft * 0.2)  # 20% variance
                    params['$filter'] += f" and LivingArea ge {sqft - sqft_range} and LivingArea le {sqft + sqft_range}"
                    
                response = self._make_request('Property', params=params)
                
            elif self.provider == 'estated':
                # Estated doesn't have direct comparable search, would need custom logic
                logger.info("Estated comparables search not yet implemented")
                return []
                
            else:
                # Generic provider format
                params = {
                    'lat': lat,
                    'lon': lon,
                    'radius': radius_miles,
                    'status': 'sold',
                    'limit': limit
                }
                response = self._make_request('comparables', params=params)
            
            if response and not response.get('error'):
                config = self.api_configs[self.provider]
                data_key = config.get('data_key', 'data')
                
                if data_key in response:
                    return response[data_key] if isinstance(response[data_key], list) else [response[data_key]]
                elif isinstance(response, list):
                    return response
                    
        except Exception as e:
            logger.error(f"Error fetching comparables from {self.provider}: {e}")
            
        return []
    

    def get_market_statistics(self, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Get market statistics for a given city and state"""
        if not self.api_key:
            logger.warning(f"No API key available for {self.provider}, market data unavailable")
            return {}
            
        logger.info(f"Fetching market statistics from {self.provider} for {city}, {state}")
        
        try:
            if self.provider in ['bridge', 'mlsgrid']:  # RESO compliant
                # Get active listings for market analysis
                active_params = {
                    '$filter': f"City eq '{city}' and StateOrProvince eq '{state}' and StandardStatus eq 'Active'",
                    '$select': 'ListPrice,BedroomsTotal,BathroomsTotal,LivingArea,DaysOnMarket,PropertyType',
                    '$top': 500
                }
                
                # Get recent sales for trend analysis  
                sold_params = {
                    '$filter': f"City eq '{city}' and StateOrProvince eq '{state}' and StandardStatus eq 'Closed' and CloseDate gt {datetime.now().year-1}-01-01T00:00:00Z",
                    '$select': 'ClosePrice,BedroomsTotal,BathroomsTotal,LivingArea,CloseDate,PropertyType',
                    '$top': 500
                }
                
                active_response = self._make_request('Property', params=active_params)
                sold_response = self._make_request('Property', params=sold_params)
                
                if active_response and sold_response and not active_response.get('error') and not sold_response.get('error'):
                    return self._calculate_market_stats(active_response, sold_response, city, state)
                    
            elif self.provider == 'estated':
                # Estated doesn't provide market statistics directly
                logger.info("Estated market statistics not available")
                return {}
                
            else:
                # Generic provider format
                params = {'city': city, 'state': state}
                response = self._make_request('market_stats', params=params)
                
                if response and not response.get('error'):
                    config = self.api_configs[self.provider]
                    data_key = config.get('data_key', 'data')
                    
                    if data_key in response:
                        return response[data_key]
                    else:
                        return response
                        
        except Exception as e:
            logger.error(f"Error fetching market statistics from {self.provider}: {e}")
            
        return {}
    
    def _calculate_market_stats(self, active_response: Dict, sold_response: Dict, city: str, state: str) -> Dict[str, Any]:
        """Calculate market statistics from active and sold listings"""
        config = self.api_configs[self.provider]
        data_key = config.get('data_key', 'value')
        
        active_listings = active_response.get(data_key, [])
        sold_listings = sold_response.get(data_key, [])
        
        if not isinstance(active_listings, list):
            active_listings = [active_listings] if active_listings else []
        if not isinstance(sold_listings, list):
            sold_listings = [sold_listings] if sold_listings else []
        
        # Calculate statistics
        active_prices = [listing.get('ListPrice', 0) for listing in active_listings if listing.get('ListPrice')]
        sold_prices = [listing.get('ClosePrice', 0) for listing in sold_listings if listing.get('ClosePrice')]
        days_on_market = [listing.get('DaysOnMarket', 0) for listing in active_listings if listing.get('DaysOnMarket')]
        
        import statistics
        
        return {
            'location': f'{city}, {state}',
            'total_active_listings': len(active_listings),
            'total_sales_last_year': len(sold_listings),
            'median_list_price': statistics.median(active_prices) if active_prices else 0,
            'median_sale_price': statistics.median(sold_prices) if sold_prices else 0,
            'average_days_on_market': statistics.mean(days_on_market) if days_on_market else 0,
            'price_range': {
                'min_active': min(active_prices) if active_prices else 0,
                'max_active': max(active_prices) if active_prices else 0
            },
            'market_activity': 'High' if len(active_listings) > 100 else 'Moderate' if len(active_listings) > 50 else 'Low',
            'data_source': f'{self.provider.title()} API',
            'last_updated': datetime.now().isoformat()
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection and return provider info"""
        config = self.api_configs.get(self.provider, {})
        
        result = {
            'provider': self.provider,
            'provider_name': config.get('name', 'Unknown'),
            'has_api_key': bool(self.api_key),
            'base_url': self.base_url,
            'reso_compliant': config.get('reso_compliant', False),
            'free_tier': config.get('free_tier', False)
        }
        
        if self.api_key:
            # Try a simple test request
            test_response = self._make_request('Property', params={'$top': 1})
            if test_response and not test_response.get('error'):
                result['connection_status'] = 'success'
                result['message'] = f'Successfully connected to {config.get("name", self.provider)}'
            else:
                result['connection_status'] = 'failed'
                result['message'] = test_response.get('error', 'Connection test failed')
        else:
            result['connection_status'] = 'no_api_key'
            result['message'] = f'No API key configured for {config.get("name", self.provider)}'
            
        return result


# Factory function for easy MLS client creation
def create_mls_client(provider: str = 'bridge', settings: Dict[str, Any] = None) -> MLSClient:
    """Factory function to create MLS client with specified provider
    """
    return MLSClient(provider=provider, settings=settings)


# Multi-provider MLS aggregator
class MLSAggregator:
    """Aggregates data from multiple MLS providers for redundancy"""
    
    def __init__(self, providers: List[str] = None, settings: Dict[str, Any] = None):
        """Initialize with list of provider names"""
        self.settings = settings
        if providers is None:
            # Default to providers with API keys configured in settings
            providers = []
            if self.settings:
                mls_settings = self.settings.get('mls_providers', {})
                # Get API configurations from a dummy MLSClient instance
                dummy_client = MLSClient()
                for provider_name, config in dummy_client._get_api_configurations().items():
                    api_key_name = config.get('api_key_env', '').lower()
                    if mls_settings.get(api_key_name):
                        providers.append(provider_name)
            if not providers:
                providers = ['bridge', 'estated'] # Fallback if no keys configured
            
        self.clients = {}
        for provider in providers:
            try:
                self.clients[provider] = MLSClient(provider=provider, settings=self.settings)
                logger.info(f"Initialized {provider} MLS client")
            except Exception as e:
                logger.error(f"Failed to initialize {provider} MLS client: {e}")
    
    def search_properties(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search properties across all available providers"""
        all_results = []
        
        for provider, client in self.clients.items():
            try:
                results = client.search_properties(query_params)
                if results:
                    # Add provider metadata to each result
                    for result in results:
                        result['_data_source'] = provider
                    all_results.extend(results)
                    logger.info(f"Got {len(results)} results from {provider}")
            except Exception as e:
                logger.error(f"Error searching {provider}: {e}")
        
        return all_results
    
    def get_best_market_statistics(self, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Get market statistics from the best available provider"""
        # Try providers in order of preference
        provider_priority = ['bridge', 'mlsgrid', 'attom', 'estated']
        
        for provider in provider_priority:
            if provider in self.clients:
                try:
                    stats = self.clients[provider].get_market_statistics(city, state)
                    if stats and not stats.get('error'):
                        stats['_data_source'] = provider
                        return stats
                except Exception as e:
                    logger.error(f"Error getting market stats from {provider}: {e}")
        
        return None
    
    def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Test connections to all configured providers"""
        results = {}
        
        for provider, client in self.clients.items():
            try:
                results[provider] = client.test_connection()
            except Exception as e:
                results[provider] = {
                    'provider': provider,
                    'connection_status': 'error',
                    'message': str(e)
                }
        
        return results