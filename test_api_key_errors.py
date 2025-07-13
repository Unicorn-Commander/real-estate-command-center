#!/usr/bin/env python3
"""
Test script to demonstrate enhanced API key error messages
"""
import sys
import os

# Add desktop to path
sys.path.insert(0, '/home/ucadmin/Development/real-estate-command-center/desktop')

from PySide6.QtWidgets import QApplication
from src.core.api_key_manager import api_key_manager

def test_api_key_manager():
    """Test the API key manager functionality"""
    print("Testing API Key Manager")
    print("=" * 50)
    
    # Check status of all keys
    print("\n1. API Key Status:")
    status = api_key_manager.get_api_key_status()
    for key_type, is_configured in status.items():
        config = api_key_manager.API_KEYS.get(key_type, {})
        status_icon = "✅" if is_configured else "❌"
        print(f"   {status_icon} {config.get('name', key_type)}: {'Configured' if is_configured else 'Missing'}")
    
    # Get missing keys
    print("\n2. Missing API Keys:")
    missing = api_key_manager.get_missing_keys()
    if missing:
        for key_type, config in missing:
            print(f"   - {config['name']} ({config['purpose']})")
    else:
        print("   All API keys are configured!")
    
    # Test getting a specific key
    print("\n3. Testing specific key retrieval:")
    test_keys = ['openai', 'bridge', 'mlsgrid']
    for key_type in test_keys:
        key = api_key_manager.get_api_key(key_type)
        if key:
            # Mask the key for security
            masked_key = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            print(f"   {key_type}: {masked_key}")
        else:
            print(f"   {key_type}: Not configured")
    
    # Show dialog for missing keys (requires Qt app)
    print("\n4. Testing error dialogs...")
    print("   (Dialogs will only show if Qt application is running)")
    
    # Create Qt app if not exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Show summary dialog
    print("\n5. Showing API Key Summary Dialog...")
    api_key_manager.show_api_key_summary()
    
    # Test checking a missing key
    print("\n6. Testing missing key check (will show dialog if key is missing)...")
    has_openai = api_key_manager.check_api_key('openai', show_dialog=True)
    print(f"   OpenAI key check: {'Configured' if has_openai else 'Missing'}")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_api_key_manager()