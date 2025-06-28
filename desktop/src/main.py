#!/usr/bin/env python3
"""
UC-1 Real Estate Commander - Main Application
"""
import sys
import os
import json
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from core.colonel_client import ColonelClient
from core.plasma_integration import PlasmaIntegration
from ui.main_window import MainWindow

# Determine config path (desktop/settings.json)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'settings.json')

# Ensure defaults
default_config = {'api_url': 'http://localhost:8264', 'theme': 'dark_amber.xml'}
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(default_config, f, indent=2)

with open(CONFIG_PATH) as f:
    config = json.load(f)
API_URL = config.get('api_url', default_config['api_url'])
THEME = config.get('theme', default_config['theme'])


def main():
    app = QApplication(sys.argv)
    # Apply theme
    apply_stylesheet(app, theme=THEME)

    # Initialize client and KDE integration
    colonel = ColonelClient(API_URL)
    plasma = PlasmaIntegration(app)

    # Create and show main window
    window = MainWindow(colonel, THEME, CONFIG_PATH)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
