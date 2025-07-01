"""
Enhanced Settings Dialog for Real Estate Command Center
Supports MLS providers, AI backends, and application configuration
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QWidget, QFormLayout, QLineEdit, QComboBox, 
                               QDialogButtonBox, QGroupBox, QCheckBox, QSpinBox,
                               QTextEdit, QLabel, QPushButton, QFileDialog,
                               QScrollArea, QMessageBox)
from PySide6.QtCore import Qt, Signal
import json
import os

class EnhancedSettingsDialog(QDialog):
    """Comprehensive settings dialog for all system configuration"""
    
    settings_changed = Signal(dict)  # Emit when settings change
    
    def __init__(self, current_settings: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Real Estate Command Center - Settings')
        self.setModal(True)
        self.resize(800, 600)
        
        # Default settings
        self.default_settings = {
            # MLS Provider Settings
            'mls_providers': {
                'bridge_api_key': '',
                'mlsgrid_api_key': '',
                'rentspree_api_key': '',
                'estated_api_key': '',
                'attom_api_key': '',
                'preferred_provider': 'bridge',
                'use_multiple_providers': True,
                'rate_limit_seconds': 1
            },
            # AI Backend Settings
            'ai_backend': {
                'backend_type': 'ollama',  # 'ollama', 'openai', 'open_interpreter'
                'openai_api_key': '',
                'ollama_url': 'http://localhost:11434',
                'open_interpreter_mode': 'local',
                'custom_models': {
                    'property_analyst': 'qwen2.5vl:q4_k_m',
                    'market_researcher': 'qwen3:q4_k_m', 
                    'lead_manager': 'gemma3:4b-q4_k_m',
                    'marketing_expert': 'gemma3:4b-q4_k_m'
                }
            },
            # Public Data Settings
            'public_data': {
                'enable_scraping': True,
                'respect_robots_txt': True,
                'rate_limit_seconds': 2,
                'max_retries': 3,
                'preferred_counties': ['King', 'Multnomah', 'Los Angeles', 'Harris']
            },
            # Application Settings
            'application': {
                'theme': 'dark_amber.xml',
                'auto_save_settings': True,
                'debug_mode': False,
                'data_cache_enabled': True,
                'cache_expiry_hours': 24
            }
        }
        
        # Merge with current settings
        self.settings = self.default_settings.copy()
        if current_settings:
            self._merge_settings(self.settings, current_settings)
        
        self.init_ui()
        self.load_settings_to_ui()
    
    def _merge_settings(self, default: dict, current: dict):
        """Recursively merge current settings with defaults"""
        for key, value in current.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_mls_tab()
        self.create_ai_tab()
        self.create_public_data_tab()
        self.create_application_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Test connections button
        self.test_button = QPushButton('Test Connections')
        self.test_button.clicked.connect(self.test_connections)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        # Import/Export buttons
        import_button = QPushButton('Import Settings')
        import_button.clicked.connect(self.import_settings)
        button_layout.addWidget(import_button)
        
        export_button = QPushButton('Export Settings')
        export_button.clicked.connect(self.export_settings)
        button_layout.addWidget(export_button)
        
        # Standard buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def create_mls_tab(self):
        """Create MLS providers configuration tab"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout(widget)
        
        # API Keys Group
        api_group = QGroupBox('MLS Provider API Keys')
        api_layout = QFormLayout(api_group)
        
        # Bridge Interactive
        self.bridge_key_edit = QLineEdit()
        self.bridge_key_edit.setEchoMode(QLineEdit.Password)
        self.bridge_key_edit.setPlaceholderText('Contact your local MLS for access (FREE)')
        api_layout.addRow('Bridge Interactive API Key:', self.bridge_key_edit)
        
        # Estated Public Records
        self.estated_key_edit = QLineEdit()
        self.estated_key_edit.setEchoMode(QLineEdit.Password)
        self.estated_key_edit.setPlaceholderText('Free tier: 1,000 requests/month')
        api_layout.addRow('Estated Public Records API Key:', self.estated_key_edit)
        
        # MLS Grid
        self.mlsgrid_key_edit = QLineEdit()
        self.mlsgrid_key_edit.setEchoMode(QLineEdit.Password)
        self.mlsgrid_key_edit.setPlaceholderText('RESO compliant (~$20-50/month)')
        api_layout.addRow('MLS Grid API Key:', self.mlsgrid_key_edit)
        
        # RentSpree
        self.rentspree_key_edit = QLineEdit()
        self.rentspree_key_edit.setEchoMode(QLineEdit.Password)
        self.rentspree_key_edit.setPlaceholderText('Contact through your MLS benefits')
        api_layout.addRow('RentSpree API Key:', self.rentspree_key_edit)
        
        # ATTOM Data
        self.attom_key_edit = QLineEdit()
        self.attom_key_edit.setEchoMode(QLineEdit.Password)
        self.attom_key_edit.setPlaceholderText('Enterprise pricing')
        api_layout.addRow('ATTOM Data API Key:', self.attom_key_edit)
        
        layout.addWidget(api_group)
        
        # Provider Configuration Group
        config_group = QGroupBox('Provider Configuration')
        config_layout = QFormLayout(config_group)
        
        # Preferred provider
        self.preferred_provider_combo = QComboBox()
        self.preferred_provider_combo.addItems(['bridge', 'estated', 'mlsgrid', 'rentspree', 'attom'])
        config_layout.addRow('Preferred Provider:', self.preferred_provider_combo)
        
        # Use multiple providers
        self.use_multiple_checkbox = QCheckBox('Use Multiple Providers (Recommended)')
        self.use_multiple_checkbox.setToolTip('Enables data aggregation from multiple sources for better coverage')
        config_layout.addRow('Multi-Provider Mode:', self.use_multiple_checkbox)
        
        # Rate limiting
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 10)
        self.rate_limit_spin.setSuffix(' seconds')
        self.rate_limit_spin.setToolTip('Minimum time between API requests to avoid rate limiting')
        config_layout.addRow('Rate Limit:', self.rate_limit_spin)
        
        layout.addWidget(config_group)
        
        # Cost Information
        cost_group = QGroupBox('Cost Information & Recommendations')
        cost_layout = QVBoxLayout(cost_group)
        
        cost_text = QLabel('''
<b>FREE Options (Recommended Start):</b>
• Bridge Interactive: FREE (requires MLS approval)
• Estated Public Records: FREE tier (1,000 requests/month)  
• Public Records Scraping: Always FREE

<b>Paid Options:</b>
• MLS Grid: $20-50/month (RESO compliant)
• RentSpree: Varies (rental-focused)
• ATTOM Data: $$$ (enterprise)

<b>Recommendation:</b> Start with Bridge Interactive + Estated + Public Records for a completely free setup.
        ''')
        cost_text.setWordWrap(True)
        cost_layout.addWidget(cost_text)
        
        layout.addWidget(cost_group)
        
        layout.addStretch()
        self.tab_widget.addTab(scroll, 'MLS Providers')
    
    def create_ai_tab(self):
        """Create AI backend configuration tab"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout(widget)
        
        # Backend Selection Group
        backend_group = QGroupBox('AI Backend Selection')
        backend_layout = QFormLayout(backend_group)
        
        self.ai_backend_combo = QComboBox()
        self.ai_backend_combo.addItems(['ollama', 'openai', 'open_interpreter', 'real_estate_interpreter'])
        self.ai_backend_combo.currentTextChanged.connect(self.on_ai_backend_changed)
        backend_layout.addRow('AI Backend:', self.ai_backend_combo)
        
        layout.addWidget(backend_group)
        
        # Ollama Configuration
        self.ollama_group = QGroupBox('Ollama Configuration')
        ollama_layout = QFormLayout(self.ollama_group)
        
        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setPlaceholderText('http://localhost:11434')
        ollama_layout.addRow('Ollama URL:', self.ollama_url_edit)
        
        layout.addWidget(self.ollama_group)
        
        # OpenAI Configuration
        self.openai_group = QGroupBox('OpenAI Configuration')
        openai_layout = QFormLayout(self.openai_group)
        
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.Password)
        self.openai_key_edit.setPlaceholderText('sk-...')
        openai_layout.addRow('OpenAI API Key:', self.openai_key_edit)
        
        layout.addWidget(self.openai_group)
        
        # Open Interpreter Configuration
        self.open_interpreter_group = QGroupBox('Open Interpreter Configuration')
        interpreter_layout = QFormLayout(self.open_interpreter_group)
        
        self.interpreter_mode_combo = QComboBox()
        self.interpreter_mode_combo.addItems(['local', 'hosted', 'custom'])
        interpreter_layout.addRow('Mode:', self.interpreter_mode_combo)
        
        layout.addWidget(self.open_interpreter_group)
        
        # Real Estate Interpreter Configuration
        self.re_interpreter_group = QGroupBox('Real Estate Interpreter (Integrated Colonel)')
        re_interpreter_layout = QFormLayout(self.re_interpreter_group)
        
        re_info_text = QLabel('''
<b>Real Estate Interpreter Features:</b>
• Integrated tool calling for property analysis
• Direct MLS and public data access
• Safe code execution for calculations
• Professional report generation
• No external dependencies

This is the recommended backend for real estate workflows.
        ''')
        re_info_text.setWordWrap(True)
        re_interpreter_layout.addWidget(re_info_text)
        
        layout.addWidget(self.re_interpreter_group)
        
        # Model Configuration
        models_group = QGroupBox('AI Model Configuration')
        models_layout = QFormLayout(models_group)
        
        self.property_analyst_edit = QLineEdit()
        self.property_analyst_edit.setPlaceholderText('qwen2.5vl:q4_k_m')
        models_layout.addRow('Property Analyst Model:', self.property_analyst_edit)
        
        self.market_researcher_edit = QLineEdit()
        self.market_researcher_edit.setPlaceholderText('qwen3:q4_k_m')
        models_layout.addRow('Market Researcher Model:', self.market_researcher_edit)
        
        self.lead_manager_edit = QLineEdit()
        self.lead_manager_edit.setPlaceholderText('gemma3:4b-q4_k_m')
        models_layout.addRow('Lead Manager Model:', self.lead_manager_edit)
        
        self.marketing_expert_edit = QLineEdit()
        self.marketing_expert_edit.setPlaceholderText('gemma3:4b-q4_k_m')
        models_layout.addRow('Marketing Expert Model:', self.marketing_expert_edit)
        
        layout.addWidget(models_group)
        
        # AI Backend Information
        ai_info_group = QGroupBox('Backend Information')
        ai_info_layout = QVBoxLayout(ai_info_group)
        
        ai_info_text = QLabel('''
<b>Real Estate Interpreter (Recommended):</b> Integrated Colonel fork with tool calling, no external deps
<b>Ollama:</b> Local AI models, complete privacy, no API costs
<b>OpenAI:</b> Hosted API, excellent quality, pay-per-use ($0.002/1K tokens)
<b>Open Interpreter:</b> Direct integration, can execute code, powerful but requires caution

<b>For real estate workflows:</b> Use Real Estate Interpreter for best integration.
        ''')
        ai_info_text.setWordWrap(True)
        ai_info_layout.addWidget(ai_info_text)
        
        layout.addWidget(ai_info_group)
        
        layout.addStretch()
        self.tab_widget.addTab(scroll, 'AI Backend')
    
    def create_public_data_tab(self):
        """Create public data scraping configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Public Data Scraping Group
        scraping_group = QGroupBox('Public Records Scraping')
        scraping_layout = QFormLayout(scraping_group)
        
        self.enable_scraping_checkbox = QCheckBox('Enable Public Records Scraping')
        self.enable_scraping_checkbox.setToolTip('Scrape government property records (always legal)')
        scraping_layout.addRow('Enable Scraping:', self.enable_scraping_checkbox)
        
        self.respect_robots_checkbox = QCheckBox('Respect robots.txt')
        self.respect_robots_checkbox.setToolTip('Check robots.txt before scraping (recommended)')
        scraping_layout.addRow('Robots.txt Compliance:', self.respect_robots_checkbox)
        
        self.scraping_rate_limit_spin = QSpinBox()
        self.scraping_rate_limit_spin.setRange(1, 30)
        self.scraping_rate_limit_spin.setSuffix(' seconds')
        self.scraping_rate_limit_spin.setToolTip('Delay between scraping requests for respectful data gathering')
        scraping_layout.addRow('Scraping Rate Limit:', self.scraping_rate_limit_spin)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(1, 10)
        self.max_retries_spin.setToolTip('Maximum retry attempts for failed requests')
        scraping_layout.addRow('Max Retries:', self.max_retries_spin)
        
        layout.addWidget(scraping_group)
        
        # Preferred Counties
        counties_group = QGroupBox('Preferred Counties (for specific scrapers)')
        counties_layout = QVBoxLayout(counties_group)
        
        counties_text = QLabel('Enter counties where you frequently work (comma-separated):')
        counties_layout.addWidget(counties_text)
        
        self.preferred_counties_edit = QLineEdit()
        self.preferred_counties_edit.setPlaceholderText('King, Multnomah, Los Angeles, Harris')
        counties_layout.addWidget(self.preferred_counties_edit)
        
        layout.addWidget(counties_group)
        
        # Legal Information
        legal_group = QGroupBox('Legal Information')
        legal_layout = QVBoxLayout(legal_group)
        
        legal_text = QLabel('''
<b>What We Scrape (100% Legal):</b>
• County Assessor Records (public data)
• Property Tax Records (government databases)
• Deed and Transfer Records (public records)
• US Census Data (public domain)

<b>Best Practices:</b>
• Rate limiting implemented for respectful scraping
• Robots.txt compliance checking
• Focus on government/public data sources only
• No private or copyrighted data collection

<b>Note:</b> All scraped data comes from legally accessible public records.
        ''')
        legal_text.setWordWrap(True)
        legal_layout.addWidget(legal_text)
        
        layout.addWidget(legal_group)
        
        layout.addStretch()
        self.tab_widget.addTab(widget, 'Public Data')
    
    def create_application_tab(self):
        """Create general application settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Appearance Group
        appearance_group = QGroupBox('Appearance')
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        themes = ['modern', 'dark_amber.xml', 'light_blue.xml', 'dark_light.xml', 'light_pink.xml']
        self.theme_combo.addItems(themes)
        appearance_layout.addRow('Theme:', self.theme_combo)
        
        layout.addWidget(appearance_group)
        
        # Data Management Group
        data_group = QGroupBox('Data Management')
        data_layout = QFormLayout(data_group)
        
        self.auto_save_checkbox = QCheckBox('Auto-save settings on changes')
        data_layout.addRow('Auto-save:', self.auto_save_checkbox)
        
        self.cache_enabled_checkbox = QCheckBox('Enable data caching')
        self.cache_enabled_checkbox.setToolTip('Cache API responses to reduce redundant requests')
        data_layout.addRow('Data Caching:', self.cache_enabled_checkbox)
        
        self.cache_expiry_spin = QSpinBox()
        self.cache_expiry_spin.setRange(1, 168)  # 1 hour to 1 week
        self.cache_expiry_spin.setSuffix(' hours')
        self.cache_expiry_spin.setToolTip('How long to keep cached data')
        data_layout.addRow('Cache Expiry:', self.cache_expiry_spin)
        
        layout.addWidget(data_group)
        
        # Developer Group
        dev_group = QGroupBox('Developer Options')
        dev_layout = QFormLayout(dev_group)
        
        self.debug_mode_checkbox = QCheckBox('Enable debug mode')
        self.debug_mode_checkbox.setToolTip('Show additional logging and debug information')
        dev_layout.addRow('Debug Mode:', self.debug_mode_checkbox)
        
        layout.addWidget(dev_group)
        
        layout.addStretch()
        self.tab_widget.addTab(widget, 'Application')
    
    def on_ai_backend_changed(self, backend):
        """Handle AI backend selection changes"""
        self.ollama_group.setVisible(backend == 'ollama')
        self.openai_group.setVisible(backend == 'openai')
        self.open_interpreter_group.setVisible(backend == 'open_interpreter')
        self.re_interpreter_group.setVisible(backend == 'real_estate_interpreter')
    
    def load_settings_to_ui(self):
        """Load current settings into UI controls"""
        # MLS settings
        mls = self.settings['mls_providers']
        self.bridge_key_edit.setText(mls.get('bridge_api_key', ''))
        self.estated_key_edit.setText(mls.get('estated_api_key', ''))
        self.mlsgrid_key_edit.setText(mls.get('mlsgrid_api_key', ''))
        self.rentspree_key_edit.setText(mls.get('rentspree_api_key', ''))
        self.attom_key_edit.setText(mls.get('attom_api_key', ''))
        self.preferred_provider_combo.setCurrentText(mls.get('preferred_provider', 'bridge'))
        self.use_multiple_checkbox.setChecked(mls.get('use_multiple_providers', True))
        self.rate_limit_spin.setValue(mls.get('rate_limit_seconds', 1))
        
        # AI settings
        ai = self.settings['ai_backend']
        self.ai_backend_combo.setCurrentText(ai.get('backend_type', 'ollama'))
        self.openai_key_edit.setText(ai.get('openai_api_key', ''))
        self.ollama_url_edit.setText(ai.get('ollama_url', 'http://localhost:11434'))
        self.interpreter_mode_combo.setCurrentText(ai.get('open_interpreter_mode', 'local'))
        
        models = ai.get('custom_models', {})
        self.property_analyst_edit.setText(models.get('property_analyst', 'qwen2.5vl:q4_k_m'))
        self.market_researcher_edit.setText(models.get('market_researcher', 'qwen3:q4_k_m'))
        self.lead_manager_edit.setText(models.get('lead_manager', 'gemma3:4b-q4_k_m'))
        self.marketing_expert_edit.setText(models.get('marketing_expert', 'gemma3:4b-q4_k_m'))
        
        # Public data settings
        public = self.settings['public_data']
        self.enable_scraping_checkbox.setChecked(public.get('enable_scraping', True))
        self.respect_robots_checkbox.setChecked(public.get('respect_robots_txt', True))
        self.scraping_rate_limit_spin.setValue(public.get('rate_limit_seconds', 2))
        self.max_retries_spin.setValue(public.get('max_retries', 3))
        self.preferred_counties_edit.setText(', '.join(public.get('preferred_counties', [])))
        
        # Application settings
        app = self.settings['application']
        self.theme_combo.setCurrentText(app.get('theme', 'modern'))
        self.auto_save_checkbox.setChecked(app.get('auto_save_settings', True))
        self.debug_mode_checkbox.setChecked(app.get('debug_mode', False))
        self.cache_enabled_checkbox.setChecked(app.get('data_cache_enabled', True))
        self.cache_expiry_spin.setValue(app.get('cache_expiry_hours', 24))
        
        # Update visibility
        self.on_ai_backend_changed(self.ai_backend_combo.currentText())
    
    def get_settings_from_ui(self) -> dict:
        """Extract settings from UI controls"""
        settings = {
            'mls_providers': {
                'bridge_api_key': self.bridge_key_edit.text().strip(),
                'estated_api_key': self.estated_key_edit.text().strip(),
                'mlsgrid_api_key': self.mlsgrid_key_edit.text().strip(),
                'rentspree_api_key': self.rentspree_key_edit.text().strip(),
                'attom_api_key': self.attom_key_edit.text().strip(),
                'preferred_provider': self.preferred_provider_combo.currentText(),
                'use_multiple_providers': self.use_multiple_checkbox.isChecked(),
                'rate_limit_seconds': self.rate_limit_spin.value()
            },
            'ai_backend': {
                'backend_type': self.ai_backend_combo.currentText(),
                'openai_api_key': self.openai_key_edit.text().strip(),
                'ollama_url': self.ollama_url_edit.text().strip(),
                'open_interpreter_mode': self.interpreter_mode_combo.currentText(),
                'custom_models': {
                    'property_analyst': self.property_analyst_edit.text().strip(),
                    'market_researcher': self.market_researcher_edit.text().strip(),
                    'lead_manager': self.lead_manager_edit.text().strip(),
                    'marketing_expert': self.marketing_expert_edit.text().strip(),
                    'real_estate_agent': self.real_estate_agent_edit.text().strip()
                }
            },
            'public_data': {
                'enable_scraping': self.enable_scraping_checkbox.isChecked(),
                'respect_robots_txt': self.respect_robots_checkbox.isChecked(),
                'rate_limit_seconds': self.scraping_rate_limit_spin.value(),
                'max_retries': self.max_retries_spin.value(),
                'preferred_counties': [c.strip() for c in self.preferred_counties_edit.text().split(',') if c.strip()]
            },
            'application': {
                'theme': self.theme_combo.currentText(),
                'auto_save_settings': self.auto_save_checkbox.isChecked(),
                'debug_mode': self.debug_mode_checkbox.isChecked(),
                'data_cache_enabled': self.cache_enabled_checkbox.isChecked(),
                'cache_expiry_hours': self.cache_expiry_spin.value()
            }
        }
        return settings
    
    def test_connections(self):
        """Test all configured connections"""
        settings = self.get_settings_from_ui()
        
        # Test MLS connections
        from core.mls_client_enhanced import create_mls_client
        
        results = []
        
        # Test each provider with API key
        providers = [
            ('bridge', settings['mls_providers']['bridge_api_key']),
            ('estated', settings['mls_providers']['estated_api_key']),
            ('mlsgrid', settings['mls_providers']['mlsgrid_api_key']),
            ('rentspree', settings['mls_providers']['rentspree_api_key']),
            ('attom', settings['mls_providers']['attom_api_key'])
        ]
        
        for provider, api_key in providers:
            if api_key:
                os.environ[f'{provider.upper()}_API_KEY'] = api_key
                try:
                    client = create_mls_client(provider)
                    status = client.test_connection()
                    if status['connection_status'] == 'success':
                        results.append(f"✅ {status['provider_name']}: Connected")
                    else:
                        results.append(f"❌ {status['provider_name']}: {status['message']}")
                except Exception as e:
                    results.append(f"❌ {provider.title()}: {str(e)}")
            else:
                results.append(f"⚠️ {provider.title()}: No API key provided")
        
        # Test AI backend
        ai_backend = settings['ai_backend']['backend_type']
        if ai_backend == 'openai' and settings['ai_backend']['openai_api_key']:
            try:
                import openai
                client = openai.OpenAI(api_key=settings['ai_backend']['openai_api_key'])
                client.models.list()
                results.append("✅ OpenAI: Connected")
            except Exception as e:
                results.append(f"❌ OpenAI: {str(e)}")
        elif ai_backend == 'ollama':
            try:
                import requests
                response = requests.get(f"{settings['ai_backend']['ollama_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    results.append("✅ Ollama: Connected")
                else:
                    results.append(f"❌ Ollama: HTTP {response.status_code}")
            except Exception as e:
                results.append(f"❌ Ollama: {str(e)}")
        
        # Show results
        QMessageBox.information(self, 'Connection Test Results', '\n'.join(results))
    
    def import_settings(self):
        """Import settings from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Settings', '', 'JSON Files (*.json)'
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)
                self._merge_settings(self.settings, imported_settings)
                self.load_settings_to_ui()
                QMessageBox.information(self, 'Success', 'Settings imported successfully!')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to import settings: {str(e)}')
    
    def export_settings(self):
        """Export settings to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Settings', 'real_estate_settings.json', 'JSON Files (*.json)'
        )
        if file_path:
            try:
                settings_to_export = self.get_settings_from_ui()
                with open(file_path, 'w') as f:
                    json.dump(settings_to_export, f, indent=2)
                QMessageBox.information(self, 'Success', 'Settings exported successfully!')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to export settings: {str(e)}')
    
    def apply_settings(self):
        """Apply settings without closing dialog"""
        settings = self.get_settings_from_ui()
        self.settings = settings
        self.settings_changed.emit(settings)
    
    def accept(self):
        """Apply settings and close dialog"""
        self.apply_settings()
        super().accept()
    
    def get_final_settings(self) -> dict:
        """Get the final settings after dialog completion"""
        return self.settings