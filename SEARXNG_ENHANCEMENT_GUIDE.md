# SearXNG Real Estate Enhancement Guide

## Overview

This guide details how to transform the current SearXNG instance into a "real estate powerhouse" by implementing custom search engines, enabling proxy integration, and optimizing configurations for property data aggregation.

## Current Status Assessment

### ✅ Infrastructure Ready
- **Docker Integration**: SearXNG containerized in `docker-compose.yaml`
- **BrightData Proxy**: Configuration exists but disabled in `.env` file
- **Settings Framework**: Basic `settings.yml` structure in place
- **API Access**: Accessible on port 8888 for programmatic queries

### ❌ Missing Real Estate Features
- **Custom Engines**: No specialized real estate search engines implemented
- **Site-Specific Scrapers**: Only generic engines with `site:` queries
- **Proxy Rotation**: BrightData integration commented out
- **Rate Limiting**: No specialized handling for real estate sites

## Enhancement Roadmap

### Phase 1: Enable BrightData Proxy Integration

**Current Configuration** (in `searxng/old-core-searxng)/.env`):
```bash
USE_ROTATING_PROXY=false
# BRIGHTDATA_USERNAME='username goes here'
# BRIGHTDATA_PASSWORD=password
# BRIGHTDATA_GATEWAY=brd.superproxy.io
# BRIGHTDATA_PORT=33335
```

**To Enable**:
1. Uncomment and configure BrightData credentials
2. Set `USE_ROTATING_PROXY=true`
3. Update SearXNG settings to use proxy rotation

### Phase 2: Custom Real Estate Search Engines

#### Zillow Engine
Create dedicated engine for Zillow property searches:
```yaml
- name: zillow
  engine: xpath
  search_url: https://www.zillow.com/homes/for_sale/{query}
  url_xpath: //a[@data-test="property-card-link"]/@href
  title_xpath: //span[@data-test="property-card-addr"]
  content_xpath: //div[@data-test="property-card-details"]
  categories: real_estate
```

#### Redfin Engine
```yaml
- name: redfin
  engine: xpath
  search_url: https://www.redfin.com/city/{query}
  url_xpath: //a[contains(@class, "homecard")]/@href
  title_xpath: //div[@data-rf-test-id="titleSection"]
  content_xpath: //div[contains(@class, "stats")]
  categories: real_estate
```

#### Realtor.com Engine
```yaml
- name: realtor
  engine: xpath
  search_url: https://www.realtor.com/realestateandhomes-search/{query}
  url_xpath: //a[@data-testid="property-anchor"]/@href
  title_xpath: //div[@data-testid="card-address"]
  content_xpath: //div[@data-testid="card-price"]
  categories: real_estate
```

### Phase 3: County Assessor Integration

#### Generic County Assessor Engine
```yaml
- name: county_assessor
  engine: xpath
  search_url: https://www.google.com/search?q=site:{county}.gov+assessor+property+{query}
  url_xpath: //a/@href
  title_xpath: //h3
  content_xpath: //span
  categories: government
```

### Phase 4: MLS Provider Engines

#### MLS Grid Integration
```yaml
- name: mls_grid
  engine: json
  search_url: https://api.mlsgrid.com/v2/Property/Search
  headers:
    Authorization: Bearer {api_key}
  categories: mls
```

### Phase 5: Advanced Features

#### Rate Limiting Configuration
```yaml
engines:
  - name: zillow
    request_timeout: 10.0
    max_request_timeout: 15.0
    retry_on_http_error: [429, 503]
    categories: real_estate
```

#### User Agent Rotation
```yaml
outgoing:
  useragent_suffix: "RealEstateBot/1.0"
  pool_connections: 100
  pool_maxsize: 10
  enable_http2: true
```

## Implementation Guide

### Step 1: Enable BrightData Proxy

1. **Get BrightData Credentials**:
   - Sign up at brightdata.com
   - Create proxy endpoint
   - Note username, password, gateway, port

2. **Update Environment**:
   ```bash
   cd /home/ucadmin/Development/real-estate-command-center
   
   # Edit searxng/old-core-searxng)/.env
   USE_ROTATING_PROXY=true
   BRIGHTDATA_USERNAME='your-username'
   BRIGHTDATA_PASSWORD='your-password'
   BRIGHTDATA_GATEWAY=brd.superproxy.io
   BRIGHTDATA_PORT=33335
   ```

3. **Update SearXNG Settings**:
   Add to `searxng/settings.yml`:
   ```yaml
   outgoing:
     proxies:
       http: http://your-username:your-password@brd.superproxy.io:33335
       https: http://your-username:your-password@brd.superproxy.io:33335
   ```

### Step 2: Add Custom Real Estate Engines

1. **Create Enhanced Settings File**:
   ```bash
   cp searxng/settings.yml searxng/settings_enhanced.yml
   ```

2. **Add Real Estate Engines**:
   Edit `searxng/settings_enhanced.yml` and add engines section:
   ```yaml
   engines:
     # Existing engines...
     
     # Real Estate Engines
     - name: zillow_properties
       engine: xpath
       search_url: https://www.zillow.com/homes/for_sale/{query}
       url_xpath: //a[@data-test="property-card-link"]/@href
       title_xpath: //span[@data-test="property-card-addr"]
       content_xpath: //div[@data-test="property-card-details"]
       categories: [real_estate]
       shortcut: zil
       timeout: 10.0
       
     - name: redfin_properties
       engine: xpath
       search_url: https://www.redfin.com/city/{query}
       url_xpath: //a[contains(@class, "homecard")]/@href
       title_xpath: //div[@data-rf-test-id="titleSection"]
       content_xpath: //div[contains(@class, "stats")]
       categories: [real_estate]
       shortcut: red
       timeout: 10.0
   ```

3. **Add Real Estate Category**:
   ```yaml
   categories_as_tabs:
     general:
       real_estate: Real Estate
   ```

### Step 3: Configure Docker Integration

1. **Update docker-compose.yaml**:
   ```yaml
   searxng:
     image: searxng/searxng:latest
     container_name: real_estate_searxng
     restart: always
     ports:
       - "8888:8080"
     volumes:
       - ./searxng/settings_enhanced.yml:/etc/searxng/settings.yml
     environment:
       SEARXNG_SETTINGS_PATH: /etc/searxng/settings.yml
       USE_ROTATING_PROXY: "${USE_ROTATING_PROXY:-false}"
       BRIGHTDATA_USERNAME: "${BRIGHTDATA_USERNAME}"
       BRIGHTDATA_PASSWORD: "${BRIGHTDATA_PASSWORD}"
   ```

### Step 4: Test Enhanced Configuration

1. **Restart SearXNG**:
   ```bash
   cd /home/ucadmin/Development/real-estate-command-center
   docker-compose restart searxng
   ```

2. **Test Real Estate Searches**:
   ```bash
   # Test via API
   curl "http://localhost:8888/search?q=houses+Portland+OR&categories=real_estate"
   
   # Test specific engines
   curl "http://localhost:8888/search?q=3+bedroom+Seattle&engines=zillow_properties"
   ```

3. **Verify Proxy Usage**:
   ```bash
   # Check SearXNG logs for proxy connections
   docker logs real_estate_searxng | grep -i proxy
   ```

## Integration with Real Estate Commander

### Update Property Service

Modify `desktop/src/core/property_service.py` to use enhanced SearXNG:

```python
class PropertyService:
    def __init__(self):
        self.searxng_url = "http://localhost:8888"
    
    def search_properties(self, query, location=None):
        """Search properties using enhanced SearXNG."""
        params = {
            'q': f"{query} {location}" if location else query,
            'categories': 'real_estate',
            'format': 'json'
        }
        
        response = requests.get(f"{self.searxng_url}/search", params=params)
        return response.json()
    
    def search_specific_engine(self, query, engine='zillow_properties'):
        """Search using specific real estate engine."""
        params = {
            'q': query,
            'engines': engine,
            'format': 'json'
        }
        
        response = requests.get(f"{self.searxng_url}/search", params=params)
        return response.json()
```

## Expected Benefits

### Data Quality Improvements
- **Direct Source Access**: Bypass generic search results
- **Structured Data**: XPath extraction provides consistent formatting
- **Rate Limiting**: Respectful scraping prevents IP blocks
- **Proxy Rotation**: BrightData ensures reliable access

### Performance Enhancements
- **Targeted Searches**: Real estate-specific engines reduce noise
- **Parallel Queries**: Multiple engines simultaneously
- **Caching**: SearXNG caches results for faster repeat queries
- **Load Balancing**: Proxy rotation distributes requests

### Compliance Benefits
- **Respectful Scraping**: Built-in delays and user agent rotation
- **ToS Compliance**: Follows robots.txt and rate limits
- **IP Protection**: Proxy usage prevents direct blocking
- **Error Handling**: Graceful failures with retry logic

## Cost Analysis

### BrightData Proxy Costs
- **Residential IPs**: ~$8.40/GB for US residential
- **Datacenter IPs**: ~$0.60/GB for datacenter proxies
- **Monthly Minimum**: Typically $500/month for professional plans

### Alternative Proxy Services
- **Oxylabs**: Similar pricing to BrightData
- **SmartProxy**: ~$50/month for 5GB residential
- **ProxyMesh**: ~$10/month for 10GB datacenter

### Free Alternatives
- **Tor Network**: Built-in SearXNG support (slower, less reliable)
- **Free Proxy Lists**: Unreliable, often blocked
- **Rate Limiting Only**: No proxy, just respectful delays

## Monitoring and Maintenance

### Health Checks
```bash
# Monitor SearXNG status
curl http://localhost:8888/stats

# Check engine status
curl http://localhost:8888/config

# Monitor proxy usage (if BrightData enabled)
curl http://localhost:8888/stats/engines
```

### Log Analysis
```bash
# Watch SearXNG logs
docker logs -f real_estate_searxng

# Filter for errors
docker logs real_estate_searxng | grep -i error

# Monitor proxy connections
docker logs real_estate_searxng | grep -i proxy
```

### Performance Optimization
- **Engine Timeout Tuning**: Adjust timeouts based on site response times
- **Request Throttling**: Implement delays between requests
- **Cache Configuration**: Optimize Redis caching for frequent queries
- **Engine Selection**: Disable underperforming or blocked engines

## Security Considerations

### API Key Protection
- Store BrightData credentials in `.env` files (not committed to git)
- Use environment variable substitution in docker-compose
- Rotate proxy credentials regularly

### Access Control
- Configure SearXNG to only accept local connections
- Implement authentication if exposing externally
- Use firewall rules to restrict access

### Data Privacy
- Configure SearXNG to not log sensitive queries
- Implement query sanitization
- Use HTTPS for all external connections

## Next Steps

1. **Choose proxy solution** (BrightData, alternatives, or rate-limiting only)
2. **Implement Phase 1** (proxy integration)
3. **Test basic functionality** with existing engines
4. **Add custom real estate engines** (Phase 2)
5. **Integrate with desktop application**
6. **Monitor performance and adjust**

This enhancement transforms SearXNG from a generic search interface into a specialized real estate data aggregation powerhouse, providing the Real Estate Commander with robust, reliable property data sources.