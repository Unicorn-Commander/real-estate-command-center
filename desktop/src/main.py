#!/usr/bin/env python3
"""
Magic Commander: Real Estate Edition
Professional AI-Powered Real Estate Management Platform

Powered by Unicorn Commander Platform
Created by Magic Unicorn Tech
"""
import sys
import os
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qt_material import apply_stylesheet
from core.colonel_client import ColonelClient
from core.enhanced_colonel_client import EnhancedColonelClient
from core.settings_manager import settings_manager
from core.plasma_integration import PlasmaIntegration
from ui.main_window import MainWindow
from ui.modern_theme import apply_modern_theme
import qtawesome as qta

# Determine config path (desktop/settings.json)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'settings.json')

# Ensure defaults with modern theme
default_config = {'api_url': 'http://localhost:8264', 'theme': 'modern'}
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(default_config, f, indent=2)

with open(CONFIG_PATH) as f:
    config = json.load(f)
API_URL = config.get('api_url', default_config['api_url'])
THEME = config.get('theme', default_config['theme'])


def main():
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Magic Commander: Real Estate Edition")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Magic Unicorn Tech")
    app.setOrganizationDomain("magicunicorn.tech")
    
    # Set application icon
    try:
        icon = qta.icon('fa5s.magic', color='#8B5CF6')
        app.setWindowIcon(icon)
    except:
        pass  # Icon not critical
    
    # Load settings and set up environment
    current_settings = settings_manager.get_all_settings()
    settings_manager.setup_environment_variables()
    
    # Get theme from settings and apply
    theme = current_settings.get('application', {}).get('theme', THEME)
    if theme == 'modern':
        apply_modern_theme(app)
        print("🎨 Applied modern Magic Commander theme")
    else:
        apply_stylesheet(app, theme=theme)
        print(f"🎨 Applied qt-material theme: {theme}")

    # Banner
    print("=" * 60)
    print("🦄 Magic Commander: Real Estate Edition")
    print("   Professional AI-Powered Real Estate Management")
    print("")
    print("   Powered by Unicorn Commander Platform")
    print("   Created by Magic Unicorn Tech")
    print("=" * 60)
    
    # Initialize enhanced client and KDE integration
    print("🚀 Initializing AI systems...")
    
    # Use enhanced colonel client with settings
    colonel = None
    try:
        colonel = EnhancedColonelClient(current_settings)
        print("✅ Enhanced AI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced AI client: {e}")
        print("Please check your settings and ensure all dependencies are met.")
        sys.exit(1) # Exit the application if EnhancedColonelClient fails to initialize
    
    # Initialize KDE integration
    try:
        plasma = PlasmaIntegration(app)
        print("🖥️ KDE Plasma integration initialized")
    except Exception as e:
        print(f"⚠️ KDE integration skipped: {e}")

    # Create and show main window with enhanced features
    print("🏗️ Building modern interface...")
    window = MainWindow(colonel, theme, CONFIG_PATH)
    window.show()
    
    print("")
    print("🎯 Magic Commander: Real Estate Edition is ready!")
    print("💡 Configure API keys in Settings (Ctrl+S) for enhanced functionality")
    print("🚀 Visit https://unicorncommander.com for more information")
    print("")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
