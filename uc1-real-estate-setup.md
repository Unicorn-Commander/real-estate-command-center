# UC-1 Real Estate Commander - Development Setup Guide

## Project Structure

```bash
uc1-real-estate-commander/
├── backend/
│   ├── the_colonel/          # Your forked The_Colonel
│   ├── api/                  # FastAPI extensions
│   │   ├── __init__.py
│   │   ├── main.py          # Main API server
│   │   ├── routers/
│   │   │   ├── cma.py       # CMA generation endpoints
│   │   │   ├── properties.py # Property search
│   │   │   └── leads.py     # Lead management
│   │   └── services/
│   │       ├── llm.py       # Ollama integration
│   │       ├── voice.py     # Whisper/Kokoro
│   │       └── scraper.py   # Property data scraping
│   └── docker-compose.yml    # All backend services
│
├── desktop/                  # KDE Desktop Application
│   ├── src/
│   │   ├── main.py          # Application entry point
│   │   ├── ui/
│   │   │   ├── main_window.py
│   │   │   ├── cma_wizard.py
│   │   │   └── widgets/
│   │   ├── core/
│   │   │   ├── colonel_client.py  # The_Colonel API client
│   │   │   ├── voice_assistant.py
│   │   │   └── property_manager.py
│   │   └── kde/
│   │       ├── plasma_integration.py
│   │       ├── krunner_plugin.py
│   │       └── activities.py
│   ├── resources/
│   │   ├── ui/              # Qt Designer files
│   │   ├── icons/
│   │   └── templates/       # Report templates
│   └── pyproject.toml
│
├── shared/                   # Shared libraries
│   ├── models/              # SQLAlchemy models
│   ├── prompts/             # AI prompts
│   └── utils/
│
└── scripts/
    ├── setup.sh             # One-click installer
    └── dev-setup.sh         # Developer environment
```

## Initial Setup Script

```bash
#!/bin/bash
# dev-setup.sh - Complete development environment setup

echo "🦄 Setting up UC-1 Real Estate Commander Development Environment"

# 1. Clone The Colonel
echo "📥 Cloning The_Colonel..."
git clone https://github.com/Unicorn-Commander/The_Colonel.git backend/the_colonel
cd backend/the_colonel
pip install -e .
cd ../..

# 2. Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install desktop dependencies
echo "📦 Installing desktop dependencies..."
pip install pyside6 aiohttp asyncio watchdog
pip install python-dotenv sqlalchemy psycopg2-binary
pip install redis chromadb qdrant-client
pip install reportlab pillow matplotlib

# 4. Install KDE development packages
echo "🎨 Installing KDE development packages..."
sudo apt update
sudo apt install -y \
    python3-pyside6.qtcore \
    python3-pyside6.qtwidgets \
    python3-pyside6.qtmultimedia \
    kde-frameworks-5-dev \
    libkf5notifications-dev \
    libkf5config-dev

# 5. Setup Docker services
echo "🐳 Setting up Docker services..."
cd backend
docker-compose up -d
cd ..

# 6. Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

echo "✅ Development environment ready!"
echo "Run: source venv/bin/activate && python desktop/src/main.py"
```

## Backend Docker Compose

```yaml
# backend/docker-compose.yml
version: '3.8'

services:
  # The Colonel API Server
  the_colonel:
    build: ./the_colonel
    container_name: uc1-colonel
    ports:
      - "8264:8264"
    volumes:
      - ./the_colonel/profiles:/app/profiles
      - ~/.local/share/uc1-commander:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - uc1-network

  # Your existing services from main docker-compose
  ollama:
    extends:
      file: ../../docker-compose.yml
      service: ollama
    networks:
      - uc1-network

  postgresql:
    extends:
      file: ../../docker-compose.yml
      service: postgresql
    networks:
      - uc1-network

  redis:
    extends:
      file: ../../docker-compose.yml
      service: redis
    networks:
      - uc1-network

  qdrant:
    extends:
      file: ../../docker-compose.yml
      service: qdrant
    networks:
      - uc1-network

networks:
  uc1-network:
    driver: bridge
```

## Core Application (main.py)

```python
#!/usr/bin/env python3
"""
UC-1 Real Estate Commander - Main Application
"""
import sys
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from ui.main_window import MainWindow
from core.colonel_client import ColonelClient
from kde.plasma_integration import PlasmaIntegration

class RealEstateCommander(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application metadata
        self.setApplicationName("UC-1 Real Estate Commander")
        self.setOrganizationName("Unicorn Commander")
        self.setApplicationDisplayName("Real Estate Commander")
        
        # Initialize The Colonel client
        self.colonel = ColonelClient("http://localhost:8264")
        
        # Initialize KDE integration
        self.plasma = PlasmaIntegration(self)
        
        # Create main window
        self.main_window = MainWindow(self.colonel)
        
        # Setup global shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Setup KDE global shortcuts"""
        # Alt+C for new CMA
        self.plasma.register_global_shortcut(
            "Alt+C", 
            self.main_window.new_cma_voice
        )
        
        # Alt+R for voice command
        self.plasma.register_global_shortcut(
            "Alt+R",
            self.main_window.activate_voice
        )

if __name__ == "__main__":
    app = RealEstateCommander(sys.argv)
    app.main_window.show()
    sys.exit(app.exec())
```

## The Colonel Client

```python
# desktop/src/core/colonel_client.py
import aiohttp
import asyncio
from typing import Dict, Any, Optional

class ColonelClient:
    """Client for The_Colonel API server"""
    
    def __init__(self, base_url: str = "http://localhost:8264"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code via The Colonel"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tools/execute/python",
                json={"code": code}
            ) as resp:
                return await resp.json()
    
    async def execute_shell(self, command: str) -> Dict[str, Any]:
        """Execute shell command via The Colonel"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tools/execute/shell",
                json={"command": command}
            ) as resp:
                return await resp.json()
    
    async def chat(self, messages: list, profile: str = "real-estate") -> str:
        """Chat with The Colonel using a specific profile"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                params={"profile": profile},
                json={
                    "model": "the-colonel",
                    "messages": messages,
                    "stream": False
                }
            ) as resp:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
    
    async def analyze_property(self, address: str) -> Dict[str, Any]:
        """Use The Colonel to analyze a property"""
        code = f"""
import requests
import json

# Scrape property data
address = "{address}"
# Add your property scraping logic here

# Analyze with local LLM
# Return structured data
result = {{
    "address": address,
    "estimated_value": 450000,
    "sqft": 2000,
    "bedrooms": 3,
    "bathrooms": 2
}}

print(json.dumps(result))
"""
        result = await self.execute_python(code)
        return json.loads(result["output"])
```

## CMA Wizard UI

```python
# desktop/src/ui/cma_wizard.py
from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, 
                              QLineEdit, QLabel, QPushButton)
from PySide6.QtCore import Signal, Slot
import asyncio

class PropertyInputPage(QWizardPage):
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setTitle("Property Information")
        self.setSubTitle("Enter the property address or speak it")
        
        layout = QVBoxLayout()
        
        # Address input
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("123 Main St, Anytown, ST 12345")
        layout.addWidget(QLabel("Property Address:"))
        layout.addWidget(self.address_input)
        
        # Voice input button
        self.voice_btn = QPushButton("🎤 Speak Address")
        self.voice_btn.clicked.connect(self.voice_input)
        layout.addWidget(self.voice_btn)
        
        self.setLayout(layout)
        
    @Slot()
    def voice_input(self):
        """Capture voice input via The Colonel"""
        # This would integrate with Whisper via The Colonel
        pass

class CMAWizard(QWizard):
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel = colonel_client
        
        self.setWindowTitle("CMA Generation Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Add pages
        self.addPage(PropertyInputPage(self.colonel))
        # Add more pages: comp selection, adjustments, report options
        
    def accept(self):
        """Generate the CMA when wizard completes"""
        asyncio.create_task(self.generate_cma())
        super().accept()
        
    async def generate_cma(self):
        """Use The Colonel to generate the CMA"""
        messages = [
            {"role": "system", "content": "You are a real estate CMA expert."},
            {"role": "user", "content": f"Generate a CMA for {self.property_address}"}
        ]
        
        result = await self.colonel.chat(messages, profile="cma-generator")
        # Process and display result
```

## The Colonel Profile for Real Estate

```yaml
# backend/the_colonel/profiles/real-estate.yaml
name: "Real Estate Assistant"
model: "qwen2.5:7b-instruct"
system_prompt: |
  You are an expert real estate assistant with deep knowledge of:
  - Comparative Market Analysis (CMA)
  - Property valuation
  - Market trends
  - Real estate terminology
  - MLS systems
  
  You have access to tools for:
  - Web scraping property data
  - Database queries
  - File operations
  - Calculations
  
  Always provide accurate, professional advice.

tools:
  - python_executor
  - shell_executor
  - file_reader
  - file_writer

temperature: 0.7
max_tokens: 4096
```

## Quick Start Commands

```bash
# 1. Start all services
cd backend && docker-compose up -d

# 2. Test The Colonel is running
curl http://localhost:8264/v1/models

# 3. Run the desktop app
cd desktop
python src/main.py

# 4. Test voice command (Alt+R)
# Say: "Create a CMA for 123 Main Street"
```

## Next Steps

1. **Create The Colonel profiles** for different tasks:
   - `cma-generator.yaml`
   - `lead-responder.yaml`
   - `marketing-writer.yaml`

2. **Build the UI components**:
   - Main dashboard
   - CMA wizard
   - Lead manager
   - Voice feedback widget

3. **Integrate with KDE**:
   - System tray icon
   - KRunner commands
   - Desktop notifications
   - Global shortcuts

4. **Add property data sources**:
   - MLS API integration
   - Web scraping rules
   - Public records access

Want me to create any specific component in detail?