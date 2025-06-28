
## File 6: Voice Assistant Integration

```python
# desktop/src/core/voice_assistant.py
import asyncio
import tempfile
import wave
import json
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtMultimedia import QMediaRecorder, QAudioInput, QMediaCaptureSession
import pyaudio
import numpy as np

class VoiceAssistant(QObject):
    """Voice assistant using Whisper and Kokoro TTS"""
    
    # Signals
    transcription_ready = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.recording = False
        self.audio_data = []
        
        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.stream = None
        
    def start_listening(self, callback=None):
        """Start listening for voice input"""
        self.callback = callback
        self.status_changed.emit("Listening...")
        self.start_recording()
        
        # Auto-stop after 5 seconds
        asyncio.create_task(self.auto_stop(5))
    
    def start_recording(self):
        """Start audio recording"""
        self.recording = True
        self.audio_data = []
        
        # Open audio stream
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if self.recording:
            self.audio_data.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self):
        """Stop recording and process"""
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Save audio to temp file
        if self.audio_data:
            asyncio.create_task(self.process_audio())
    
    async def auto_stop(self, duration):
        """Auto-stop recording after duration"""
        await asyncio.sleep(duration)
        if self.recording:
            self.stop_recording()
    
    async def process_audio(self):
        """Process recorded audio with Whisper"""
        # Save audio to file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_data))
        wf.close()
        
        # Send to Colonel for transcription
        code = f'''
import whisper
import json

# Load Whisper model
model = whisper.load_model("base")

# Transcribe audio
result = model.transcribe("{temp_file.name}")
text = result["text"].strip()

print(json.dumps({{"text": text}}))
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            data = json.loads(result["output"])
            text = data.get("text", "")
            
            self.transcription_ready.emit(text)
            if self.callback:
                self.callback(text)
        
        # Cleanup
        Path(temp_file.name).unlink()
    
    async def speak(self, text: str):
        """Convert text to speech using Kokoro TTS"""
        code = f'''
import requests
import json
import base64

# Call Kokoro TTS service
response = requests.post(
    "http://unicorn-kokoro:8880/tts",
    json={{"text": "{text}", "voice": "en-US-Female"}}
)

# Get audio data
audio_data = response.content
encoded = base64.b64encode(audio_data).decode('utf-8')

print(json.dumps({{"audio": encoded}}))
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            data = json.loads(result["output"])
            # Play audio (would need QMediaPlayer setup)
```

## File 7: KDE Plasma Integration

```python
# desktop/src/kde/plasma_integration.py
import dbus
from PySide6.QtCore import QObject, Signal
from PySide6.QtDBus import QDBusConnection, QDBusInterface

class PlasmaIntegration(QObject):
    """KDE Plasma desktop integration"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.bus = QDBusConnection.sessionBus()
        
        # Register with KDE
        self.register_service()
        
    def register_service(self):
        """Register as KDE service"""
        # Register D-Bus service
        self.bus.registerService("com.unicorncommander.RealEstateCommander")
        
        # Register with KDE globals
        kglobal = QDBusInterface(
            "org.kde.kglobalaccel",
            "/kglobalaccel",
            "org.kde.KGlobalAccel",
            self.bus
        )
    
    def register_global_shortcut(self, key_sequence, name, callback):
        """Register a global shortcut with KDE"""
        # This would integrate with KDE's global shortcuts system
        # For now, use Qt's approach
        from PySide6.QtGui import QShortcut, QKeySequence
        from PySide6.QtWidgets import QApplication
        
        shortcut = QShortcut(QKeySequence(key_sequence), self.app.main_window)
        shortcut.activated.connect(callback)
        shortcut.setContext(Qt.ApplicationShortcut)
    
    def show_notification(self, title, message, icon="dialog-information"):
        """Show KDE notification"""
        notify = QDBusInterface(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            self.bus
        )
        
        notify.call(
            "Notify",
            "Real Estate Commander",  # app name
            0,  # replaces id
            icon,  # icon
            title,  # summary
            message,  # body
            [],  # actions
            {},  # hints
            5000  # timeout
        )
    
    def add_to_activities(self, activity_id, window_id):
        """Add window to KDE activity"""
        activities = QDBusInterface(
            "org.kde.ActivityManager",
            "/ActivityManager",
            "org.kde.ActivityManager",
            self.bus
        )
        
        # Associate window with activity
        activities.call("associateWindow", window_id, activity_id)
    
    def create_krunner_plugin(self):
        """Create KRunner search plugin"""
        # This would create a KRunner plugin for quick commands
        # Users could type "cma 123 main st" in KRunner
        pass
```

## File 8: Dashboard Widget

```python
# desktop/src/ui/dashboard_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QFrame, QGridLayout, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont
import asyncio
from datetime import datetime

class MetricCard(QFrame):
    """Dashboard metric card"""
    
    clicked = Signal()
    
    def __init__(self, title, value="0", icon="", color="#2196F3"):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: #f5f5f5;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Icon and title
        header = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
            header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 14px;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(self.value_label)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_value(self, value):
        self.value_label.setText(str(value))

class DashboardWidget(QWidget):
    """Main dashboard widget"""
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setup_ui()
        self.start_updates()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Welcome message
        welcome = QLabel(f"Welcome back! Today is {datetime.now().strftime('%A, %B %d, %Y')}")
        welcome.setStyleSheet("font-size: 18px; padding: 10px;")
        layout.addWidget(welcome)
        
        # Metrics grid
        metrics_layout = QGridLayout()
        
        # Today's metrics
        self.cma_card = MetricCard("CMAs Today", "0", "📊", "#2196F3")
        self.cma_card.clicked.connect(lambda: self.parent().parent().tabs.setCurrentIndex(1))
        metrics_layout.addWidget(self.cma_card, 0, 0)
        
        self.leads_card = MetricCard("New Leads", "0", "👥", "#4CAF50")
        self.leads_card.clicked.connect(lambda: self.parent().parent().tabs.setCurrentIndex(2))
        metrics_layout.addWidget(self.leads_card, 0, 1)
        
        self.showings_card = MetricCard("Showings", "0", "🏠", "#FF9800")
        metrics_layout.addWidget(self.showings_card, 0, 2)
        
        self.tasks_card = MetricCard("Tasks", "0", "✓", "#9C27B0")
        metrics_layout.addWidget(self.tasks_card, 0, 3)
        
        layout.addLayout(metrics_layout)
        
        # Recent activity
        activity_label = QLabel("Recent Activity")
        activity_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
        layout.addWidget(activity_label)
        
        self.activity_list = QWidget()
        activity_layout = QVBoxLayout(self.activity_list)
        
        # Sample activities
        activities = [
            ("🎤", "Voice command: 'Create CMA for 123 Main St'", "2 min ago"),
            ("📧", "New lead from Zillow: Sarah Johnson", "15 min ago"),
            ("📊", "CMA completed: 456 Oak Ave", "1 hour ago"),
            ("📱", "Missed call from (555) 123-4567", "2 hours ago")
        ]
        
        for icon, text, time in activities:
            item = QHBoxLayout()
            item.addWidget(QLabel(icon))
            item.addWidget(QLabel(text))
            item.addStretch()
            item.addWidget(QLabel(time))
            
            activity_layout.addLayout(item)
        
        layout.addWidget(self.activity_list)
        layout.addStretch()
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        voice_btn = QPushButton("🎤 Voice Command")
        voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        voice_btn.clicked.connect(self.parent().parent().activate_voice)
        actions_layout.addWidget(voice_btn)
        
        cma_btn = QPushButton("📊 New CMA")
        cma_btn.clicked.connect(self.parent().parent().new_cma)
        actions_layout.addWidget(cma_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def start_updates(self):
        """Start periodic dashboard updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Initial update
        self.update_metrics()
    
    @Slot()
    def update_metrics(self):
        """Update dashboard metrics"""
        asyncio.create_task(self.fetch_metrics())
    
    async def fetch_metrics(self):
        """Fetch latest metrics from database"""
        code = '''
import json
from datetime import datetime, date

# Get today's metrics (would query database)
metrics = {
    "cmas_today": 3,
    "new_leads": 7,
    "showings": 2,
    "tasks": 5
}

print(json.dumps(metrics))
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            metrics = json.loads(result["output"])
            self.cma_card.update_value(metrics["cmas_today"])
            self.leads_card.update_value(metrics["new_leads"])
            self.showings_card.update_value(metrics["showings"])
            self.tasks_card.update_value(metrics["tasks"])
```

## File 9: Setup and Installation Scripts

```bash
# scripts/setup.sh
#!/bin/bash
set -e

echo "🦄 UC-1 Real Estate Commander Setup"
echo "===================================="

# Check system requirements
echo "Checking system requirements..."

# Check for Python 3.9+
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,9) else 1)'; then
    echo "❌ Python 3.9 or higher is required"
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required. Please install Docker first."
    exit 1
fi

# Check for KDE
if ! command -v plasmashell &> /dev/null; then
    echo "⚠️  Warning: KDE Plasma not detected. Some features may not work."
fi

# Create directories
echo "Creating project structure..."
mkdir -p ~/.local/share/uc1-commander/{data,logs,profiles}
mkdir -p ~/.config/uc1-commander

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup Docker services
echo "Setting up Docker services..."
cd backend
docker-compose up -d
cd ..

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

# Download Ollama models
echo "Downloading AI models..."
docker exec uc1-ollama ollama pull qwen2.5:7b-instruct-q4_K_M
docker exec uc1-ollama ollama pull phi3:mini

# Create desktop entry
echo "Creating desktop shortcuts..."
cat > ~/.local/share/applications/uc1-real-estate-commander.desktop << EOF
[Desktop Entry]
Type=Application
Name=Real Estate Commander
Comment=AI-powered real estate assistant
Icon=home
Exec=$PWD/venv/bin/python $PWD/desktop/src/main.py
Terminal=false
Categories=Office;Development;
Keywords=real estate;cma;ai;assistant;
EOF

# Create Colonel profiles
echo "Setting up AI profiles..."
cp scripts/profiles/*.yaml backend/colonel/profiles/

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  python desktop/src/main.py"
echo ""
echo "Or use the desktop shortcut in your application menu"
```

## File 10: Requirements and Docker Compose

```txt
# requirements.txt
PySide6>=6.6.0
aiohttp>=3.9.0
asyncio
python-dotenv
sqlalchemy>=2.0.0
psycopg2-binary
redis>=5.0.0
chromadb>=0.4.0
qdrant-client
reportlab>=4.0.0
pillow>=10.0.0
matplotlib>=3.8.0
pyaudio>=0.2.13
numpy>=1.24.0
watchdog>=3.0.0
dbus-python
```

```yaml
# backend/docker-compose.yml
version: '3.8'

services:
  the_colonel:
    build: 
      context: ./colonel
      dockerfile: Dockerfile
    container_name: uc1-colonel
    ports:
      - "8264:8264"
    volumes:
      - ./colonel/profiles:/app/profiles
      - ~/.local/share/uc1-commander:/app/data
    environment:
      - PYTHONUNBUFFERED=1
      - OPENAI_API_KEY=${OPENAI_API_KEY:-none}
    networks:
      - uc1-network
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:rocm
    container_name: uc1-ollama
    devices:
      - /dev/kfd:/dev/kfd
      - /dev/dri:/dev/dri
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - HSA_OVERRIDE_GFX_VERSION=11.0.2
      - OLLAMA_HOST=0.0.0.0
    networks:
      - uc1-network

  postgres:
    image: postgres:16-alpine
    container_name: uc1-postgres
    environment:
      - POSTGRES_USER=realestate
      - POSTGRES_PASSWORD=commander123
      - POSTGRES_DB=realestate_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - uc1-network

  redis:# UC-1 Real Estate Commander - Complete Implementation Files

## Project Overview for AI Assistant

You are building a KDE-native Real Estate Command Center that runs on the UC-1 hardware. The application helps real estate agents automate their workflows, with initial focus on CMA (Comparative Market Analysis) generation.

**Technology Stack:**
- PySide6 for KDE desktop application
- The_Colonel (Open Interpreter fork) for AI capabilities
- PostgreSQL for data storage
- Docker services for backend
- Voice control via Whisper/Kokoro

## File 1: Project Structure and Setup

```bash
# create_project_structure.sh
#!/bin/bash

# Create the complete project structure
mkdir -p uc1-real-estate-commander/{backend,desktop,shared,scripts,docs}
mkdir -p uc1-real-estate-commander/backend/{api,colonel,docker}
mkdir -p uc1-real-estate-commander/desktop/src/{ui,core,kde,assets}
mkdir -p uc1-real-estate-commander/desktop/resources/{icons,templates,styles}
mkdir -p uc1-real-estate-commander/shared/{models,prompts,utils}

cd uc1-real-estate-commander

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.env
.vscode/
.idea/
*.log
*.db
.DS_Store
build/
dist/
*.egg-info/
EOF

# Create README
cat > README.md << 'EOF'
# UC-1 Real Estate Commander

AI-powered real estate assistant running locally on UC-1 hardware.

## Features
- Voice-controlled CMA generation
- 24/7 lead response system
- Marketing automation
- KDE desktop integration

## Quick Start
```bash
./scripts/setup.sh
source venv/bin/activate
python desktop/src/main.py
```
EOF

echo "Project structure created!"
```

## File 2: Main Application Entry Point

```python
# desktop/src/main.py
#!/usr/bin/env python3
"""
UC-1 Real Estate Commander - Main Application
KDE-native real estate assistant powered by The Colonel
"""
import sys
import os
import asyncio
import signal
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtGui import QIcon, QAction

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from desktop.src.ui.main_window import MainWindow
from desktop.src.core.colonel_client import ColonelClient
from desktop.src.core.voice_assistant import VoiceAssistant
from desktop.src.kde.plasma_integration import PlasmaIntegration

class RealEstateCommander(QApplication):
    """Main application class"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Application metadata
        self.setApplicationName("UC-1 Real Estate Commander")
        self.setOrganizationName("Unicorn Commander")
        self.setApplicationDisplayName("Real Estate Commander")
        self.setQuitOnLastWindowClosed(False)
        
        # Initialize components
        self.colonel = ColonelClient("http://localhost:8264")
        self.voice_assistant = VoiceAssistant(self.colonel)
        
        # Create main window
        self.main_window = MainWindow(self.colonel, self.voice_assistant)
        
        # KDE integration
        self.plasma = PlasmaIntegration(self)
        self.setup_global_shortcuts()
        
        # System tray
        self.setup_system_tray()
        
        # Async event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def setup_global_shortcuts(self):
        """Register KDE global shortcuts"""
        shortcuts = [
            ("Alt+C", "New CMA", self.main_window.new_cma_voice),
            ("Alt+R", "Voice Command", self.main_window.activate_voice),
            ("Alt+L", "Show Leads", self.main_window.show_leads),
            ("Alt+M", "New Marketing", self.main_window.new_marketing)
        ]
        
        for key, name, callback in shortcuts:
            self.plasma.register_global_shortcut(key, name, callback)
    
    def setup_system_tray(self):
        """Create system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("home"))
        self.tray_icon.setToolTip("Real Estate Commander")
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)
        
        new_cma_action = QAction("New CMA", self)
        new_cma_action.triggered.connect(self.main_window.new_cma)
        tray_menu.addAction(new_cma_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()

def main():
    """Application entry point"""
    app = RealEstateCommander(sys.argv)
    
    # Show main window
    app.main_window.show()
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

## File 3: Main Window UI

```python
# desktop/src/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QPushButton, QLabel, QListWidget,
                              QTextEdit, QGroupBox, QGridLayout, QLineEdit,
                              QProgressBar, QMenuBar, QStatusBar)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QKeySequence
import asyncio
from datetime import datetime

from desktop.src.ui.cma_wizard import CMAWizard
from desktop.src.ui.dashboard_widget import DashboardWidget

class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    voice_command_received = Signal(str)
    status_update = Signal(str)
    
    def __init__(self, colonel_client, voice_assistant):
        super().__init__()
        self.colonel = colonel_client
        self.voice = voice_assistant
        
        self.setWindowTitle("UC-1 Real Estate Commander")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set KDE window properties
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        
    def setup_ui(self):
        """Create the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Voice status bar
        self.voice_status = QWidget()
        voice_layout = QHBoxLayout(self.voice_status)
        
        self.voice_indicator = QLabel("🎤 Ready")
        self.voice_indicator.setStyleSheet("QLabel { font-size: 16px; padding: 5px; }")
        voice_layout.addWidget(self.voice_indicator)
        
        self.voice_button = QPushButton("Hold to Speak (Alt+R)")
        self.voice_button.setCheckable(True)
        self.voice_button.pressed.connect(self.start_voice_recording)
        self.voice_button.released.connect(self.stop_voice_recording)
        voice_layout.addWidget(self.voice_button)
        
        voice_layout.addStretch()
        layout.addWidget(self.voice_status)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard = DashboardWidget(self.colonel)
        self.tabs.addTab(self.dashboard, "Dashboard")
        
        # CMAs tab
        self.cma_widget = self.create_cma_tab()
        self.tabs.addTab(self.cma_widget, "CMAs")
        
        # Leads tab
        self.leads_widget = self.create_leads_tab()
        self.tabs.addTab(self.leads_widget, "Leads")
        
        # Marketing tab
        self.marketing_widget = self.create_marketing_tab()
        self.tabs.addTab(self.marketing_widget, "Marketing")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_cma_tab(self):
        """Create the CMA management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.new_cma_btn = QPushButton("New CMA (Alt+C)")
        self.new_cma_btn.clicked.connect(self.new_cma)
        toolbar.addWidget(self.new_cma_btn)
        
        self.voice_cma_btn = QPushButton("🎤 Voice CMA")
        self.voice_cma_btn.clicked.connect(self.new_cma_voice)
        toolbar.addWidget(self.voice_cma_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Recent CMAs list
        self.cma_list = QListWidget()
        layout.addWidget(QLabel("Recent CMAs:"))
        layout.addWidget(self.cma_list)
        
        return widget
    
    def create_leads_tab(self):
        """Create the leads management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats
        stats_group = QGroupBox("Lead Statistics")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("New Today:"), 0, 0)
        self.new_leads_label = QLabel("0")
        stats_layout.addWidget(self.new_leads_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Pending:"), 0, 2)
        self.pending_leads_label = QLabel("0")
        stats_layout.addWidget(self.pending_leads_label, 0, 3)
        
        layout.addWidget(stats_group)
        
        # Lead list
        self.leads_list = QListWidget()
        layout.addWidget(QLabel("Recent Leads:"))
        layout.addWidget(self.leads_list)
        
        return widget
    
    def create_marketing_tab(self):
        """Create the marketing automation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.new_listing_btn = QPushButton("New Listing Campaign")
        self.new_listing_btn.clicked.connect(self.new_marketing)
        actions_layout.addWidget(self.new_listing_btn)
        
        self.social_media_btn = QPushButton("Generate Social Posts")
        actions_layout.addWidget(self.social_media_btn)
        
        layout.addWidget(actions_group)
        
        # Campaign list
        self.campaigns_list = QListWidget()
        layout.addWidget(QLabel("Active Campaigns:"))
        layout.addWidget(self.campaigns_list)
        
        return widget
    
    def setup_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_cma_action = QAction("New CMA", self)
        new_cma_action.setShortcut(QKeySequence("Ctrl+N"))
        new_cma_action.triggered.connect(self.new_cma)
        file_menu.addAction(new_cma_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        voice_action = QAction("Voice Command", self)
        voice_action.setShortcut(QKeySequence("Alt+R"))
        voice_action.triggered.connect(self.activate_voice)
        tools_menu.addAction(voice_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Connect signals and slots"""
        self.voice_command_received.connect(self.process_voice_command)
        self.status_update.connect(self.update_status)
    
    @Slot()
    def new_cma(self):
        """Launch CMA wizard"""
        wizard = CMAWizard(self.colonel, self)
        wizard.exec()
    
    @Slot()
    def new_cma_voice(self):
        """Start voice-controlled CMA creation"""
        self.voice_indicator.setText("🎤 Say the property address...")
        self.voice.start_listening(callback=self.handle_cma_voice)
    
    @Slot()
    def activate_voice(self):
        """Activate voice command mode"""
        self.voice_indicator.setText("🎤 Listening...")
        self.voice.start_listening(callback=self.handle_voice_command)
    
    @Slot()
    def show_leads(self):
        """Show leads tab"""
        self.tabs.setCurrentIndex(2)
        self.show()
        self.raise_()
    
    @Slot()
    def new_marketing(self):
        """Create new marketing campaign"""
        # Launch marketing wizard
        pass
    
    @Slot()
    def start_voice_recording(self):
        """Start recording voice"""
        self.voice_indicator.setText("🔴 Recording...")
        self.voice.start_recording()
    
    @Slot()
    def stop_voice_recording(self):
        """Stop recording and process"""
        self.voice_indicator.setText("⏳ Processing...")
        text = self.voice.stop_recording()
        if text:
            self.voice_command_received.emit(text)
    
    @Slot(str)
    def process_voice_command(self, command):
        """Process voice command"""
        self.status_bar.showMessage(f"Processing: {command}")
        # Send to Colonel for processing
        asyncio.create_task(self.colonel.process_command(command))
    
    def handle_cma_voice(self, text):
        """Handle voice input for CMA"""
        if text:
            # Launch CMA wizard with address
            wizard = CMAWizard(self.colonel, self)
            wizard.set_address(text)
            wizard.exec()
    
    def handle_voice_command(self, text):
        """Handle general voice command"""
        if text:
            self.process_voice_command(text)
    
    @Slot(str)
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.showMessage(message)
        self.voice_indicator.setText("🎤 Ready")
    
    @Slot()
    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About", 
                         "UC-1 Real Estate Commander\n\n"
                         "AI-powered real estate assistant\n"
                         "Built on UC-1 hardware")
```

## File 4: Colonel Client Integration

```python
# desktop/src/core/colonel_client.py
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

class ColonelClient:
    """Client for The_Colonel API server"""
    
    def __init__(self, base_url: str = "http://localhost:8264"):
        self.base_url = base_url
        self.session = None
        self.profiles_dir = Path(__file__).parent.parent.parent.parent / "backend/colonel/profiles"
        
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
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read file via The Colonel"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tools/files/read",
                json={"path": path}
            ) as resp:
                return await resp.json()
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file via The Colonel"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tools/files/write",
                json={"path": path, "content": content}
            ) as resp:
                return await resp.json()
    
    async def take_screenshot(self) -> Dict[str, Any]:
        """Take screenshot via The Colonel"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tools/computer/screenshot"
            ) as resp:
                return await resp.json()
    
    async def chat(self, messages: List[Dict[str, str]], 
                   profile: str = "real-estate-assistant",
                   stream: bool = False) -> str:
        """Chat with The Colonel using a specific profile"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                params={"profile": profile},
                json={
                    "model": "the-colonel",
                    "messages": messages,
                    "stream": stream
                }
            ) as resp:
                if stream:
                    # Handle streaming response
                    async for line in resp.content:
                        if line:
                            yield line.decode('utf-8')
                else:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process natural language command"""
        messages = [
            {
                "role": "system", 
                "content": "You are a real estate AI assistant. Parse the user's command and execute the appropriate action."
            },
            {
                "role": "user",
                "content": command
            }
        ]
        
        response = await self.chat(messages, profile="command-processor")
        
        # The Colonel should return structured action
        return {"action": response, "status": "processed"}
    
    async def generate_cma(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a CMA using The Colonel"""
        code = f'''
import json
import pandas as pd
from datetime import datetime

# Property data
subject = {json.dumps(property_data)}

# Generate CMA analysis
# This would normally pull comps from database or scrape
comps = [
    {{"address": "124 Main St", "price": 455000, "sqft": 2100, "beds": 3, "baths": 2}},
    {{"address": "122 Main St", "price": 445000, "sqft": 1950, "beds": 3, "baths": 2}},
    {{"address": "126 Main St", "price": 465000, "sqft": 2200, "beds": 3, "baths": 2.5}}
]

# Calculate price per sqft
for comp in comps:
    comp["price_per_sqft"] = comp["price"] / comp["sqft"]

# Analysis
avg_price_per_sqft = sum(c["price_per_sqft"] for c in comps) / len(comps)
estimated_value = subject["sqft"] * avg_price_per_sqft

result = {{
    "subject": subject,
    "comparables": comps,
    "analysis": {{
        "avg_price_per_sqft": round(avg_price_per_sqft, 2),
        "estimated_value": round(estimated_value, -3),
        "value_range": {{
            "low": round(estimated_value * 0.95, -3),
            "high": round(estimated_value * 1.05, -3)
        }},
        "generated_at": datetime.now().isoformat()
    }}
}}

print(json.dumps(result, indent=2))
'''
        
        result = await self.execute_python(code)
        return json.loads(result["output"])
```

## File 5: CMA Wizard

```python
# desktop/src/ui/cma_wizard.py
from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                              QLineEdit, QLabel, QPushButton, QTableWidget,
                              QTableWidgetItem, QTextEdit, QComboBox,
                              QSpinBox, QCheckBox, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QPixmap
import asyncio
import json
from datetime import datetime

class PropertyInputPage(QWizardPage):
    """First page - property input"""
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setTitle("Property Information")
        self.setSubTitle("Enter the subject property details")
        
        layout = QVBoxLayout()
        
        # Address section
        address_group = QGroupBox("Property Address")
        address_layout = QGridLayout(address_group)
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("123 Main St, Anytown, ST 12345")
        address_layout.addWidget(QLabel("Address:"), 0, 0)
        address_layout.addWidget(self.address_input, 0, 1, 1, 2)
        
        self.voice_btn = QPushButton("🎤 Speak Address")
        self.voice_btn.clicked.connect(self.voice_input)
        address_layout.addWidget(self.voice_btn, 0, 3)
        
        layout.addWidget(address_group)
        
        # Property details
        details_group = QGroupBox("Property Details")
        details_layout = QGridLayout(details_group)
        
        # Bedrooms
        details_layout.addWidget(QLabel("Bedrooms:"), 0, 0)
        self.bedrooms = QSpinBox()
        self.bedrooms.setRange(1, 10)
        self.bedrooms.setValue(3)
        details_layout.addWidget(self.bedrooms, 0, 1)
        
        # Bathrooms
        details_layout.addWidget(QLabel("Bathrooms:"), 0, 2)
        self.bathrooms = QSpinBox()
        self.bathrooms.setRange(1, 10)
        self.bathrooms.setValue(2)
        details_layout.addWidget(self.bathrooms, 0, 3)
        
        # Square footage
        details_layout.addWidget(QLabel("Sq Ft:"), 1, 0)
        self.sqft = QSpinBox()
        self.sqft.setRange(500, 10000)
        self.sqft.setValue(2000)
        self.sqft.setSingleStep(50)
        details_layout.addWidget(self.sqft, 1, 1)
        
        # Year built
        details_layout.addWidget(QLabel("Year Built:"), 1, 2)
        self.year_built = QSpinBox()
        self.year_built.setRange(1900, 2025)
        self.year_built.setValue(2000)
        details_layout.addWidget(self.year_built, 1, 3)
        
        # Property type
        details_layout.addWidget(QLabel("Type:"), 2, 0)
        self.property_type = QComboBox()
        self.property_type.addItems(["Single Family", "Condo", "Townhouse", "Multi-Family"])
        details_layout.addWidget(self.property_type, 2, 1)
        
        layout.addWidget(details_group)
        
        # Auto-fill button
        self.autofill_btn = QPushButton("🔍 Auto-fill from MLS/Public Records")
        self.autofill_btn.clicked.connect(self.autofill_property)
        layout.addWidget(self.autofill_btn)
        
        self.setLayout(layout)
        
        # Register fields
        self.registerField("address*", self.address_input)
        self.registerField("bedrooms", self.bedrooms)
        self.registerField("bathrooms", self.bathrooms)
        self.registerField("sqft", self.sqft)
        self.registerField("year_built", self.year_built)
        self.registerField("property_type", self.property_type, "currentText")
    
    @Slot()
    def voice_input(self):
        """Capture voice input for address"""
        # This would integrate with voice assistant
        pass
    
    @Slot()
    def autofill_property(self):
        """Auto-fill property details from MLS/public records"""
        address = self.address_input.text()
        if address:
            # Use Colonel to scrape property data
            asyncio.create_task(self.fetch_property_data(address))
    
    async def fetch_property_data(self, address):
        """Fetch property data via Colonel"""
        code = f'''
# Scrape property data for: {address}
# This would connect to MLS API or scrape public records
# For demo, return mock data
import json

data = {{
    "bedrooms": 4,
    "bathrooms": 2.5,
    "sqft": 2150,
    "year_built": 2005,
    "property_type": "Single Family"
}}

print(json.dumps(data))
'''
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            data = json.loads(result["output"])
            self.bedrooms.setValue(data["bedrooms"])
            self.bathrooms.setValue(data["bathrooms"])
            self.sqft.setValue(data["sqft"])
            self.year_built.setValue(data["year_built"])

class ComparablesPage(QWizardPage):
    """Second page - select comparables"""
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setTitle("Select Comparables")
        self.setSubTitle("Choose comparable properties for analysis")
        
        layout = QVBoxLayout()
        
        # Search criteria
        criteria_group = QGroupBox("Search Criteria")
        criteria_layout = QGridLayout(criteria_group)
        
        criteria_layout.addWidget(QLabel("Radius (miles):"), 0, 0)
        self.radius = QSpinBox()
        self.radius.setRange(1, 10)
        self.radius.setValue(1)
        criteria_layout.addWidget(self.radius, 0, 1)
        
        criteria_layout.addWidget(QLabel("Max Age (months):"), 0, 2)
        self.max_age = QSpinBox()
        self.max_age.setRange(1, 12)
        self.max_age.setValue(6)
        criteria_layout.addWidget(self.max_age, 0, 3)
        
        self.search_btn = QPushButton("Search for Comparables")
        self.search_btn.clicked.connect(self.search_comparables)
        criteria_layout.addWidget(self.search_btn, 1, 0, 1, 4)
        
        layout.addWidget(criteria_group)
        
        # Comparables table
        self.comps_table = QTableWidget()
        self.comps_table.setColumnCount(7)
        self.comps_table.setHorizontalHeaderLabels([
            "Select", "Address", "Price", "Sq Ft", "Beds", "Baths", "Sold Date"
        ])
        layout.addWidget(self.comps_table)
        
        self.setLayout(layout)
    
    @Slot()
    def search_comparables(self):
        """Search for comparable properties"""
        # Get subject property from wizard
        address = self.wizard().field("address")
        sqft = self.wizard().field("sqft")
        beds = self.wizard().field("bedrooms")
        
        asyncio.create_task(self.fetch_comparables(address, sqft, beds))
    
    async def fetch_comparables(self, address, sqft, beds):
        """Fetch comparables via Colonel"""
        code = f'''
import json
from datetime import datetime, timedelta

# Search for comparables near {address}
# Criteria: {sqft} sqft, {beds} beds, within {self.radius.value()} miles

# Mock data for demo - would actually scrape MLS/public records
comps = [
    {{
        "address": "124 Main St",
        "price": 455000,
        "sqft": 2100,
        "beds": 3,
        "baths": 2,
        "sold_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    }},
    {{
        "address": "456 Oak Ave",
        "price": 448000,
        "sqft": 2050,
        "beds": 3,
        "baths": 2,
        "sold_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d")
    }},
    {{
        "address": "789 Elm Dr",
        "price": 465000,
        "sqft": 2200,
        "beds": 4,
        "baths": 2.5,
        "sold_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    }},
    {{
        "address": "321 Pine St",
        "price": 442000,
        "sqft": 1950,
        "beds": 3,
        "baths": 2,
        "sold_date": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    }}
]

print(json.dumps(comps))
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            comps = json.loads(result["output"])
            self.populate_comps_table(comps)
    
    def populate_comps_table(self, comps):
        """Populate the comparables table"""
        self.comps_table.setRowCount(len(comps))
        
        for row, comp in enumerate(comps):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.comps_table.setCellWidget(row, 0, checkbox)
            
            # Data
            self.comps_table.setItem(row, 1, QTableWidgetItem(comp["address"]))
            self.comps_table.setItem(row, 2, QTableWidgetItem(f"${comp['price']:,}"))
            self.comps_table.setItem(row, 3, QTableWidgetItem(f"{comp['sqft']:,}"))
            self.comps_table.setItem(row, 4, QTableWidgetItem(str(comp["beds"])))
            self.comps_table.setItem(row, 5, QTableWidgetItem(str(comp["baths"])))
            self.comps_table.setItem(row, 6, QTableWidgetItem(comp["sold_date"]))

class AnalysisPage(QWizardPage):
    """Third page - adjustments and analysis"""
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setTitle("Market Analysis")
        self.setSubTitle("Review and adjust the comparative analysis")
        
        layout = QVBoxLayout()
        
        # Analysis summary
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        layout.addWidget(QLabel("Analysis Summary:"))
        layout.addWidget(self.analysis_text)
        
        # Value estimate
        value_group = QGroupBox("Estimated Value")
        value_layout = QGridLayout(value_group)
        
        value_layout.addWidget(QLabel("Low:"), 0, 0)
        self.value_low = QLabel("$0")
        value_layout.addWidget(self.value_low, 0, 1)
        
        value_layout.addWidget(QLabel("Recommended:"), 0, 2)
        self.value_recommended = QLabel("$0")
        value_layout.addWidget(self.value_recommended, 0, 3)
        
        value_layout.addWidget(QLabel("High:"), 0, 4)
        self.value_high = QLabel("$0")
        value_layout.addWidget(self.value_high, 0, 5)
        
        layout.addWidget(value_group)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """Run analysis when page is shown"""
        asyncio.create_task(self.run_analysis())
    
    async def run_analysis(self):
        """Run CMA analysis via Colonel"""
        # Get property data
        property_data = {
            "address": self.wizard().field("address"),
            "sqft": self.wizard().field("sqft"),
            "bedrooms": self.wizard().field("bedrooms"),
            "bathrooms": self.wizard().field("bathrooms"),
            "year_built": self.wizard().field("year_built")
        }
        
        result = await self.colonel.generate_cma(property_data)
        
        # Update UI
        analysis = result.get("analysis", {})
        self.value_low.setText(f"${analysis['value_range']['low']:,}")
        self.value_recommended.setText(f"${analysis['estimated_value']:,}")
        self.value_high.setText(f"${analysis['value_range']['high']:,}")
        
        # Generate analysis text
        analysis_text = f"""
COMPARATIVE MARKET ANALYSIS
Generated: {datetime.now().strftime('%B %d, %Y')}

Subject Property: {property_data['address']}
Square Footage: {property_data['sqft']:,}
Bedrooms: {property_data['bedrooms']}
Bathrooms: {property_data['bathrooms']}

MARKET ANALYSIS:
Average Price per Sq Ft: ${analysis['avg_price_per_sqft']:.2f}

Based on the analysis of {len(result.get('comparables', []))} comparable properties,
the estimated market value is:

${analysis['estimated_value']:,}

Value Range: ${analysis['value_range']['low']:,} - ${analysis['value_range']['high']:,}
"""
        self.analysis_text.setPlainText(analysis_text)

class ReportPage(QWizardPage):
    """Final page - generate report"""
    
    def __init__(self, colonel_client):
        super().__init__()
        self.colonel = colonel_client
        self.setTitle("Generate Report")
        self.setSubTitle("Customize and generate the CMA report")
        
        layout = QVBoxLayout()
        
        # Report options
        options_group = QGroupBox("Report Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_photos = QCheckBox("Include property photos")
        self.include_photos.setChecked(True)
        options_layout.addWidget(self.include_photos)
        
        self.include_map = QCheckBox("Include neighborhood map")
        self.include_map.setChecked(True)
        options_layout.addWidget(self.include_map)
        
        self.include_trends = QCheckBox("Include market trends")
        self.include_trends.setChecked(True)
        options_layout.addWidget(self.include_trends)
        
        layout.addWidget(options_group)
        
        # Agent branding
        branding_group = QGroupBox("Agent Information")
        branding_layout = QGridLayout(branding_group)
        
        branding_layout.addWidget(QLabel("Agent Name:"), 0, 0)
        self.agent_name = QLineEdit()
        self.agent_name.setText("Your Name")
        branding_layout.addWidget(self.agent_name, 0, 1)
        
        branding_layout.addWidget(QLabel("Phone:"), 1, 0)
        self.agent_phone = QLineEdit()
        self.agent_phone.setText("(555) 123-4567")
        branding_layout.addWidget(self.agent_phone, 1, 1)
        
        branding_layout.addWidget(QLabel("Email:"), 2, 0)
        self.agent_email = QLineEdit()
        self.agent_email.setText("agent@realestate.com")
        branding_layout.addWidget(self.agent_email, 2, 1)
        
        layout.addWidget(branding_group)
        
        # Generate button
        self.generate_btn = QPushButton("Generate PDF Report")
        self.generate_btn.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_btn)
        
        self.setLayout(layout)
    
    @Slot()
    def generate_report(self):
        """Generate the PDF report"""
        asyncio.create_task(self.create_pdf())
    
    async def create_pdf(self):
        """Create PDF via Colonel"""
        code = '''
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from datetime import datetime
import json

# Create PDF
filename = f"CMA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
doc = SimpleDocTemplate(filename, pagesize=letter)
story = []
styles = getSampleStyleSheet()

# Add content
story.append(Paragraph("COMPARATIVE MARKET ANALYSIS", styles['Title']))
story.append(Spacer(1, 12))
story.append(Paragraph(f"Prepared on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))

# Build PDF
doc.build(story)
print(f"Report generated: {filename}")
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            # Show success message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Success", "CMA Report generated successfully!")

class CMAWizard(QWizard):
    """Main CMA generation wizard"""
    
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel = colonel_client
        
        self.setWindowTitle("CMA Generation Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(800, 600)
        
        # Add pages
        self.addPage(PropertyInputPage(self.colonel))
        self.addPage(ComparablesPage(self.colonel))
        self.addPage(AnalysisPage(self.colonel))
        self.addPage(ReportPage(self.colonel))
    
    def set_address(self, address: str):
        """Set address from voice input"""
        self.page(0).address_input.setText(address)