#!/bin/bash
# Production launch script with all services check

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🏢 Launching Real Estate Command Center (Production Mode)"
echo "========================================================"

# Function to check service
check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --filter "name=$container_name" --format "{{.Status}}" | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} $service_name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is not running"
        return 1
    fi
}

# Check all required services
echo
echo "Checking required services..."
SERVICES_OK=true

if ! check_service "PostgreSQL" "real_estate_db"; then
    SERVICES_OK=false
fi

if ! check_service "SearXNG" "real_estate_searxng"; then
    SERVICES_OK=false
fi

if ! check_service "Ollama AI" "unicorn-ollama"; then
    echo "  ⚠️  AI features will be limited without Ollama"
fi

# If services not running, offer to start them
if [ "$SERVICES_OK" = false ]; then
    echo
    echo "Some required services are not running."
    echo -n "Would you like to start Docker services? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        ./scripts/docker-services.sh start
        echo
        echo "Waiting for services to be ready..."
        sleep 5
    else
        echo "⚠️  Warning: Application may not function properly without all services"
    fi
fi

# Set production environment
export REAL_ESTATE_ENV=production
export REAL_ESTATE_DEBUG=0

# Launch application
echo
echo "Starting application..."
cd desktop && /usr/bin/python3 src/main.py