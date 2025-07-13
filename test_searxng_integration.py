#!/usr/bin/env python3
"""Test script to verify SearXNG integration with Real Estate Command Center"""

import requests
import json
import sys

def test_searxng_instance(url, name, test_query):
    """Test a SearXNG instance"""
    print(f"\n=== Testing {name} at {url} ===")
    try:
        params = {
            'q': test_query,
            'format': 'json',
            'safesearch': 0
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Connection successful")
        print(f"✓ Number of results: {len(data.get('results', []))}")
        
        # Show first 3 results
        for i, result in enumerate(data.get('results', [])[:3]):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Engine: {result.get('engine', 'N/A')}")
            
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_property_scraper_integration():
    """Test PropertyScraper with both SearXNG instances"""
    print("\n=== Testing PropertyScraper Integration ===")
    try:
        sys.path.insert(0, '/home/ucadmin/Development/real-estate-command-center/desktop')
        from src.core.property_scraper import PropertyScraper
        
        scraper = PropertyScraper()
        print(f"✓ PropertyScraper initialized")
        print(f"  Real Estate URL: {scraper.searxng_real_estate_url}")
        print(f"  General URL: {scraper.searxng_general_url}")
        
        # Test real estate search
        print("\nTesting real estate property search...")
        result = scraper._search_with_searxng("123 main street portland", "zillow.com", use_real_estate=True)
        if result:
            print(f"✓ Real estate search returned: {result}")
        else:
            print("✗ No results from real estate search")
            
        # Test general search
        print("\nTesting general web search...")
        result = scraper._search_with_searxng("property tax records portland", "portland.gov", use_real_estate=False)
        if result:
            print(f"✓ General search returned: {result}")
        else:
            print("✗ No results from general search")
            
        return True
    except Exception as e:
        print(f"✗ PropertyScraper test failed: {e}")
        return False

def main():
    print("SearXNG Integration Test for Real Estate Command Center")
    print("=" * 60)
    
    # Test both SearXNG instances
    real_estate_ok = test_searxng_instance(
        "http://localhost:18888/search",
        "SearXNG-Real-Estate",
        "houses for sale portland oregon"
    )
    
    general_ok = test_searxng_instance(
        "http://localhost:8888/search", 
        "General SearXNG",
        "portland property tax records"
    )
    
    # Test PropertyScraper integration
    scraper_ok = test_property_scraper_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  SearXNG-Real-Estate (port 18888): {'✓ OK' if real_estate_ok else '✗ FAILED'}")
    print(f"  General SearXNG (port 8888): {'✓ OK' if general_ok else '✗ FAILED'}")
    print(f"  PropertyScraper Integration: {'✓ OK' if scraper_ok else '✗ FAILED'}")
    
    if real_estate_ok and general_ok and scraper_ok:
        print("\n✓ All tests passed! Integration is working correctly.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()