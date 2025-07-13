#!/bin/bash
# Launch script for Real Estate Command Center
# Automatically detects environment and starts with appropriate settings

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    # Check for virtual environment first
    if [[ -f "$SCRIPT_DIR/venv/bin/python" ]]; then
        PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
        print_status "Using virtual environment Python: $PYTHON_CMD"
    elif [[ -f "/usr/bin/python3" ]]; then
        PYTHON_CMD="/usr/bin/python3"
        print_status "Using system Python: $PYTHON_CMD"
    else
        print_error "Python not found"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Python version: $PYTHON_VERSION"
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check required Python packages
    MISSING_PACKAGES=""
    
    # Check packages with special import names
    if ! $PYTHON_CMD -c "from bs4 import BeautifulSoup" 2>/dev/null; then
        MISSING_PACKAGES="$MISSING_PACKAGES beautifulsoup4"
    fi
    
    # Check other packages
    for package in PySide6 requests psycopg2; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            MISSING_PACKAGES="$MISSING_PACKAGES $package"
        fi
    done
    
    if [[ -n "$MISSING_PACKAGES" ]]; then
        print_warning "Missing Python packages:$MISSING_PACKAGES"
        print_info "Install with: sudo $PYTHON_CMD -m pip install$MISSING_PACKAGES --break-system-packages"
        return 1
    else
        print_status "All Python dependencies installed"
        return 0
    fi
}

# Function to check Docker services
check_docker_services() {
    if command_exists docker; then
        print_info "Checking Docker services..."
        
        # Check PostgreSQL
        if docker ps --filter "name=real_estate_db" --format "{{.Status}}" | grep -q "Up"; then
            print_status "PostgreSQL is running"
        else
            print_warning "PostgreSQL is not running"
            echo -n "Would you like to start Docker services? (y/N): "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                ./scripts/docker-services.sh start
            fi
        fi
        
        # Check SearXNG
        if docker ps --filter "name=real_estate_searxng" --format "{{.Status}}" | grep -q "Up"; then
            print_status "SearXNG is running"
        else
            print_warning "SearXNG is not running"
        fi
    else
        print_warning "Docker not installed - some features may be limited"
    fi
}

# Function to check Ollama
check_ollama() {
    if docker ps --filter "name=unicorn-ollama" --format "{{.Status}}" | grep -q "Up"; then
        print_status "Ollama AI service is running"
    else
        print_warning "Ollama AI service is not running - AI features will be limited"
    fi
}

# Function to launch application
launch_app() {
    local mode=$1
    
    print_info "Launching Real Estate Command Center in $mode mode..."
    
    # Set environment variables
    export REAL_ESTATE_ENV=$mode
    
    # Launch based on mode
    case $mode in
        development)
            export REAL_ESTATE_DEBUG=1
            cd desktop && $PYTHON_CMD src/main.py
            ;;
        production)
            export REAL_ESTATE_DEBUG=0
            cd desktop && $PYTHON_CMD src/main.py
            ;;
        demo)
            export REAL_ESTATE_DEBUG=0
            export REAL_ESTATE_DEMO_MODE=1
            cd desktop && $PYTHON_CMD src/main.py
            ;;
        *)
            print_error "Unknown mode: $mode"
            exit 1
            ;;
    esac
}

# Main script
echo "========================================"
echo "  Real Estate Command Center Launcher"
echo "========================================"
echo

# Check Python
check_python

# Check dependencies
if ! check_dependencies; then
    echo
    echo -n "Continue anyway? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check services
check_docker_services
check_ollama

echo
echo "Select launch mode:"
echo "1) Development (debug enabled)"
echo "2) Production (optimized)"
echo "3) Demo (sample data mode)"
echo "4) Exit"
echo

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        launch_app "development"
        ;;
    2)
        launch_app "production"
        ;;
    3)
        launch_app "demo"
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac