"""
AI-Enhanced Team Chat Widget for Real Estate Command Center
Revolutionary team collaboration with integrated AI agents
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QLabel, QListWidget, QListWidgetItem, QComboBox,
    QFrame, QSplitter, QScrollArea, QGroupBox, QCheckBox,
    QMessageBox, QCompleter, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot, QStringListModel
from PySide6.QtGui import QAction, QIcon, QFont, QPalette, QColor, QTextCursor
import qtawesome as qta
from datetime import datetime
import re
import json
from typing import List, Dict, Any, Optional

from core.team_collaboration import (
    get_collaboration_service, MessageType, TeamRole, Team, TeamMessage,
    AI_AGENT_IDS, AI_AGENT_NAMES
)
from core.user_management import get_user_manager


class AIAgentMentionCompleter(QCompleter):
    """Auto-completer for AI agent mentions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.collaboration_service = get_collaboration_service()
        self._update_model()
    
    def _update_model(self):
        """Update completion model with AI agents"""
        agents = self.collaboration_service.get_ai_agent_list()
        completions = []
        
        for agent in agents:
            # Add @mention completions
            completions.append(f"@{agent['type']}")
            completions.append(f"@{agent['name']}")
        
        model = QStringListModel(completions)
        self.setModel(model)
        self.setCaseSensitivity(Qt.CaseInsensitive)


class TeamChatMessage(QWidget):
    """Individual chat message widget with AI agent styling"""
    
    def __init__(self, message: TeamMessage, parent=None):
        super().__init__(parent)
        self.message = message
        self._create_ui()
    
    def _create_ui(self):
        """Create message UI with special styling for AI agents"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Message header
        header_layout = QHBoxLayout()
        
        # Sender info with AI agent icons
        sender_label = QLabel()
        is_ai_agent = self.message.sender_id in AI_AGENT_NAMES
        
        if is_ai_agent:
            # AI agent styling
            agent_icon = self._get_agent_icon()
            sender_text = f"{agent_icon} {self.message.sender_name}"
            sender_label.setText(sender_text)
            sender_label.setStyleSheet("""
                QLabel {
                    color: #8B5CF6;
                    font-weight: bold;
                    font-size: 13px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(139, 92, 246, 0.1), stop:1 rgba(139, 92, 246, 0.05));
                    padding: 2px 6px;
                    border-radius: 8px;
                    border-left: 3px solid #8B5CF6;
                }
            """)
        else:
            # Human user styling
            sender_label.setText(self.message.sender_name)
            sender_label.setStyleSheet("""
                QLabel {
                    color: #374151;
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
        
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        
        # Timestamp
        timestamp_label = QLabel(self.message.timestamp.strftime("%H:%M"))
        timestamp_label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        header_layout.addWidget(timestamp_label)
        
        layout.addLayout(header_layout)
        
        # Message content
        content_label = QLabel(self.message.content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        
        # Style based on message type
        if self.message.message_type == MessageType.AI_ALERT:
            content_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(239, 68, 68, 0.1), stop:1 rgba(239, 68, 68, 0.05));
                    padding: 8px;
                    border-radius: 6px;
                    border-left: 3px solid #EF4444;
                    color: #1F2937;
                }
            """)
        elif self.message.message_type == MessageType.AI_INSIGHT:
            content_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(59, 130, 246, 0.1), stop:1 rgba(59, 130, 246, 0.05));
                    padding: 8px;
                    border-radius: 6px;
                    border-left: 3px solid #3B82F6;
                    color: #1F2937;
                }
            """)
        elif is_ai_agent:
            content_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(139, 92, 246, 0.08), stop:1 rgba(139, 92, 246, 0.03));
                    padding: 8px;
                    border-radius: 6px;
                    color: #1F2937;
                }
            """)
        else:
            content_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    color: #1F2937;
                }
            """)
        
        layout.addWidget(content_label)
        
        # Message actions (reactions, etc.)
        if self.message.message_type in [MessageType.AI_ALERT, MessageType.AI_INSIGHT]:
            actions_layout = QHBoxLayout()
            
            # Quick action buttons for AI messages
            if "price" in self.message.content.lower():
                price_btn = QPushButton("📊 View Details")
                price_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 2px 6px; }")
                actions_layout.addWidget(price_btn)
            
            if "lead" in self.message.content.lower():
                lead_btn = QPushButton("👤 Open Lead")
                lead_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 2px 6px; }")
                actions_layout.addWidget(lead_btn)
            
            actions_layout.addStretch()
            layout.addLayout(actions_layout)
    
    def _get_agent_icon(self) -> str:
        """Get icon for AI agent type"""
        if "Market Monitor" in self.message.sender_name:
            return "🏠"
        elif "Lead Scorer" in self.message.sender_name:
            return "👥"
        elif "Property Watcher" in self.message.sender_name:
            return "👀"
        elif "Campaign Optimizer" in self.message.sender_name:
            return "📢"
        return "🤖"


class AIEnhancedTeamChat(QWidget):
    """AI-Enhanced team chat widget with agent integration"""
    
    message_sent = Signal(str, str)  # team_id, message
    ai_agent_mentioned = Signal(str, str, str)  # team_id, message, agent_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.collaboration_service = get_collaboration_service()
        self.user_manager = get_user_manager()
        self.current_team = None
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._refresh_messages)
        
        self._create_ui()
        self._setup_ai_integration()
    
    def _create_ui(self):
        """Create the enhanced chat UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header with AI status
        header_frame = QFrame()
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #7C3AED);
                border-radius: 8px 8px 0 0;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        # Team selector
        self.team_selector = QComboBox()
        self.team_selector.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_white.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.team_selector.currentTextChanged.connect(self._team_changed)
        header_layout.addWidget(QLabel("Team:"))
        header_layout.addWidget(self.team_selector)
        
        header_layout.addStretch()
        
        # AI agents status indicator
        self.ai_status_label = QLabel("🤖 4 AI Agents Active")
        self.ai_status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: rgba(255, 255, 255, 0.1);
                padding: 4px 8px;
                border-radius: 12px;
            }
        """)
        header_layout.addWidget(self.ai_status_label)
        
        layout.addWidget(header_frame)
        
        # Chat messages area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch()
        
        scroll_area.setWidget(self.messages_widget)
        layout.addWidget(scroll_area)
        
        # Message input area
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_frame.setStyleSheet("""
            QFrame {
                background: #F9FAFB;
                border-top: 1px solid #E5E7EB;
            }
        """)
        
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        
        # AI agents quick access
        ai_buttons_layout = QHBoxLayout()
        ai_buttons_layout.addWidget(QLabel("💬 Mention AI:"))
        
        for agent_type, agent_id in AI_AGENT_IDS.items():
            agent_name = AI_AGENT_NAMES[agent_id]
            btn = QPushButton(agent_name.split()[0])  # Just the emoji and first word
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(139, 92, 246, 0.1);
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    border-radius: 12px;
                    padding: 2px 8px;
                    font-size: 10px;
                    color: #8B5CF6;
                }
                QPushButton:hover {
                    background: rgba(139, 92, 246, 0.2);
                }
            """)
            btn.clicked.connect(lambda checked, t=agent_type: self._insert_agent_mention(t))
            ai_buttons_layout.addWidget(btn)
        
        ai_buttons_layout.addStretch()
        input_layout.addLayout(ai_buttons_layout)
        
        # Message input with mention support
        message_input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message... Use @agent_name to mention AI agents")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
                outline: none;
            }
        """)
        self.message_input.returnPressed.connect(self._send_message)
        
        # Set up AI agent mention auto-completion
        self.completer = AIAgentMentionCompleter()
        self.message_input.setCompleter(self.completer)
        
        message_input_layout.addWidget(self.message_input)
        
        # Send button
        send_btn = QPushButton("Send")
        send_btn.setIcon(qta.icon('fa5s.paper-plane', color='white'))
        send_btn.setStyleSheet("""
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7C3AED;
            }
        """)
        send_btn.clicked.connect(self._send_message)
        message_input_layout.addWidget(send_btn)
        
        input_layout.addLayout(message_input_layout)
        layout.addWidget(input_frame)
    
    def _setup_ai_integration(self):
        """Set up AI agent integration"""
        # Connect to colonel client if available
        try:
            from core.colonel_client import get_colonel_client
            colonel_client = get_colonel_client()
            self.collaboration_service.set_colonel_client(colonel_client)
        except Exception as e:
            print(f"Could not connect AI agents to collaboration: {e}")
        
        # Load teams
        self._load_teams()
        
        # Start auto-refresh for real-time messages
        self.auto_refresh_timer.start(3000)  # Refresh every 3 seconds
    
    def _load_teams(self):
        """Load available teams"""
        self.team_selector.clear()
        self.team_selector.addItem("Select Team", None)
        
        # Get user's teams
        if self.user_manager.current_user:
            user_teams = self.collaboration_service.get_user_teams(
                self.user_manager.current_user.user_id
            )
            
            for team in user_teams:
                self.team_selector.addItem(team.name, team.team_id)
    
    def _team_changed(self, team_name: str):
        """Handle team selection change"""
        team_id = self.team_selector.currentData()
        if team_id:
            self.current_team = team_id
            self._load_messages()
        else:
            self.current_team = None
            self._clear_messages()
    
    def _load_messages(self):
        """Load messages for current team"""
        if not self.current_team:
            return
        
        # Clear existing messages
        self._clear_messages()
        
        # Get team messages
        messages = self.collaboration_service.get_team_messages(self.current_team, limit=50)
        
        # Add messages to UI (reverse order for chronological display)
        for message in reversed(messages):
            self._add_message_widget(message)
    
    def _clear_messages(self):
        """Clear all message widgets"""
        while self.messages_layout.count() > 1:  # Keep the stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_message_widget(self, message: TeamMessage):
        """Add message widget to chat"""
        message_widget = TeamChatMessage(message)
        
        # Insert before the stretch item
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        
        # Auto-scroll to bottom
        QApplication.processEvents()  # Process the layout update
        scroll_area = self.messages_widget.parent().parent()
        if hasattr(scroll_area, 'verticalScrollBar'):
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().maximum()
            )
    
    def _send_message(self):
        """Send message to team chat"""
        if not self.current_team or not self.message_input.text().strip():
            return
        
        message_text = self.message_input.text().strip()
        
        # Check for AI agent mentions
        mentioned_agents = self._extract_ai_mentions(message_text)
        
        # Send message to team
        if self.user_manager.current_user:
            message = self.collaboration_service.send_message(
                team_id=self.current_team,
                sender_id=self.user_manager.current_user.user_id,
                sender_name=self.user_manager.current_user.full_name,
                message_type=MessageType.TEXT,
                content=message_text
            )
            
            if message:
                # Add to UI immediately
                self._add_message_widget(message)
                
                # Process AI mentions
                for agent_type in mentioned_agents:
                    self._process_ai_mention(message, agent_type)
        
        # Clear input
        self.message_input.clear()
        
        # Emit signal
        self.message_sent.emit(self.current_team, message_text)
    
    def _extract_ai_mentions(self, message_text: str) -> List[str]:
        """Extract AI agent mentions from message"""
        mentioned_agents = []
        
        # Look for @mentions
        mentions = re.findall(r'@(\w+)', message_text)
        
        for mention in mentions:
            # Check if mention matches an AI agent
            for agent_type, agent_id in AI_AGENT_IDS.items():
                agent_name = AI_AGENT_NAMES[agent_id]
                
                if (mention.lower() == agent_type.lower() or 
                    mention.lower() in agent_name.lower() or
                    agent_type.lower() in mention.lower()):
                    mentioned_agents.append(agent_type)
                    break
        
        return mentioned_agents
    
    def _process_ai_mention(self, message: TeamMessage, agent_type: str):
        """Process AI agent mention and generate response"""
        try:
            ai_response = self.collaboration_service.process_ai_mention(
                team_id=self.current_team,
                message=message,
                mentioned_agent=agent_type
            )
            
            if ai_response:
                # Add AI response to UI
                self._add_message_widget(ai_response)
                
                # Emit signal
                self.ai_agent_mentioned.emit(self.current_team, message.content, agent_type)
        
        except Exception as e:
            print(f"Error processing AI mention: {e}")
    
    def _insert_agent_mention(self, agent_type: str):
        """Insert AI agent mention into message input"""
        current_text = self.message_input.text()
        mention = f"@{agent_type} "
        
        # Insert at cursor position
        cursor_pos = self.message_input.cursorPosition()
        new_text = current_text[:cursor_pos] + mention + current_text[cursor_pos:]
        
        self.message_input.setText(new_text)
        self.message_input.setCursorPosition(cursor_pos + len(mention))
        self.message_input.setFocus()
    
    def _refresh_messages(self):
        """Refresh messages if team is selected"""
        if self.current_team:
            current_count = self.messages_layout.count() - 1  # Subtract stretch
            
            # Get latest messages
            messages = self.collaboration_service.get_team_messages(self.current_team, limit=50)
            
            # Check if there are new messages
            if len(messages) > current_count:
                # Add only new messages
                new_messages = messages[:len(messages) - current_count]
                for message in reversed(new_messages):
                    self._add_message_widget(message)
    
    def receive_ai_alert(self, agent_type: str, alert_message: str, priority: str = "normal"):
        """Receive AI alert from autonomous agents"""
        if self.current_team:
            # AI agents broadcast alerts to all teams automatically
            # This will be picked up by the auto-refresh
            pass