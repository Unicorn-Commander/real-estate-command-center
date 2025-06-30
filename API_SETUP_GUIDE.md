# Real Estate Command Center - API Setup Guide

This guide explains how to configure API keys and environment variables for the enhanced Real Estate Command Center with multiple MLS providers and public data sources.

## 🎯 Quick Start Summary

The application now supports **5 MLS providers** plus **public data scraping**:

### **Free/Low-Cost Options** ✅
- **Bridge Interactive**: Free (requires MLS approval)
- **Estated Public Records**: Free tier available
- **Public Data Scraping**: Government records (free)

### **Paid Options** 💰
- **MLS Grid**: RESO compliant, varies by MLS
- **RentSpree**: Rental-focused API
- **ATTOM Data**: Comprehensive property data

---

## 📋 Environment Variables Setup

Create a `.env` file in the project root with your API keys:

```bash
# Create .env file
cd /home/ucadmin/Development/real-estate-command-center
nano .env
```

### **Environment Variables Template**

```bash
# ===== MLS API KEYS =====

# Bridge Interactive (FREE - requires MLS approval)
BRIDGE_API_KEY=your_bridge_api_key_here

# MLS Grid (RESO compliant)
MLSGRID_API_KEY=your_mlsgrid_api_key_here

# RentSpree (rental-focused)
RENTSPREE_API_KEY=your_rentspree_api_key_here

# Estated Public Records (FREE tier available)
ESTATED_API_KEY=your_estated_api_key_here

# ATTOM Data (comprehensive property data)
ATTOM_API_KEY=your_attom_api_key_here

# ===== BACKUP/LEGACY =====
MLS_API_KEY=your_backup_mls_key_here
```

### **Load Environment Variables**

Add to your shell profile (`.bashrc` or `.zshrc`):

```bash
# Add to ~/.bashrc
echo 'set -a; source /home/ucadmin/Development/real-estate-command-center/.env; set +a' >> ~/.bashrc
source ~/.bashrc
```

---

## 🔧 Provider-Specific Setup Instructions

### 1. **Bridge Interactive** (Recommended - FREE)

**Cost**: FREE (requires MLS approval)  
**Best for**: Full MLS access, RESO compliant

**Setup Steps**:
1. Contact your local MLS organization
2. Request Bridge Interactive API access
3. Complete MLS approval process
4. Receive API key and base URL
5. Set environment variable:
   ```bash
   export BRIDGE_API_KEY="your_bridge_key_here"
   ```

**Documentation**: [Bridge Interactive Developers](https://www.bridgeinteractive.com/developers/bridge-api/)

### 2. **Estated Public Records** (Recommended - FREE TIER)

**Cost**: FREE tier available  
**Best for**: Property details, ownership records

**Setup Steps**:
1. Visit [Estated.com](https://estated.com/property-data-api)
2. Sign up for free API key
3. Verify email and complete profile
4. Get API key from dashboard
5. Set environment variable:
   ```bash
   export ESTATED_API_KEY="your_estated_key_here"
   ```

**Free Tier Limits**: 1,000 requests/month

### 3. **MLS Grid** (RESO Compliant)

**Cost**: Varies by MLS ($20-50/month typically)  
**Best for**: RESO standard compliance

**Setup Steps**:
1. Visit [MLSGrid.com](https://www.mlsgrid.com/)
2. Contact for pricing and availability
3. Complete MLS verification
4. Receive API credentials
5. Set environment variable:
   ```bash
   export MLSGRID_API_KEY="your_mlsgrid_key_here"
   ```

### 4. **RentSpree** (Rental Focus)

**Cost**: Varies  
**Best for**: Rental properties, tenant screening

**Setup Steps**:
1. Visit [RentSpree API](https://api.rentspree.com/)
2. Request access through MLS benefits
3. Complete integration setup
4. Set environment variable:
   ```bash
   export RENTSPREE_API_KEY="your_rentspree_key_here"
   ```

### 5. **ATTOM Data** (Comprehensive)

**Cost**: $$$$ (Enterprise pricing)  
**Best for**: Comprehensive property analytics

**Setup Steps**:
1. Visit [ATTOM Data](https://www.attomdata.com/solutions/property-data-api/)
2. Contact sales for pricing
3. Complete enterprise setup
4. Set environment variable:
   ```bash
   export ATTOM_API_KEY="your_attom_key_here"
   ```

---

## 🚀 Application Configuration

### **Choose Your Provider Strategy**

The application supports three configuration modes:

#### **1. Single Provider** (Simple)
```python
# In your code or config
property_service = PropertyService(
    preferred_mls_provider='bridge',
    use_multiple_providers=False
)
```

#### **2. Multiple Providers** (Recommended)
```python
# Uses aggregator for redundancy
property_service = PropertyService(
    preferred_mls_provider='bridge',
    use_multiple_providers=True  # Default
)
```

#### **3. Custom Provider List**
```python
# Direct aggregator use
from core.mls_client_enhanced import MLSAggregator
aggregator = MLSAggregator(['bridge', 'estated', 'mlsgrid'])
```

### **Test Your Setup**

Run the connection test:

```python
from core.mls_client_enhanced import create_mls_client

# Test individual providers
bridge_client = create_mls_client('bridge')
status = bridge_client.test_connection()
print(f"Bridge Status: {status}")

estated_client = create_mls_client('estated')
status = estated_client.test_connection()
print(f"Estated Status: {status}")
```

---

## 📊 Cost Comparison & Recommendations

| Provider | Cost | Data Quality | Setup Difficulty | Recommendation |
|----------|------|--------------|------------------|----------------|
| **Bridge Interactive** | FREE | ⭐⭐⭐⭐⭐ | Medium (MLS approval) | ✅ **Primary choice** |
| **Estated** | FREE tier | ⭐⭐⭐⭐ | Easy | ✅ **Backup/supplement** |
| **Public Records** | FREE | ⭐⭐⭐ | Easy | ✅ **Always use** |
| **MLS Grid** | $20-50/mo | ⭐⭐⭐⭐⭐ | Medium | 💡 If budget allows |
| **RentSpree** | Varies | ⭐⭐⭐ | Medium | 💡 For rentals |
| **ATTOM Data** | $$$$ | ⭐⭐⭐⭐⭐ | Hard | 💰 Enterprise only |

### **Recommended Setup for Different Use Cases**

#### **🏠 Individual Agent (Budget-Conscious)**
```bash
# FREE setup
BRIDGE_API_KEY=your_bridge_key  # Contact local MLS
ESTATED_API_KEY=your_estated_key  # Free tier
# + Public records scraping (always free)
```

#### **🏢 Small Brokerage**
```bash
# Budget-friendly with premium backup
BRIDGE_API_KEY=your_bridge_key
ESTATED_API_KEY=your_estated_key  
MLSGRID_API_KEY=your_mlsgrid_key  # $20-50/month
```

#### **🏭 Enterprise**
```bash
# All providers for maximum coverage
BRIDGE_API_KEY=your_bridge_key
MLSGRID_API_KEY=your_mlsgrid_key
ATTOM_API_KEY=your_attom_key
ESTATED_API_KEY=your_estated_key
RENTSPREE_API_KEY=your_rentspree_key
```

---

## 🔒 Legal & Compliance Notes

### **What's Legal to Scrape**
✅ **Always Legal**:
- Government property records
- County assessor data
- Public tax records
- Deed/transfer records
- US Census data

⚠️ **Requires Permission**:
- MLS data (need API access)
- Private database content
- Copyrighted information

❌ **Avoid**:
- Zillow/Redfin direct scraping
- Private user data
- Copyrighted content

### **Best Practices**
- Always check `robots.txt`
- Implement rate limiting
- Use proper User-Agent headers
- Respect Terms of Service
- Get legal advice for commercial use

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **"No API key" warnings**
```bash
# Check environment variables are loaded
echo $BRIDGE_API_KEY
echo $ESTATED_API_KEY

# Reload environment
source ~/.bashrc
```

#### **Connection failures**
```bash
# Test basic connectivity
curl -H "Authorization: Bearer $BRIDGE_API_KEY" \
     https://api.bridgeinteractive.com/v2/Property

# Check API key validity in application
cd desktop && /usr/bin/python3 -c "
from core.mls_client_enhanced import create_mls_client
client = create_mls_client('bridge')
print(client.test_connection())
"
```

#### **Rate limiting errors**
- Bridge Interactive: 1 request/second
- Estated: 1 request/second  
- MLS Grid: 1 request/second

**Solution**: Application automatically handles rate limiting

### **Application Startup**

When you launch the application, you should see:
```bash
cd /home/ucadmin/Development/real-estate-command-center/desktop
/usr/bin/python3 src/main.py

# Expected output:
✅ Bridge Interactive connected successfully
⚠️ MLS Grid: No API key configured
✅ Estated Public Records connected successfully
📊 MLS Aggregator: 2/3 providers connected
```

---

## 📝 Environment Variable Reference

### **Complete .env Template**

```bash
# ===============================================
# Real Estate Command Center - API Configuration
# ===============================================

# ===== PRIMARY MLS PROVIDERS =====

# Bridge Interactive (FREE - requires MLS approval)
# Contact your local MLS for access
BRIDGE_API_KEY=

# MLS Grid (RESO compliant, ~$20-50/month)
# Visit: https://www.mlsgrid.com/
MLSGRID_API_KEY=

# ===== PROPERTY DATA PROVIDERS =====

# Estated Public Records (FREE tier: 1k requests/month)
# Visit: https://estated.com/property-data-api
ESTATED_API_KEY=

# ATTOM Data (Enterprise pricing)
# Visit: https://www.attomdata.com/
ATTOM_API_KEY=

# ===== RENTAL-FOCUSED PROVIDERS =====

# RentSpree (varies by MLS benefits)
# Contact through your MLS
RENTSPREE_API_KEY=

# ===== BACKUP/LEGACY =====

# Generic MLS key for backward compatibility
MLS_API_KEY=

# ===== APPLICATION SETTINGS =====

# Preferred primary provider (default: bridge)
MLS_PRIMARY_PROVIDER=bridge

# Enable multiple provider aggregation (default: true)
MLS_USE_AGGREGATOR=true

# Rate limiting (requests per second)
MLS_RATE_LIMIT=1

# ===== DEVELOPMENT/TESTING =====

# Set to 'true' to enable mock data when no API keys
USE_MOCK_DATA=false

# Log level for MLS operations
MLS_LOG_LEVEL=INFO
```

Save this as `.env` in your project root and fill in the API keys you obtain.

---

## 🎯 Next Steps

1. **Start with FREE options**: Bridge Interactive + Estated + Public Records
2. **Test the integration**: Run property lookups to verify data flow
3. **Monitor usage**: Check API request limits and performance
4. **Expand gradually**: Add paid providers as needed
5. **Optimize**: Fine-tune provider priority based on data quality

Your enhanced Real Estate Command Center is now ready for production use with multiple data sources! 🚀