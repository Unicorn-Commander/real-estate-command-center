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
    
    def __init__(self, provider: str = 'bridge'):
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
        
        # Set up provider-specific configuration
        config = self.api_configs.get(self.provider, {})
        self.api_key = os.getenv(config.get('api_key_env', 'MLS_API_KEY'))
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
        
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Helper to make authenticated API requests"""
        # Rate limiting
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        
        self.last_request_time = time.time()

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP Error: {e.response.status_code}", "details": e.response.text}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            return {"error": "Connection Error", "details": str(e)}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            return {"error": "Timeout Error", "details": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return {"error": "Request Error", "details": str(e)}
        except json.JSONDecodeError:
            logger.error(f"JSON decode error for {url}: {response.text}")
            return {"error": "Invalid JSON response"}

    def search_properties(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for properties based on query parameters"""
        logger.info(f"Searching MLS properties with: {query_params}")
        # Example endpoint, adjust based on actual API documentation
        response = self._make_request("properties", params=query_params)
        if response and "value" in response: # Bridge Interactive often returns data in 'value' key
            return response["value"]
        return []

    def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific property by ID"""
        logger.info(f"Fetching MLS details for property ID: {property_id}")
        # Example endpoint, adjust based on actual API documentation
        response = self._make_request(f"properties/{property_id}")
        if response and "value" in response: # Bridge Interactive often returns data in 'value' key
            return response["value"]
        return None

    def get_comparable_sales(self, property_id: str, radius_miles: int = 5, limit: int = 5) -> List[Dict[str, Any]]:
        """Get comparable sales for a given property"""
        logger.info(f"Fetching comparable sales for property ID: {property_id}")
        # This would typically involve a more complex query based on property features and location
        # For now, simulate a search around the property's location if details are available
        # In a real scenario, the MLS API would have a dedicated comparables endpoint or advanced search
        
        # Placeholder: In a real scenario, you'd get the subject property's lat/lon and search around it.
        # For now, we'll just return some mock comparables.
        
        # In a real implementation, you'd use the property_id to get the subject property's location
        # and then search for recently sold properties within a radius.
        
        # For demonstration, let's return some mock data.
        mock_comparables = [
            {
                "address": "123 Mock St, Anytown, CA",
                "sale_price": 550000,
                "sale_date": "2024-05-01",
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1800,
                "distance_miles": 0.5
            },
            {
                "address": "456 Demo Ave, Anytown, CA",
                "sale_price": 580000,
                "sale_date": "2024-04-15",
                "bedrooms": 4,
                "bathrooms": 2.5,
                "square_feet": 2200,
                "distance_miles": 1.2
            }
        ]
        return mock_comparables

    def get_market_statistics(self, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Get market statistics for a given city and state"""
        logger.info(f"Fetching market statistics for {city}, {state}")
        # This would typically be a separate endpoint or a complex aggregation
        # Example endpoint, adjust based on actual API documentation
        response = self._make_request("market_stats", params={"city": city, "state": state})
        if response and "value" in response: # Bridge Interactive often returns data in 'value' key
            return response["value"]
        return None

