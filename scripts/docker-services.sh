#!/bin/bash
# Docker Services Management Script for Real Estate Command Center

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[X]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to check if services are running
check_services_status() {
    local db_status=$(docker ps --filter "name=real_estate_db" --format "{{.Status}}" 2>/dev/null || echo "Not running")
    local searxng_status=$(docker ps --filter "name=real_estate_searxng" --format "{{.Status}}" 2>/dev/null || echo "Not running")
    
    echo "Service Status:"
    echo "  PostgreSQL: $db_status"
    echo "  SearXNG: $searxng_status"
}

# Function to start services
start_services() {
    print_status "Starting Docker services..."
    
    # Check if docker-compose.yaml exists
    if [ ! -f "docker-compose.yaml" ]; then
        print_error "docker-compose.yaml not found in project root"
        exit 1
    fi
    
    # Start services
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 5
    
    # Check PostgreSQL
    print_status "Checking PostgreSQL connection..."
    for i in {1..30}; do
        if docker exec real_estate_db pg_isready -U realestate &>/dev/null; then
            print_status "PostgreSQL is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Check SearXNG
    print_status "Checking SearXNG..."
    for i in {1..30}; do
        if curl -s http://localhost:8888 > /dev/null; then
            print_status "SearXNG is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    print_status "Docker services started successfully!"
    check_services_status
}

# Function to stop services
stop_services() {
    print_status "Stopping Docker services..."
    docker-compose down
    print_status "Docker services stopped."
}

# Function to restart services
restart_services() {
    stop_services
    start_services
}

# Function to view logs
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to reset database
reset_database() {
    print_warning "This will delete all data in the database. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Resetting database..."
        docker-compose down -v
        docker-compose up -d
        print_status "Database reset complete."
    else
        print_status "Database reset cancelled."
    fi
}

# Function to backup database
backup_database() {
    local backup_dir="$PROJECT_ROOT/backups"
    mkdir -p "$backup_dir"
    local backup_file="$backup_dir/realestate_db_$(date +%Y%m%d_%H%M%S).sql"
    
    print_status "Creating database backup..."
    docker exec real_estate_db pg_dump -U realestate realestate_db > "$backup_file"
    print_status "Database backed up to: $backup_file"
}

# Main menu
show_menu() {
    echo ""
    echo "Real Estate Command Center - Docker Services Manager"
    echo "==================================================="
    echo "1. Start services"
    echo "2. Stop services"
    echo "3. Restart services"
    echo "4. Check status"
    echo "5. View logs (all services)"
    echo "6. View PostgreSQL logs"
    echo "7. View SearXNG logs"
    echo "8. Backup database"
    echo "9. Reset database (WARNING: Deletes all data)"
    echo "0. Exit"
    echo ""
}

# Check Docker installation
check_docker

# Process command line arguments
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Select an option: " choice
        
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3) restart_services ;;
            4) check_services_status ;;
            5) view_logs ;;
            6) view_logs db ;;
            7) view_logs searxng ;;
            8) backup_database ;;
            9) reset_database ;;
            0) exit 0 ;;
            *) print_error "Invalid option" ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
else
    # Command mode
    case $1 in
        start) start_services ;;
        stop) stop_services ;;
        restart) restart_services ;;
        status) check_services_status ;;
        logs) view_logs $2 ;;
        backup) backup_database ;;
        reset) reset_database ;;
        *) 
            echo "Usage: $0 {start|stop|restart|status|logs|backup|reset}"
            echo "   or run without arguments for interactive mode"
            exit 1 
            ;;
    esac
fi