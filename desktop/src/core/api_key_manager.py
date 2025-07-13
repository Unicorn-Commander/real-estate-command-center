"""
API Key Manager - Centralized API key validation and error messaging
Provides consistent, user-friendly error messages for missing API keys
"""
import os
import logging
from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from core.settings_manager import settings_manager

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API keys and provides user-friendly error messages"""
    
    # API key configuration
    API_KEYS = {
        'openai': {
            'name': 'OpenAI',
            'env_var': 'OPENAI_API_KEY',
            'setting_path': 'ai.api_keys.openai',
            'purpose': 'AI assistant conversations',
            'setup_url': 'https://platform.openai.com/api-keys',
            'setup_instructions': [
                '1. Go to https://platform.openai.com/api-keys',
                '2. Sign in or create an account',
                '3. Click "Create new secret key"',
                '4. Copy the key (starts with "sk-")',
                '5. Paste it in Settings > AI Configuration'
            ]
        },
        'anthropic': {
            'name': 'Anthropic (Claude)',
            'env_var': 'ANTHROPIC_API_KEY',
            'setting_path': 'ai.api_keys.anthropic',
            'purpose': 'Alternative AI assistant',
            'setup_url': 'https://console.anthropic.com/settings/keys',
            'setup_instructions': [
                '1. Go to https://console.anthropic.com',
                '2. Sign in or create an account',
                '3. Go to Settings > API Keys',
                '4. Click "Create Key"',
                '5. Copy the key and paste in Settings'
            ]
        },
        'bridge': {
            'name': 'Bridge Interactive',
            'env_var': 'BRIDGE_API_KEY',
            'setting_path': 'integrations.mls_providers.bridge_interactive.api_key',
            'purpose': 'MLS property listings',
            'setup_url': 'https://bridgeinteractive.com',
            'setup_instructions': [
                '1. Contact Bridge Interactive for access',
                '2. Request API credentials',
                '3. You\'ll receive an API key via email',
                '4. Paste it in Settings > Integrations'
            ]
        },
        'mlsgrid': {
            'name': 'MLSGrid',
            'env_var': 'MLSGRID_API_KEY',
            'setting_path': 'integrations.mls_providers.mlsgrid.api_key',
            'purpose': 'MLS property data aggregation',
            'setup_url': 'https://www.mlsgrid.com',
            'setup_instructions': [
                '1. Visit https://www.mlsgrid.com',
                '2. Click "Get Started"',
                '3. Complete the application process',
                '4. API key will be provided after approval',
                '5. Add it in Settings > Integrations'
            ]
        },
        'rentspree': {
            'name': 'RentSpree',
            'env_var': 'RENTSPREE_API_KEY',
            'setting_path': 'integrations.mls_providers.rentspree.api_key',
            'purpose': 'Rental listings and tenant screening',
            'setup_url': 'https://www.rentspree.com',
            'setup_instructions': [
                '1. Sign up at https://www.rentspree.com',
                '2. Go to Account Settings > API',
                '3. Generate a new API key',
                '4. Copy and paste in Settings'
            ]
        },
        'deepseek': {
            'name': 'DeepSeek',
            'env_var': 'DEEPSEEK_API_KEY',
            'setting_path': 'ai.api_keys.deepseek',
            'purpose': 'Cost-effective AI with excellent performance',
            'setup_url': 'https://platform.deepseek.com',
            'setup_instructions': [
                '1. Go to https://platform.deepseek.com',
                '2. Sign up or login to your account',
                '3. Navigate to API Keys section',
                '4. Create a new API key',
                '5. Copy and paste in Settings > AI Configuration'
            ]
        },
        'groq': {
            'name': 'Groq',
            'env_var': 'GROQ_API_KEY',
            'setting_path': 'ai.api_keys.groq',
            'purpose': 'Ultra-fast AI inference with LPU technology',
            'setup_url': 'https://console.groq.com',
            'setup_instructions': [
                '1. Go to https://console.groq.com',
                '2. Create an account or sign in',
                '3. Navigate to API Keys',
                '4. Generate a new API key',
                '5. Copy and paste in Settings > AI Configuration'
            ]
        },
        'xai': {
            'name': 'xAI (Grok)',
            'env_var': 'XAI_API_KEY',
            'setting_path': 'ai.api_keys.xai',
            'purpose': 'Advanced AI with real-time web search',
            'setup_url': 'https://console.x.ai',
            'setup_instructions': [
                '1. Go to https://console.x.ai',
                '2. Sign up or login (X Premium required)',
                '3. Navigate to API Keys section',
                '4. Create a new API key',
                '5. Copy and paste in Settings > AI Configuration'
            ]
        },
        'openrouter': {
            'name': 'OpenRouter',
            'env_var': 'OPENROUTER_API_KEY',
            'setting_path': 'ai.api_keys.openrouter',
            'purpose': 'Access 400+ AI models through one API',
            'setup_url': 'https://openrouter.ai',
            'setup_instructions': [
                '1. Go to https://openrouter.ai',
                '2. Sign up for an account',
                '3. Navigate to Keys in your dashboard',
                '4. Create a new API key',
                '5. Copy and paste in Settings > AI Configuration'
            ]
        }
    }
    
    def __init__(self):
        self.settings = settings_manager
        self._missing_keys_cache = set()
        
    def get_api_key(self, key_type: str) -> Optional[str]:
        """Get API key from environment or settings"""
        if key_type not in self.API_KEYS:
            logger.warning(f"Unknown API key type: {key_type}")
            return None
            
        config = self.API_KEYS[key_type]
        
        # Try environment variable first
        api_key = os.environ.get(config['env_var'])
        
        # Try settings if not in environment
        if not api_key:
            parts = config['setting_path'].split('.')
            settings = self.settings.get_all_settings()
            value = settings
            for part in parts:
                value = value.get(part, {})
                if not isinstance(value, dict) and part != parts[-1]:
                    value = None
                    break
            if isinstance(value, str) and value:
                api_key = value
                
        return api_key if api_key else None
        
    def check_api_key(self, key_type: str, show_dialog: bool = True) -> bool:
        """Check if API key exists and show user-friendly error if missing"""
        api_key = self.get_api_key(key_type)
        
        if api_key:
            return True
            
        # Only show dialog once per session for each key
        if key_type not in self._missing_keys_cache and show_dialog:
            self._missing_keys_cache.add(key_type)
            self.show_missing_key_dialog(key_type)
            
        return False
        
    def show_missing_key_dialog(self, key_type: str):
        """Show a user-friendly dialog for missing API key"""
        if key_type not in self.API_KEYS:
            return
            
        config = self.API_KEYS[key_type]
        
        dialog = QDialog()
        dialog.setWindowTitle(f"{config['name']} API Key Required")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h3>{config['name']} API Key Not Found</h3>")
        layout.addWidget(header)
        
        # Purpose
        purpose_label = QLabel(f"<b>Purpose:</b> {config['purpose']}")
        layout.addWidget(purpose_label)
        
        # Instructions
        instructions_label = QLabel("<b>Setup Instructions:</b>")
        layout.addWidget(instructions_label)
        
        instructions_text = QTextEdit()
        instructions_text.setPlainText('\n'.join(config['setup_instructions']))
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(150)
        layout.addWidget(instructions_text)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        open_settings_btn = QPushButton("Open Settings")
        open_settings_btn.clicked.connect(lambda: self._open_settings(dialog))
        button_layout.addWidget(open_settings_btn)
        
        if config.get('setup_url'):
            visit_site_btn = QPushButton(f"Visit {config['name']} Website")
            visit_site_btn.clicked.connect(lambda: self._open_url(config['setup_url']))
            button_layout.addWidget(visit_site_btn)
            
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()
        
    def _open_settings(self, dialog):
        """Open settings dialog"""
        dialog.accept()
        # Emit signal or call method to open settings
        # This will be connected in main window
        
    def _open_url(self, url: str):
        """Open URL in browser"""
        import webbrowser
        webbrowser.open(url)
        
    def get_missing_keys(self) -> List[Tuple[str, Dict]]:
        """Get list of all missing API keys"""
        missing = []
        for key_type, config in self.API_KEYS.items():
            if not self.get_api_key(key_type):
                missing.append((key_type, config))
        return missing
        
    def get_configured_keys(self) -> List[Tuple[str, Dict]]:
        """Get list of all configured API keys"""
        configured = []
        for key_type, config in self.API_KEYS.items():
            if self.get_api_key(key_type):
                configured.append((key_type, config))
        return configured
        
    def get_api_key_status(self) -> Dict[str, bool]:
        """Get status of all API keys"""
        status = {}
        for key_type in self.API_KEYS:
            status[key_type] = bool(self.get_api_key(key_type))
        return status
        
    def show_api_key_summary(self):
        """Show a summary of API key status"""
        missing = self.get_missing_keys()
        configured = self.get_configured_keys()
        
        msg = "<h3>API Key Status</h3>"
        
        if configured:
            msg += "<b>✅ Configured:</b><ul>"
            for key_type, config in configured:
                msg += f"<li>{config['name']}</li>"
            msg += "</ul>"
            
        if missing:
            msg += "<b>⚠️ Missing:</b><ul>"
            for key_type, config in missing:
                msg += f"<li>{config['name']} - {config['purpose']}</li>"
            msg += "</ul>"
            msg += "<p>Click 'Open Settings' to add missing API keys.</p>"
        else:
            msg += "<p>All API keys are configured!</p>"
            
        msgbox = QMessageBox()
        msgbox.setWindowTitle("API Key Status")
        msgbox.setText(msg)
        msgbox.setTextFormat(Qt.RichText)
        
        if missing:
            msgbox.addButton("Open Settings", QMessageBox.AcceptRole)
            msgbox.addButton("Close", QMessageBox.RejectRole)
        else:
            msgbox.addButton("OK", QMessageBox.AcceptRole)
            
        if msgbox.exec() == 0 and missing:
            # Open settings dialog
            pass

# Global instance
api_key_manager = APIKeyManager()