"""
AI Chat Widget - Real Estate Assistant Integration
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                              QLineEdit, QPushButton, QComboBox, QLabel, 
                              QSplitter, QFrame, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
import threading
from core.colonel_client import ColonelClient


class AIResponseThread(QThread):
    """Thread for AI responses to avoid blocking the UI"""
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, client, message, agent_type):
        super().__init__()
        self.client = client
        self.message = message
        self.agent_type = agent_type
    
    def run(self):
        try:
            response = self.client.chat_with_agent(self.message, self.agent_type)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")


class AIChatWidget(QWidget):
    """AI Chat Widget for real estate assistant"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colonel_client = ColonelClient()
        self.current_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🤖 Real Estate AI Assistant")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Agent selector
        agent_layout = QHBoxLayout()
        agent_layout.addWidget(QLabel("Agent:"))
        
        self.agent_combo = QComboBox()
        available_agents = list(self.colonel_client.available_agents.keys())
        agent_names = [self.colonel_client.agent_profiles[agent]['name'] 
                      for agent in available_agents]
        
        for i, agent_key in enumerate(available_agents):
            agent_name = agent_names[i]
            self.agent_combo.addItem(f"{agent_name}", agent_key)
        
        agent_layout.addWidget(self.agent_combo)
        agent_layout.addStretch()
        layout.addLayout(agent_layout)
        
        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMinimumHeight(300)
        font = QFont("Consolas", 10)
        self.chat_area.setFont(font)
        layout.addWidget(self.chat_area)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your real estate AI assistant...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Status
        self.status_label = QLabel(f"✅ {len(self.colonel_client.available_agents)}/4 agents ready")
        self.status_label.setStyleSheet("color: green; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Welcome message
        self.add_system_message("Welcome! I'm your AI real estate assistant. Choose an agent and ask me anything!")
        
    def add_system_message(self, message):
        """Add a system message to the chat"""
        self.chat_area.append(f"<div style='color: #666; font-style: italic;'>🔔 {message}</div><br>")
        
    def add_user_message(self, message):
        """Add user message to chat"""
        agent_name = self.agent_combo.currentText().split(" (")[0]
        self.chat_area.append(f"<div style='color: #0066cc; font-weight: bold;'>👤 You → {agent_name}:</div>")
        self.chat_area.append(f"<div style='margin-left: 20px; margin-bottom: 10px;'>{message}</div>")
        
    def add_ai_message(self, message):
        """Add AI response to chat"""
        # Parse the response format [Agent Name]: content
        if ": " in message and message.startswith("["):
            parts = message.split(": ", 1)
            agent_name = parts[0].strip("[]")
            content = parts[1]
        else:
            agent_name = "AI"
            content = message
            
        self.chat_area.append(f"<div style='color: #cc6600; font-weight: bold;'>🤖 {agent_name}:</div>")
        self.chat_area.append(f"<div style='margin-left: 20px; margin-bottom: 15px; background-color: #f5f5f5; padding: 10px; border-radius: 5px;'>{content}</div>")
        
        # Scroll to bottom
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_area.setTextCursor(cursor)
        
    def add_error_message(self, error):
        """Add error message to chat"""
        self.chat_area.append(f"<div style='color: red; font-weight: bold;'>❌ Error:</div>")
        self.chat_area.append(f"<div style='margin-left: 20px; margin-bottom: 15px; color: red;'>{error}</div>")
        
    def send_message(self):
        """Send message to AI agent"""
        message = self.input_field.text().strip()
        if not message:
            return
            
        # Get selected agent
        agent_key = self.agent_combo.currentData()
        if not agent_key:
            self.add_error_message("No agent selected")
            return
            
        # Add user message to chat
        self.add_user_message(message)
        self.input_field.clear()
        
        # Disable send button while processing
        self.send_button.setEnabled(False)
        self.send_button.setText("Thinking...")
        
        # Start AI response thread
        self.current_thread = AIResponseThread(self.colonel_client, message, agent_key)
        self.current_thread.response_ready.connect(self.on_response_ready)
        self.current_thread.error_occurred.connect(self.on_error_occurred)
        self.current_thread.finished.connect(self.on_thread_finished)
        self.current_thread.start()
        
    def on_response_ready(self, response):
        """Handle AI response"""
        self.add_ai_message(response)
        
    def on_error_occurred(self, error):
        """Handle AI error"""
        self.add_error_message(error)
        
    def on_thread_finished(self):
        """Re-enable UI after thread completes"""
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self.current_thread = None
        
    def get_quick_commands(self):
        """Get list of quick command suggestions"""
        return [
            "Analyze this property: 3BR/2BA, $450k, downtown location",
            "What are current market trends in Portland?",
            "Help me qualify this lead: first-time buyer, $300k budget",
            "Create marketing strategy for luxury condo listing",
            "Suggest pricing for 2BR townhouse with garage",
        ]
        
    def add_quick_command_buttons(self):
        """Add quick command buttons (optional enhancement)"""
        commands_layout = QHBoxLayout()
        
        for command in self.get_quick_commands()[:3]:  # Show first 3
            btn = QPushButton(command[:30] + "...")
            btn.clicked.connect(lambda checked, cmd=command: self.input_field.setText(cmd))
            btn.setMaximumHeight(30)
            commands_layout.addWidget(btn)
            
        return commands_layout