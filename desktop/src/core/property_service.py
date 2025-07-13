"""
Property Data Service - Real property information lookup
"""
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.property_scraper import PropertyScraper, PropertyDataEnhancer
from core.mls_client_enhanced import create_mls_client, MLSAggregator, MLSClient
from core.public_data_scraper import create_public_scraper, parse_address_components, identify_county_from_address
from core.api_key_manager import api_key_manager


class PropertyService:
    """Service for fetching real property data"""
    
    def __init__(self, preferred_mls_provider: str = 'bridge', use_multiple_providers: bool = True, settings: dict = None):
        """Initialize PropertyService with enhanced MLS integration
        
        Args:
            preferred_mls_provider: Primary MLS provider to use ('bridge', 'mlsgrid', etc.)
            use_multiple_providers: Whether to use multiple MLS providers for redundancy
            settings: Application settings dictionary
        """
        self.settings = settings or {}
        
        # Multiple data sources for redundancy
        self.data_sources = {
            'geocoding': 'https://nominatim.openstreetmap.org/search',
        }
        
        # Initialize enhanced MLS integration
        self.mls_settings = self.settings.get('integrations', {}).get('mls_providers', {})
        self.preferred_mls_provider = self.mls_settings.get('preferred_provider', preferred_mls_provider)
        self.use_multiple_providers = self.mls_settings.get('use_multiple_providers', use_multiple_providers)

        # Initialize MLS clients with settings
        if self.use_multiple_providers:
            # Use MLS aggregator for multiple data sources
            self.mls_aggregator = MLSAggregator(settings=self.settings)
            self.primary_mls_client = create_mls_client(self.preferred_mls_provider, settings=self.settings)
        else:
            # Use single provider
            self.mls_aggregator = None
            self.primary_mls_client = create_mls_client(self.preferred_mls_provider, settings=self.settings)
        
        # Initialize legacy MLS client for backward compatibility (can be removed if not needed)
        self.mls_client = MLSClient(provider=self.preferred_mls_provider) # Use preferred provider for legacy client
        
        # Initialize scraping components
        self.scraper = PropertyScraper()
        self.enhancer = PropertyDataEnhancer()
        self.public_scraper = create_public_scraper()
        
        # Test MLS connections on startup
        self._test_mls_connections()
    
    def _test_mls_connections(self):
        """Test all MLS connections and log status"""
        try:
            # Test primary MLS client
            primary_status = self.primary_mls_client.test_connection()
            if primary_status['connection_status'] == 'success':
                print(f"✅ {primary_status['provider_name']} connected successfully")
            else:
                print(f"⚠️ {primary_status['provider_name']}: {primary_status['message']}")
            
            # Test aggregator if enabled
            if self.mls_aggregator:
                agg_status = self.mls_aggregator.test_all_connections()
                connected_count = sum(1 for status in agg_status.values() 
                                    if status.get('connection_status') == 'success')
                total_count = len(agg_status)
                print(f"📊 MLS Aggregator: {connected_count}/{total_count} providers connected")
                
        except Exception as e:
            print(f"⚠️ Error testing MLS connections: {e}")
        
    def lookup_property(self, address: str) -> Dict[str, Any]:
        """Enhanced property lookup with multiple MLS providers and public data"""
        try:
            # Step 1: Geocode the address and parse components
            location_data = self._geocode_address(address)
            if not location_data:
                return {'error': 'Address not found'}
            
            address_components = parse_address_components(address)
            city = location_data['address_details'].get('city', '')
            state = location_data['address_details'].get('state', '')
            county = identify_county_from_address(address, city, state)
            
            # Step 2: Enhanced MLS lookup with multiple providers
            property_data = None
            mls_property_id = None
            data_sources_used = []
            
            # Try primary MLS client first
            search_params = {
                'address': address,
                'city': city,
                'state': state
            }
            
            primary_results = self.primary_mls_client.search_properties(search_params)
            if primary_results:
                property_data = primary_results[0]
                mls_property_id = property_data.get('id') or property_data.get('ListingId')
                data_sources_used.append(f"{self.preferred_mls_provider}_mls")
                print(f"✅ Found property in {self.preferred_mls_provider.title()} MLS")
            
            # If no results from primary, try aggregator
            if not property_data and self.mls_aggregator:
                aggregated_results = self.mls_aggregator.search_properties(search_params)
                if aggregated_results:
                    property_data = aggregated_results[0]
                    mls_property_id = property_data.get('id') or property_data.get('ListingId')
                    data_source = property_data.get('_data_source', 'unknown')
                    data_sources_used.append(f"{data_source}_mls")
                    print(f"✅ Found property via MLS aggregator ({data_source})")
            
            # Step 3: Gather public records data
            public_data = None
            if county:
                try:
                    public_data = self.public_scraper.get_comprehensive_public_data(
                        address, city, county, state
                    )
                    if public_data and public_data.get('data_sources'):
                        data_sources_used.extend([f"public_{source.lower().replace(' ', '_')}" 
                                                for source in public_data['data_sources']])
                        print(f"✅ Found public records: {', '.join(public_data['data_sources'])}")
                except Exception as e:
                    print(f"⚠️ Public records lookup failed: {e}")
            
            # Step 4: Check if we have real data, otherwise return empty result
            if not property_data:
                print("⚠️ No MLS results found and no API key configured")
                return {
                    'error': 'No property data available - MLS API key required',
                    'address': address,
                    'location': location_data,
                    'data_sources': data_sources_used,
                    'confidence': 0.0
                }
            
            # Step 5: Enhance with scraped data from multiple sources
            enhanced_data = self.enhancer.enhance_property_data({
                'address': address,
                'location': location_data,
                'property': property_data
            })
            data_sources_used.extend(enhanced_data.get('scraped_sources', {}).keys())
            
            # Step 6: Get comparable sales (prioritize enhanced MLS)
            comparables = []
            if mls_property_id:
                # Try enhanced MLS client for comparables
                enhanced_comparables = self.primary_mls_client.get_comparable_sales(mls_property_id)
                if enhanced_comparables:
                    comparables = enhanced_comparables
                    data_sources_used.append(f"{self.preferred_mls_provider}_comparables")
                    print(f"✅ Found comparable sales from {self.preferred_mls_provider.title()}")
                else:
                    # Fallback to legacy MLS client
                    legacy_comparables = self.mls_client.get_comparable_sales(mls_property_id)
                    if legacy_comparables:
                        comparables = legacy_comparables
                        data_sources_used.append('legacy_mls_comparables')
                        print("✅ Found comparable sales from legacy MLS")
                    else:
                        comparables = []
                        data_sources_used.append('no_comparables')
                        print("⚠️ No comparable sales available - MLS API key required")
            else:
                comparables = []
                data_sources_used.append('no_comparables')
            
            # Step 7: Get market data (prioritize enhanced MLS)
            market_data = None
            
            # Try aggregator first for best market data
            if self.mls_aggregator:
                market_data = self.mls_aggregator.get_best_market_statistics(city, state)
                if market_data:
                    data_source = market_data.get('_data_source', 'aggregator')
                    data_sources_used.append(f"{data_source}_market")
                    print(f"✅ Found market data from {data_source}")
            
            # Fallback to primary MLS client
            if not market_data:
                market_data = self.primary_mls_client.get_market_statistics(city, state)
                if market_data:
                    data_sources_used.append(f"{self.preferred_mls_provider}_market")
                    print(f"✅ Found market data from {self.preferred_mls_provider.title()}")
                else:
                    # No market data available without API keys
                    market_data = {}
                    data_sources_used.append('no_market_data')
                    print("⚠️ No market data available - MLS API key required")
            
            # Step 7.5: Get property photos if available
            media = []
            if property_data and property_data.get('media'):
                # Media already included from RESO search
                media = property_data.get('media', [])
            elif mls_property_id and hasattr(self.primary_mls_client, 'reso_client') and self.primary_mls_client.reso_client:
                # Try to fetch media using RESO client
                try:
                    reso_media = self.primary_mls_client.reso_client.get_media(mls_property_id)
                    if reso_media:
                        media = [{
                            'url': m.get('MediaURL'),
                            'caption': m.get('ShortDescription', ''),
                            'type': m.get('MediaCategory', 'Photo'),
                            'order': m.get('Order', 0)
                        } for m in reso_media if m.get('MediaURL')]
                        data_sources_used.append(f"{self.preferred_mls_provider}_media")
                        print(f"✅ Found {len(media)} photos from {self.preferred_mls_provider}")
                except Exception as e:
                    print(f"⚠️ Could not fetch media: {e}")
            
            # Step 8: Assemble comprehensive result
            result = {
                'address': address,
                'address_components': address_components,
                'location': location_data,
                'property': enhanced_data.get('property', property_data),
                'comparables': comparables,
                'market': market_data,
                'public_records': public_data,
                'scraped_data': enhanced_data.get('scraped_sources', {}),
                'media': media,
                'data_sources_used': list(set(data_sources_used)),  # Remove duplicates
                'data_confidence': self._calculate_data_confidence(data_sources_used, enhanced_data, public_data),
                'county': county,
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
    
    def _calculate_data_confidence(self, data_sources_used: List[str], enhanced_data: Dict, public_data: Dict) -> float:
        """Calculate overall confidence score based on data sources quality"""
        confidence_weights = {
            'bridge_mls': 0.9,
            'mlsgrid_mls': 0.9,
            'estated_mls': 0.7,
            'public_county_assessor': 0.8,
            'public_tax_records': 0.8,
            'public_deed_records': 0.7,
            'public_us_census': 0.6,
            'zillow_simulation': 0.4,
            'redfin_simulation': 0.4,
            'simulated': 0.2
        }
        
        total_weight = 0
        weighted_confidence = 0
        
        for source in data_sources_used:
            # Match source to confidence weight
            for weight_key, weight_value in confidence_weights.items():
                if weight_key in source.lower():
                    total_weight += weight_value
                    weighted_confidence += weight_value
                    break
        
        # Base confidence from enhanced data
        base_confidence = enhanced_data.get('data_confidence', 0.5)
        
        # Boost confidence if we have public records
        if public_data and public_data.get('data_sources'):
            public_source_count = len(public_data['data_sources'])
            public_boost = min(0.2, public_source_count * 0.05)
            base_confidence += public_boost
        
        # Combine weighted confidence with base confidence
        if total_weight > 0:
            final_confidence = (weighted_confidence / max(len(data_sources_used), 1) + base_confidence) / 2
        else:
            final_confidence = base_confidence
        
        return min(1.0, max(0.0, final_confidence))
    
    def _geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates and detailed location info using SearXNG."""
        try:
            # Use general SearXNG for geocoding/location data
            searxng_url = "http://localhost:8888/search"
            params = {
                'q': address,
                'format': 'json',
                'category': 'map', # Or 'general' if 'map' category doesn't yield direct geocoding results
                'safesearch': 0 # Disable safesearch for broader results
            }
            
            response = requests.get(
                searxng_url, 
                params=params,
                timeout=10,
                headers={'User-Agent': 'RealEstateCommandCenter/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                # SearXNG results structure can vary, so we need to parse it carefully
                # Look for a result that contains latitude and longitude
                for result in data.get('results', []):
                    if 'lat' in result and 'lng' in result:
                        return {
                            'lat': float(result['lat']),
                            'lon': float(result['lng']),
                            'display_name': result.get('title', address), # Use title as display name
                            'address_details': {},
                            'importance': result.get('score', 0.5) # Use score as importance
                        }
                    # Fallback for general search results that might contain address info
                    elif 'url' in result and 'title' in result:
                        # Attempt to extract address details from title or URL if it's a map link
                        if "maps.google.com" in result['url'] or "openstreetmap.org" in result['url']:
                            # This is a heuristic, might need more robust parsing
                            return {
                                'lat': 0.0, # Placeholder, actual lat/lon would need parsing from URL or title
                                'lon': 0.0, # Placeholder
                                'display_name': result['title'],
                                'address_details': {},
                                'importance': result.get('score', 0.5)
                            }
            
            return None
            
        except Exception as e:
            print(f"Geocoding error with SearXNG: {e}")
            return None
    
    def search_properties(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced property search using multiple MLS providers and web scraping"""
        try:
            city = criteria.get('city', 'Portland')
            state = criteria.get('state', 'OR')
            all_listings = []
            
            # Try enhanced MLS aggregator first for maximum results
            if self.mls_aggregator:
                aggregated_listings = self.mls_aggregator.search_properties(criteria)
                if aggregated_listings:
                    all_listings.extend(aggregated_listings)
                    providers = set(listing.get('_data_source', 'unknown') for listing in aggregated_listings)
                    print(f"✅ Found {len(aggregated_listings)} listings from MLS aggregator ({', '.join(providers)})")
            
            # Try primary MLS client if aggregator didn't work or for additional results
            if not all_listings:
                primary_listings = self.primary_mls_client.search_properties(criteria)
                if primary_listings:
                    # Add data source metadata
                    for listing in primary_listings:
                        listing['_data_source'] = self.preferred_mls_provider
                    all_listings.extend(primary_listings)
                    print(f"✅ Found {len(primary_listings)} listings from {self.preferred_mls_provider.title()} MLS")
            
            # Fallback to legacy MLS client
            if not all_listings:
                legacy_listings = self.mls_client.search_properties(criteria)
                if legacy_listings:
                    for listing in legacy_listings:
                        listing['_data_source'] = 'legacy_mls'
                    all_listings.extend(legacy_listings)
                    print(f"✅ Found {len(legacy_listings)} listings from legacy MLS")
            
            # Final fallback to web scraping
            if not all_listings:
                print("⚠️ No MLS listings found, falling back to web scraping")
                scraped_listings = self.scraper.search_area_listings(city, state, criteria)
                if scraped_listings:
                    for listing in scraped_listings:
                        listing['_data_source'] = 'web_scraping'
                    all_listings.extend(scraped_listings)
                    print(f"✅ Found {len(scraped_listings)} listings from web scraping")
            
            # Remove duplicates based on address
            unique_listings = []
            seen_addresses = set()
            
            for listing in all_listings:
                address_key = listing.get('address', '').lower().strip()
                if address_key and address_key not in seen_addresses:
                    seen_addresses.add(address_key)
                    unique_listings.append(listing)
            
            if len(unique_listings) != len(all_listings):
                print(f"📊 Removed {len(all_listings) - len(unique_listings)} duplicate listings")
            
            return unique_listings
            
        except Exception as e:
            print(f"Property search error: {e}")
            return []
    
    def get_market_analysis(self, city: str, state: str) -> Dict[str, Any]:
        """Enhanced market analysis using multiple MLS providers and data sources"""
        try:
            market_data = None
            data_sources = []
            
            # Try MLS aggregator first for best market data
            if self.mls_aggregator:
                market_data = self.mls_aggregator.get_best_market_statistics(city, state)
                if market_data:
                    data_source = market_data.get('_data_source', 'aggregator')
                    data_sources.append(f"{data_source}_market")
                    print(f"✅ Found market analysis from MLS aggregator ({data_source})")
            
            # Try primary MLS client
            if not market_data:
                market_data = self.primary_mls_client.get_market_statistics(city, state)
                if market_data and not market_data.get('error'):
                    data_sources.append(f"{self.preferred_mls_provider}_market")
                    print(f"✅ Found market analysis from {self.preferred_mls_provider.title()}")
            
            # Try legacy MLS client
            if not market_data:
                legacy_market_data = self.mls_client.get_market_statistics(city, state)
                if legacy_market_data:
                    market_data = legacy_market_data
                    data_sources.append('legacy_mls_market')
                    print("✅ Found market analysis from legacy MLS")
            
            # Fallback to calculating from listings
            if not market_data:
                print("⚠️ No direct market data available, calculating from listings")
                listings = self.search_properties({'city': city, 'state': state})
                
                if not listings:
                    return {'error': 'No market data available'}
                
                # Calculate market statistics from listings
                prices = []
                days_on_market = []
                property_types = []
                
                for listing in listings:
                    if listing.get('price'):
                        prices.append(listing['price'])
                    if listing.get('days_on_market'):
                        days_on_market.append(listing['days_on_market'])
                    if listing.get('property_type'):
                        property_types.append(listing['property_type'])
                
                if not prices:
                    return {'error': 'No pricing data available for market analysis'}
                
                import statistics
                
                market_data = {
                    'location': f'{city}, {state}',
                    'total_listings': len(listings),
                    'median_price': statistics.median(prices),
                    'average_price': statistics.mean(prices),
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices)
                    },
                    'average_days_on_market': statistics.mean(days_on_market) if days_on_market else 0,
                    'market_activity': 'High' if len(listings) > 20 else 'Moderate' if len(listings) > 10 else 'Low',
                    'property_types': list(set(property_types)),
                    'data_sources': data_sources + ['calculated_from_listings'],
                    'last_updated': datetime.now().isoformat()
                }
                data_sources.append('calculated_from_listings')
            
            # Add data source metadata if not already present
            if market_data and 'data_sources' not in market_data:
                market_data['data_sources'] = data_sources
            
            return market_data
            
        except Exception as e:
            return {'error': f'Market analysis failed: {str(e)}'}
    
    def get_comparable_sales(self, property_id: str, radius_miles: float = 1.0, days_back: int = 180) -> List[Dict[str, Any]]:
        """Get comparable sales for a property"""
        try:
            comparables = []
            
            # Try enhanced MLS aggregator first
            if self.mls_aggregator:
                # First try to get from all providers
                for provider, client in self.mls_aggregator.clients.items():
                    try:
                        provider_comps = client.get_comparable_sales(property_id, radius_miles, days_back)
                        if provider_comps:
                            # Add provider metadata
                            for comp in provider_comps:
                                comp['_data_source'] = provider
                            comparables.extend(provider_comps)
                            print(f"✅ Found {len(provider_comps)} comparables from {provider}")
                    except Exception as e:
                        print(f"⚠️ Failed to get comparables from {provider}: {e}")
            
            # Try primary MLS client if no results
            if not comparables and self.primary_mls_client:
                primary_comps = self.primary_mls_client.get_comparable_sales(property_id, radius_miles, days_back)
                if primary_comps:
                    for comp in primary_comps:
                        comp['_data_source'] = self.preferred_mls_provider
                    comparables.extend(primary_comps)
                    print(f"✅ Found {len(primary_comps)} comparables from {self.preferred_mls_provider}")
            
            # Try legacy MLS as last resort
            if not comparables and self.mls_client:
                legacy_comps = self.mls_client.get_comparable_sales(property_id)
                if legacy_comps:
                    for comp in legacy_comps:
                        comp['_data_source'] = 'legacy_mls'
                    comparables.extend(legacy_comps)
                    print(f"✅ Found {len(legacy_comps)} comparables from legacy MLS")
            
            # Standardize the comparable format for UI
            standardized_comps = []
            for comp in comparables:
                standardized = {
                    'address': comp.get('address', {}).get('unparsed') or comp.get('address') or 'Unknown',
                    'bedrooms': comp.get('property_details', {}).get('bedrooms') or comp.get('bedrooms'),
                    'bathrooms': comp.get('property_details', {}).get('bathrooms_full') or comp.get('bathrooms'),
                    'square_feet': comp.get('property_details', {}).get('square_feet') or comp.get('square_feet'),
                    'sale_price': comp.get('listing_details', {}).get('close_price') or comp.get('sale_price') or comp.get('close_price'),
                    'sale_date': comp.get('listing_details', {}).get('close_date') or comp.get('sale_date') or comp.get('close_date'),
                    'distance_miles': comp.get('distance_miles', 0),
                    'status': comp.get('status') or 'Sold',
                    '_data_source': comp.get('_data_source', 'unknown')
                }
                standardized_comps.append(standardized)
            
            return standardized_comps
            
        except Exception as e:
            print(f"Error getting comparable sales: {e}")
            return []
