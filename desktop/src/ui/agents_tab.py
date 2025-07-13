"""
Agents Status Tab - Monitor and control autonomous AI agents
"""

import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QTextEdit, QSplitter, QHeaderView,
    QProgressBar, QComboBox, QSpinBox, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QColor, QBrush
import qtawesome as qta
from ui.modern_theme import get_brand_color


class AgentStatusWidget(QWidget):
    """Widget showing status of a single agent"""
    
    def __init__(self, agent_name: str, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Agent icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)
        
        # Agent name
        self.name_label = QLabel(self.agent_name)
        self.name_label.setMinimumWidth(150)
        font = QFont()
        font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Status indicator
        self.status_label = QLabel("Idle")
        self.status_label.setMinimumWidth(80)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {get_brand_color('gray_700')};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Task count
        self.task_label = QLabel("0 tasks")
        self.task_label.setMinimumWidth(60)
        layout.addWidget(self.task_label)
        
        # Control buttons
        self.start_button = QPushButton()
        self.start_button.setIcon(qta.icon('fa5s.play', color='green'))
        self.start_button.setToolTip("Start agent")
        self.start_button.setFixedSize(28, 28)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(qta.icon('fa5s.stop', color='red'))
        self.stop_button.setToolTip("Stop agent")
        self.stop_button.setFixedSize(28, 28)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        layout.addStretch()
    
    def update_status(self, status: str, task_count: int = 0):
        """Update agent status display"""
        self.status_label.setText(status.title())
        self.task_label.setText(f"{task_count} tasks")
        
        # Update status color
        color_map = {
            "idle": get_brand_color('gray_700'),
            "running": get_brand_color('success'),
            "sleeping": get_brand_color('info'),
            "error": get_brand_color('danger'),
            "stopped": get_brand_color('gray_800')
        }
        
        bg_color = color_map.get(status, get_brand_color('gray_700'))
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
            }}
        """)
        
        # Update buttons
        is_running = status in ["running", "sleeping"]
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        
        # Update icon
        icon_map = {
            "Market Monitor": "fa5s.chart-line",
            "Lead Scoring": "fa5s.user-check",
            "Property Watcher": "fa5s.eye",
            "Campaign Optimizer": "fa5s.bullhorn"
        }
        
        icon_name = icon_map.get(self.agent_name, "fa5s.robot")
        icon_color = "green" if is_running else "gray"
        icon = qta.icon(icon_name, color=icon_color)
        self.icon_label.setPixmap(icon.pixmap(24, 24))
    
    def update_progress(self, value: int, message: str = ""):
        """Update progress bar"""
        if value > 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
            if message:
                self.progress_bar.setFormat(f"{message} - {value}%")
        else:
            self.progress_bar.setVisible(False)


class AgentsTab(QWidget):
    """Tab for monitoring and controlling autonomous agents"""
    
    # Signals
    agent_action_requested = Signal(str, str)  # agent_name, action
    
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.agent_manager = colonel_client.get_agent_manager()
        self.agent_widgets = {}
        self.init_ui()
        
        # Connect to agent manager signals
        self._connect_signals()
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_agent_statuses)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("🤖 Autonomous AI Agents")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Global controls
        self.start_all_button = QPushButton("Start All Agents")
        self.start_all_button.setIcon(qta.icon('fa5s.play-circle', color='green'))
        self.start_all_button.clicked.connect(self.start_all_agents)
        header_layout.addWidget(self.start_all_button)
        
        self.stop_all_button = QPushButton("Stop All Agents")
        self.stop_all_button.setIcon(qta.icon('fa5s.stop-circle', color='red'))
        self.stop_all_button.clicked.connect(self.stop_all_agents)
        header_layout.addWidget(self.stop_all_button)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Agents status panel
        agents_panel = QGroupBox("Agent Status")
        agents_layout = QVBoxLayout(agents_panel)
        
        # Create agent status widgets
        agent_names = ["Market Monitor", "Lead Scoring", "Property Watcher", "Campaign Optimizer"]
        for agent_name in agent_names:
            widget = AgentStatusWidget(agent_name)
            widget.start_button.clicked.connect(lambda checked, name=agent_name: self.start_agent(name))
            widget.stop_button.clicked.connect(lambda checked, name=agent_name: self.stop_agent(name))
            self.agent_widgets[agent_name] = widget
            agents_layout.addWidget(widget)
        
        agents_layout.addStretch()
        splitter.addWidget(agents_panel)
        
        # Activity log and notifications
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # Activity log
        log_panel = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_panel)
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(200)
        log_layout.addWidget(self.activity_log)
        
        bottom_splitter.addWidget(log_panel)
        
        # Agent configurations
        config_panel = QGroupBox("Agent Configuration")
        config_layout = QVBoxLayout(config_panel)
        
        # Agent selector
        agent_select_layout = QHBoxLayout()
        agent_select_layout.addWidget(QLabel("Configure Agent:"))
        
        self.agent_selector = QComboBox()
        self.agent_selector.addItems(agent_names)
        self.agent_selector.currentTextChanged.connect(self.load_agent_config)
        agent_select_layout.addWidget(self.agent_selector)
        
        config_layout.addLayout(agent_select_layout)
        
        # Configuration options
        config_form_layout = QVBoxLayout()
        
        # Check interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check Interval (seconds):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(60, 3600)
        self.interval_spinbox.setSingleStep(60)
        self.interval_spinbox.setValue(300)
        interval_layout.addWidget(self.interval_spinbox)
        config_form_layout.addLayout(interval_layout)
        
        # Enable/disable
        self.enabled_checkbox = QCheckBox("Agent Enabled")
        self.enabled_checkbox.setChecked(True)
        config_form_layout.addWidget(self.enabled_checkbox)
        
        # Save button
        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_button.setIcon(qta.icon('fa5s.save'))
        self.save_config_button.clicked.connect(self.save_agent_config)
        config_form_layout.addWidget(self.save_config_button)
        
        config_layout.addLayout(config_form_layout)
        config_layout.addStretch()
        
        bottom_splitter.addWidget(config_panel)
        
        splitter.addWidget(bottom_splitter)
        layout.addWidget(splitter)
        
        # Initial status update
        self.refresh_agent_statuses()
    
    def _connect_signals(self):
        """Connect to agent manager signals"""
        self.agent_manager.agent_status_changed.connect(self.on_agent_status_changed)
        self.agent_manager.agent_notification.connect(self.on_agent_notification)
        self.agent_manager.agent_error.connect(self.on_agent_error)
        
        # Connect to individual agent signals
        for agent_name, agent in self.agent_manager.agents.items():
            agent.progress_update.connect(self.on_agent_progress)
    
    @Slot(str, str)
    def on_agent_status_changed(self, agent_name: str, status: str):
        """Handle agent status change"""
        if agent_name in self.agent_widgets:
            # Get task count
            agent = self.agent_manager.agents.get(agent_name)
            task_count = len(agent._tasks) if agent else 0
            
            self.agent_widgets[agent_name].update_status(status, task_count)
            self.log_activity(f"{agent_name}: Status changed to {status}")
    
    @Slot(str, str, str)
    def on_agent_notification(self, agent_name: str, notification_type: str, message: str):
        """Handle agent notification"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color code by type
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        color = color_map.get(notification_type, "black")
        
        formatted_message = f'<span style="color: {color}"><b>[{timestamp}] {agent_name}:</b> {message}</span>'
        self.activity_log.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    @Slot(str, str)
    def on_agent_error(self, agent_name: str, error: str):
        """Handle agent error"""
        self.on_agent_notification(agent_name, "error", f"Error: {error}")
    
    @Slot(str, int, str)
    def on_agent_progress(self, agent_name: str, percentage: int, message: str):
        """Handle agent progress update"""
        if agent_name in self.agent_widgets:
            self.agent_widgets[agent_name].update_progress(percentage, message)
    
    def refresh_agent_statuses(self):
        """Refresh status of all agents"""
        statuses = self.agent_manager.get_all_agent_statuses()
        
        for agent_name, status in statuses.items():
            if agent_name in self.agent_widgets:
                agent = self.agent_manager.agents.get(agent_name)
                task_count = len(agent._tasks) if agent else 0
                self.agent_widgets[agent_name].update_status(status, task_count)
    
    def start_agent(self, agent_name: str):
        """Start a specific agent"""
        self.agent_manager.start_agent(agent_name)
        self.log_activity(f"Starting {agent_name}...")
    
    def stop_agent(self, agent_name: str):
        """Stop a specific agent"""
        self.agent_manager.stop_agent(agent_name)
        self.log_activity(f"Stopping {agent_name}...")
    
    def start_all_agents(self):
        """Start all agents"""
        self.agent_manager.start_all_agents()
        self.log_activity("Starting all agents...")
    
    def stop_all_agents(self):
        """Stop all agents"""
        self.agent_manager.stop_all_agents()
        self.log_activity("Stopping all agents...")
    
    def load_agent_config(self, agent_name: str):
        """Load configuration for selected agent"""
        config = self.agent_manager.agent_configs.get(agent_name, {})
        self.interval_spinbox.setValue(config.get("check_interval", 300))
        self.enabled_checkbox.setChecked(config.get("enabled", True))
    
    def save_agent_config(self):
        """Save configuration for selected agent"""
        agent_name = self.agent_selector.currentText()
        
        config = {
            "enabled": self.enabled_checkbox.isChecked(),
            "check_interval": self.interval_spinbox.value()
        }
        
        self.agent_manager.update_agent_config(agent_name, config)
        self.log_activity(f"Configuration saved for {agent_name}")
    
    def log_activity(self, message: str):
        """Log an activity message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")
    
    def cleanup(self):
        """Cleanup when tab is closed"""
        self.update_timer.stop()