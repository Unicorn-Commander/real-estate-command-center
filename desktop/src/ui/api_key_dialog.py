"""
API Key Management Dialog - User-friendly interface for managing API keys
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTabWidget, QWidget, QFormLayout, QTextEdit,
    QMessageBox, QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import qtawesome as qta
from core.api_key_manager import api_key_manager
from core.settings_manager import settings_manager
import webbrowser

class APIKeyDialog(QDialog):
    """Dialog for managing API keys"""
    
    keys_updated = Signal()  # Emitted when keys are saved
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Management")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self.api_inputs = {}
        self.setup_ui()
        self.load_current_keys()
        
    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.key', color='#8B5CF6').pixmap(32, 32))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("<h2>API Key Management</h2>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Status summary
        self.status_label = QLabel()
        self.update_status_label()
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Info text
        info_text = QLabel(
            "Configure your API keys to enable various features. "
            "Your keys are stored securely and never shared."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_text)
        
        # Tab widget for different categories
        self.tabs = QTabWidget()
        
        # AI Services tab
        ai_widget = self.create_ai_tab()
        self.tabs.addTab(ai_widget, qta.icon('fa5s.robot'), "AI Services")
        
        # MLS Providers tab
        mls_widget = self.create_mls_tab()
        self.tabs.addTab(mls_widget, qta.icon('fa5s.home'), "MLS Providers")
        
        # Other Services tab (future expansion)
        # other_widget = self.create_other_tab()
        # self.tabs.addTab(other_widget, qta.icon('fa5s.plug'), "Other Services")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Selected Key")
        self.test_button.setIcon(qta.icon('fa5s.plug'))
        self.test_button.clicked.connect(self.test_selected_key)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.setIcon(qta.icon('fa5s.save'))
        self.save_button.clicked.connect(self.save_keys)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_ai_tab(self) -> QWidget:
        """Create the AI services tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area for multiple providers
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # OpenAI
        openai_group = self.create_api_key_group(
            'openai',
            'OpenAI (GPT-4, GPT-3.5)',
            'Powers AI conversations and analysis',
            'https://platform.openai.com/api-keys'
        )
        scroll_layout.addWidget(openai_group)
        
        # Anthropic
        anthropic_group = self.create_api_key_group(
            'anthropic',
            'Anthropic (Claude)',
            'Alternative AI provider for conversations',
            'https://console.anthropic.com/settings/keys'
        )
        scroll_layout.addWidget(anthropic_group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
        
    def create_mls_tab(self) -> QWidget:
        """Create the MLS providers tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area for multiple providers
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Bridge Interactive
        bridge_group = self.create_api_key_group(
            'bridge',
            'Bridge Interactive',
            'Comprehensive MLS data aggregator',
            'https://bridgeinteractive.com'
        )
        scroll_layout.addWidget(bridge_group)
        
        # MLSGrid
        mlsgrid_group = self.create_api_key_group(
            'mlsgrid',
            'MLSGrid',
            'Standardized MLS data across multiple regions',
            'https://www.mlsgrid.com'
        )
        scroll_layout.addWidget(mlsgrid_group)
        
        # RentSpree
        rentspree_group = self.create_api_key_group(
            'rentspree',
            'RentSpree',
            'Rental listings and tenant screening',
            'https://www.rentspree.com'
        )
        scroll_layout.addWidget(rentspree_group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
        
    def create_api_key_group(self, key_type: str, title: str, description: str, url: str) -> QGroupBox:
        """Create a group box for an API key"""
        config = api_key_manager.API_KEYS.get(key_type, {})
        
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 5px;")
        layout.addWidget(desc_label)
        
        # Input layout
        input_layout = QHBoxLayout()
        
        # Key input
        key_input = QLineEdit()
        key_input.setPlaceholderText(f"Enter your {title} API key...")
        key_input.setEchoMode(QLineEdit.Password)
        self.api_inputs[key_type] = key_input
        input_layout.addWidget(key_input)
        
        # Show/hide button
        show_button = QPushButton()
        show_button.setIcon(qta.icon('fa5s.eye'))
        show_button.setFixedWidth(30)
        show_button.setCheckable(True)
        show_button.toggled.connect(lambda checked: key_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        input_layout.addWidget(show_button)
        
        layout.addLayout(input_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Get key button
        get_key_button = QPushButton(f"Get {title} Key")
        get_key_button.setIcon(qta.icon('fa5s.external-link-alt'))
        get_key_button.clicked.connect(lambda: webbrowser.open(url))
        button_layout.addWidget(get_key_button)
        
        # Instructions button
        instructions_button = QPushButton("Setup Instructions")
        instructions_button.setIcon(qta.icon('fa5s.info-circle'))
        instructions_button.clicked.connect(lambda: self.show_instructions(key_type))
        button_layout.addWidget(instructions_button)
        
        button_layout.addStretch()
        
        # Status indicator
        self.update_key_status(key_type, key_input)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        
        return group
        
    def update_key_status(self, key_type: str, input_widget: QLineEdit):
        """Update the status indicator for a key"""
        has_key = bool(api_key_manager.get_api_key(key_type))
        if has_key:
            input_widget.setStyleSheet("QLineEdit { border: 2px solid #4CAF50; }")
        else:
            input_widget.setStyleSheet("QLineEdit { border: 1px solid #ccc; }")
            
    def show_instructions(self, key_type: str):
        """Show setup instructions for a specific API key"""
        config = api_key_manager.API_KEYS.get(key_type, {})
        if not config:
            return
            
        instructions = '\n'.join(config.get('setup_instructions', []))
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"{config['name']} Setup Instructions")
        msg.setText(f"<h3>How to get your {config['name']} API Key:</h3>")
        msg.setInformativeText(instructions)
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        
    def load_current_keys(self):
        """Load current API keys into the form"""
        for key_type, input_widget in self.api_inputs.items():
            current_key = api_key_manager.get_api_key(key_type)
            if current_key:
                input_widget.setText(current_key)
                
    def save_keys(self):
        """Save all API keys"""
        settings = settings_manager.get_all_settings()
        
        for key_type, input_widget in self.api_inputs.items():
            key_value = input_widget.text().strip()
            config = api_key_manager.API_KEYS.get(key_type, {})
            
            if key_value:
                # Save to settings
                path_parts = config['setting_path'].split('.')
                current = settings
                for i, part in enumerate(path_parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path_parts[-1]] = key_value
                
                # Also set in environment
                import os
                os.environ[config['env_var']] = key_value
            else:
                # Remove key if empty
                path_parts = config['setting_path'].split('.')
                current = settings
                for part in path_parts[:-1]:
                    if part not in current:
                        break
                    current = current[part]
                else:
                    if path_parts[-1] in current:
                        del current[path_parts[-1]]
                        
        # Save settings
        settings_manager.save_settings(settings)
        
        # Update UI
        self.update_status_label()
        self.keys_updated.emit()
        
        QMessageBox.information(self, "Success", "API keys saved successfully!")
        self.accept()
        
    def test_selected_key(self):
        """Test the selected API key"""
        current_tab = self.tabs.currentIndex()
        
        # Get the current key type based on focused input
        focused_key_type = None
        for key_type, input_widget in self.api_inputs.items():
            if input_widget.hasFocus():
                focused_key_type = key_type
                break
                
        if not focused_key_type:
            QMessageBox.warning(self, "No Key Selected", "Please click on an API key field to test it.")
            return
            
        key_value = self.api_inputs[focused_key_type].text().strip()
        if not key_value:
            QMessageBox.warning(self, "No Key", "Please enter an API key to test.")
            return
            
        # TODO: Implement actual API testing
        config = api_key_manager.API_KEYS.get(focused_key_type, {})
        QMessageBox.information(
            self, 
            "Test API Key", 
            f"Testing {config['name']} API key...\n\n"
            f"(Test functionality will be implemented based on the specific API)"
        )
        
    def update_status_label(self):
        """Update the status label showing key counts"""
        status = api_key_manager.get_api_key_status()
        configured = sum(1 for v in status.values() if v)
        total = len(status)
        
        if configured == total:
            self.status_label.setText(f"<b style='color: green;'>✓ All {total} keys configured</b>")
        elif configured == 0:
            self.status_label.setText(f"<b style='color: red;'>⚠ No keys configured</b>")
        else:
            self.status_label.setText(f"<b style='color: orange;'>⚠ {configured}/{total} keys configured</b>")