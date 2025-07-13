#!/bin/bash
# Quick launch script for development mode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Launching Real Estate Command Center (Development Mode)"
echo "=========================================================="

# Set development environment
export REAL_ESTATE_ENV=development
export REAL_ESTATE_DEBUG=1

# Use system Python
PYTHON_CMD="/usr/bin/python3"

# Check if Docker services are running
if command -v docker >/dev/null 2>&1; then
    if ! docker ps --filter "name=real_estate_db" --format "{{.Status}}" | grep -q "Up"; then
        echo "⚠️  PostgreSQL is not running. Start with: ./scripts/docker-services.sh start"
    fi
    if ! docker ps --filter "name=unicorn-ollama" --format "{{.Status}}" | grep -q "Up"; then
        echo "⚠️  Ollama AI is not running. AI features will be limited."
    fi
fi

# Launch application
cd desktop && $PYTHON_CMD src/main.py