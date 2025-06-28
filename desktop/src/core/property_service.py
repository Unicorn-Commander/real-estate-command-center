"""
Property Data Service - Real property information lookup
"""
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.property_scraper import PropertyScraper, PropertyDataEnhancer


class PropertyService:
    """Service for fetching real property data"""
    
    def __init__(self):
        # Multiple data sources for redundancy
        self.data_sources = {
            'geocoding': 'https://nominatim.openstreetmap.org/search',
            'zillow_mock': 'https://api.bridge-api.com',  # Placeholder for real API
        }
        
        # Initialize scraping components
        self.scraper = PropertyScraper()
        self.enhancer = PropertyDataEnhancer()
        
    def lookup_property(self, address: str) -> Dict[str, Any]:
        """Look up property by address and return comprehensive data"""
        try:
            # Step 1: Geocode the address
            location_data = self._geocode_address(address)
            if not location_data:
                return {'error': 'Address not found'}
            
            # Step 2: Get property details with web scraping enhancement
            property_data = self._get_property_details(address, location_data)
            
            # Step 3: Enhance with scraped data from multiple sources
            enhanced_data = self.enhancer.enhance_property_data({
                'address': address,
                'location': location_data,
                'property': property_data
            })
            
            # Step 4: Get comparable sales
            comparables = self._get_comparable_sales(location_data)
            
            # Step 5: Get market data
            market_data = self._get_market_data(location_data)
            
            result = {
                'address': address,
                'location': location_data,
                'property': enhanced_data.get('property', property_data),
                'comparables': comparables,
                'market': market_data,
                'scraped_data': enhanced_data.get('scraped_sources', {}),
                'data_confidence': enhanced_data.get('data_confidence', 0.5),
                'last_updated': datetime.now().isoformat()
            }
            
            # Add enhanced property details if available
            if 'consolidated_data' in enhanced_data:
                consolidated = enhanced_data['consolidated_data']
                for key, value in consolidated.items():
                    if value is not None and key != 'confidence_score':
                        result['property'][key] = value
            
            return result
            
        except Exception as e:
            return {'error': f'Property lookup failed: {str(e)}'}
    
    def _geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates and detailed location info"""
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = requests.get(
                self.data_sources['geocoding'], 
                params=params,
                timeout=10,
                headers={'User-Agent': 'RealEstateCommandCenter/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    return {
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result['display_name'],
                        'address_details': result.get('address', {}),
                        'importance': result.get('importance', 0.5)
                    }
            
            return None
            
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def _get_property_details(self, address: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed property information (currently using mock data)"""
        
        # TODO: Replace with real MLS/Zillow API
        # For now, generate realistic mock data based on location
        
        import random
        
        # Extract city/state for realistic pricing
        city = location['address_details'].get('city', 'Unknown')
        state = location['address_details'].get('state', 'Unknown')
        
        # Basic property type determination
        property_types = ['Single Family', 'Condo', 'Townhouse', 'Multi Family']
        property_type = random.choice(property_types)
        
        # Realistic pricing based on mock city data
        base_prices = {
            'Portland': 650000, 'Seattle': 850000, 'San Francisco': 1500000,
            'Austin': 450000, 'Denver': 550000, 'Miami': 400000
        }
        base_price = base_prices.get(city, 350000)
        
        # Generate realistic property details
        bedrooms = random.randint(2, 5)
        bathrooms = random.choice([1.5, 2, 2.5, 3, 3.5])
        sqft = random.randint(1200, 4000)
        
        # Price based on size and location
        price = int(base_price * (sqft / 2000) * random.uniform(0.8, 1.3))
        
        return {
            'type': property_type,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'square_feet': sqft,
            'lot_size': random.randint(5000, 15000),
            'year_built': random.randint(1960, 2020),
            'estimated_value': price,
            'last_sale_price': int(price * random.uniform(0.7, 0.9)),
            'last_sale_date': '2022-03-15',  # Mock date
            'property_tax': int(price * 0.012),  # Rough estimate
            'hoa_fees': random.randint(0, 300) if property_type in ['Condo', 'Townhouse'] else 0,
            'city': city,
            'state': state,
            'zip_code': location['address_details'].get('postcode', '00000')
        }
    
    def _get_comparable_sales(self, location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get comparable sales in the area"""
        
        # Mock comparable sales data
        import random
        
        comparables = []
        for i in range(5):
            # Generate nearby coordinates
            lat_offset = random.uniform(-0.01, 0.01)
            lon_offset = random.uniform(-0.01, 0.01)
            
            comp = {
                'address': f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Dr', 'Way'])}",
                'sale_price': random.randint(300000, 800000),
                'sale_date': f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                'bedrooms': random.randint(2, 5),
                'bathrooms': random.choice([1.5, 2, 2.5, 3]),
                'square_feet': random.randint(1200, 3500),
                'distance_miles': random.uniform(0.1, 1.5),
                'lat': location['lat'] + lat_offset,
                'lon': location['lon'] + lon_offset
            }
            comparables.append(comp)
        
        return comparables
    
    def _get_market_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Get market statistics for the area"""
        
        import random
        
        return {
            'median_home_value': random.randint(400000, 700000),
            'market_trend': random.choice(['Rising', 'Stable', 'Declining']),
            'days_on_market': random.randint(15, 60),
            'price_per_sqft': random.randint(200, 400),
            'market_temperature': random.choice(['Hot', 'Warm', 'Balanced', 'Cool']),
            'inventory_months': random.uniform(1.5, 6.0),
            'year_over_year_change': random.uniform(-5.0, 15.0)
        }
    
    def search_properties(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for properties matching criteria using web scraping"""
        try:
            city = criteria.get('city', 'Portland')
            state = criteria.get('state', 'OR')
            
            # Use scraper to get real area listings
            listings = self.scraper.search_area_listings(city, state, criteria)
            
            return listings
            
        except Exception as e:
            print(f"Property search error: {e}")
            return []
    
    def get_market_analysis(self, city: str, state: str) -> Dict[str, Any]:
        """Get comprehensive market analysis for an area"""
        try:
            # Search recent listings to analyze market
            listings = self.search_properties({'city': city, 'state': state})
            
            if not listings:
                return {'error': 'No market data available'}
            
            # Calculate market statistics
            prices = [listing['price'] for listing in listings]
            days_on_market = [listing['days_on_market'] for listing in listings]
            
            import statistics
            
            return {
                'location': f'{city}, {state}',
                'total_listings': len(listings),
                'median_price': statistics.median(prices),
                'average_price': statistics.mean(prices),
                'price_range': {
                    'min': min(prices),
                    'max': max(prices)
                },
                'average_days_on_market': statistics.mean(days_on_market),
                'market_activity': 'High' if len(listings) > 20 else 'Moderate' if len(listings) > 10 else 'Low',
                'property_types': list(set(listing['property_type'] for listing in listings)),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Market analysis failed: {str(e)}'}