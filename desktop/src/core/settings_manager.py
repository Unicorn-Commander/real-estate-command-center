"""
Settings Manager for Real Estate Command Center
Handles loading, saving, and managing application settings
"""
import json
import os
from typing import Dict, Any
from pathlib import Path

class SettingsManager:
    """Manages application settings with persistence"""
    
    def __init__(self, settings_file: str = None):
        self.app_dir = Path.home() / '.real_estate_command_center'
        self.app_dir.mkdir(exist_ok=True)
        
        self.settings_file = settings_file or str(self.app_dir / 'settings.json')
        self.legacy_settings_file = str(Path(__file__).parent.parent.parent / 'settings.json')
        
        self.default_settings = {
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
            'ai_backend': {
                'backend_type': 'real_estate_interpreter',  # Default to integrated Colonel
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
            'public_data': {
                'enable_scraping': True,
                'respect_robots_txt': True,
                'rate_limit_seconds': 2,
                'max_retries': 3,
                'preferred_counties': ['King', 'Multnomah', 'Los Angeles', 'Harris']
            },
            'application': {
                'theme': 'modern',  # Default to our modern theme
                'auto_save_settings': True,
                'debug_mode': False,
                'data_cache_enabled': True,
                'cache_expiry_hours': 24,
                'window_geometry': None,
                'window_state': None
            },
            # Legacy settings for backward compatibility
            'api_endpoint': 'http://localhost:11434',
            'theme': 'modern'
        }
        
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, with fallback to defaults"""
        settings = self.default_settings.copy()
        
        # Try to load from new settings file
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                self._deep_merge(settings, loaded_settings)
                return settings
            except Exception as e:
                print(f"Warning: Could not load settings from {self.settings_file}: {e}")
        
        # Try to load from legacy settings file
        if os.path.exists(self.legacy_settings_file):
            try:
                with open(self.legacy_settings_file, 'r') as f:
                    legacy_settings = json.load(f)
                # Migrate legacy settings
                self._migrate_legacy_settings(settings, legacy_settings)
                # Save migrated settings to new location
                self.save_settings(settings)
                return settings
            except Exception as e:
                print(f"Warning: Could not load legacy settings from {self.legacy_settings_file}: {e}")
        
        # Return defaults if no settings file found
        return settings
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Deep merge update dict into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _migrate_legacy_settings(self, settings: Dict[str, Any], legacy: Dict[str, Any]):
        """Migrate legacy settings format to new format"""
        # Map legacy API endpoint to new AI backend settings
        if 'api_endpoint' in legacy:
            settings['ai_backend']['ollama_url'] = legacy['api_endpoint']
            settings['api_endpoint'] = legacy['api_endpoint']  # Keep for backward compatibility
        
        # Map legacy theme
        if 'theme' in legacy:
            settings['application']['theme'] = legacy['theme']
            settings['theme'] = legacy['theme']  # Keep for backward compatibility
        
        # Merge any other legacy settings
        for key, value in legacy.items():
            if key not in ['api_endpoint', 'theme']:
                settings[key] = value
    
    def save_settings(self, settings: Dict[str, Any] = None):
        """Save settings to file"""
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings to {self.settings_file}: {e}")
    
    def get_setting(self, key_path: str, default=None):
        """Get a setting using dot notation (e.g., 'mls_providers.bridge_api_key')"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_setting(self, key_path: str, value: Any):
        """Set a setting using dot notation"""
        keys = key_path.split('.')
        current = self.settings
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Auto-save if enabled
        if self.get_setting('application.auto_save_settings', True):
            self.save_settings()
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update settings with new values"""
        self._deep_merge(self.settings, new_settings)
        
        # Auto-save if enabled
        if self.get_setting('application.auto_save_settings', True):
            self.save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self.settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self.save_settings()
    
    def setup_environment_variables(self):
        """Set up environment variables from settings"""
        # MLS API keys
        mls_providers = self.get_setting('mls_providers', {})
        for provider, key in mls_providers.items():
            if provider.endswith('_api_key') and key:
                env_var = provider.upper()
                os.environ[env_var] = key
        
        # AI backend settings
        ai_backend = self.get_setting('ai_backend', {})
        if ai_backend.get('openai_api_key'):
            os.environ['OPENAI_API_KEY'] = ai_backend['openai_api_key']
        
        # Set backend type for colonel client
        os.environ['USE_OPENAI'] = str(ai_backend.get('backend_type') == 'openai').lower()
    
    def get_legacy_settings(self) -> Dict[str, Any]:
        """Get settings in legacy format for backward compatibility"""
        return {
            'api_endpoint': self.get_setting('ai_backend.ollama_url', 'http://localhost:11434'),
            'theme': self.get_setting('application.theme', 'dark_amber.xml')
        }
    
    def export_settings(self, file_path: str):
        """Export settings to a JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def import_settings(self, file_path: str):
        """Import settings from a JSON file"""
        with open(file_path, 'r') as f:
            imported_settings = json.load(f)
        
        self.update_settings(imported_settings)
    
    def validate_settings(self) -> Dict[str, str]:
        """Validate current settings and return any issues"""
        issues = {}
        
        # Check MLS provider settings
        mls = self.get_setting('mls_providers', {})
        preferred = mls.get('preferred_provider', 'bridge')
        preferred_key = f"{preferred}_api_key"
        
        if not mls.get(preferred_key):
            issues['mls'] = f"No API key configured for preferred provider '{preferred}'"
        
        # Check AI backend settings
        ai = self.get_setting('ai_backend', {})
        backend = ai.get('backend_type', 'ollama')
        
        if backend == 'openai' and not ai.get('openai_api_key'):
            issues['ai'] = "OpenAI selected but no API key configured"
        elif backend == 'ollama' and not ai.get('ollama_url'):
            issues['ai'] = "Ollama selected but no URL configured"
        
        return issues

# Global settings manager instance
settings_manager = SettingsManager()