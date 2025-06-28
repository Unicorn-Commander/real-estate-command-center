"""
Main application window with menus, toolbar, status bar, and tabs.
"""
import os
import json
import datetime
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QMenu, QMessageBox, QDialog, QDockWidget
)
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import QSize, Qt
from qt_material import apply_stylesheet
from ui.leads_tab import LeadsTab
from ui.marketing_tab import MarketingTab
from ui.database_tab import DatabaseTab
from ui.dashboard_tab import DashboardTab
from ui.cma_tab import CMATab
from ui.settings_dialog import SettingsDialog
from ui.ai_chat_widget import AIChatWidget


class MainWindow(QMainWindow):
    def __init__(self, colonel_client, theme, config_path, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.theme = theme
        self.config_path = config_path

        self.setWindowTitle("UC-1 Real Estate Commander")
        self.resize(900, 600)

        # Status bar
        self.statusBar().showMessage('Initializing...')

        # Tabs (create first so actions can reference them)
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(self.colonel_client)
        self.leads_tab = LeadsTab(self.colonel_client)
        self.marketing_tab = MarketingTab(self.colonel_client)
        self.cma_tab = CMATab(self.colonel_client)
        self.database_tab = DatabaseTab(self.colonel_client)
        self.tabs.addTab(self.dashboard_tab, 'Dashboard')
        self.tabs.addTab(self.leads_tab, 'Leads')
        self.tabs.addTab(self.marketing_tab, 'Marketing')
        self.tabs.addTab(self.cma_tab, 'CMA')
        self.tabs.addTab(self.database_tab, 'Database')
        self.setCentralWidget(self.tabs)

        # AI Chat Dock Widget
        self.ai_dock = QDockWidget("AI Assistant", self)
        self.ai_chat_widget = AIChatWidget()
        self.ai_dock.setWidget(self.ai_chat_widget)
        self.ai_dock.setMinimumWidth(350)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)

        # Actions, menus, toolbar (create after tabs)
        self._create_actions()
        self._create_menu()
        self._create_toolbar()

        # Initial status
        try:
            ok = self.colonel_client.ping()
            self.statusBar().showMessage(
                f"API: {'Connected' if ok else 'Disconnected'}")
        except Exception:
            self.statusBar().showMessage('API: Error')

    def _create_actions(self):
        # Refresh
        self.action_refresh = QAction(
            qta.icon('fa5s.sync'), 'Refresh All', self)
        self.action_refresh.setShortcut(QKeySequence('Ctrl+R'))
        self.action_refresh.setToolTip('Refresh all tabs (Ctrl+R)')
        self.action_refresh.triggered.connect(self.refresh_all)
        # New Lead
        self.action_new_lead = QAction(
            qta.icon('fa5s.user-plus'), 'New Lead', self)
        self.action_new_lead.setShortcut(QKeySequence('Ctrl+N'))
        self.action_new_lead.setToolTip('Add a new lead (Ctrl+N)')
        self.action_new_lead.triggered.connect(self.leads_tab.on_new_lead)
        # New Campaign
        self.action_new_campaign = QAction(
            qta.icon('fa5s.bullhorn'), 'New Campaign', self)
        self.action_new_campaign.setShortcut(QKeySequence('Ctrl+Shift+N'))
        self.action_new_campaign.setToolTip(
            'Add a new campaign (Ctrl+Shift+N)')
        self.action_new_campaign.triggered.connect(
            self.marketing_tab.on_new_campaign)
        # New CMA
        self.action_new_cma = QAction(
            qta.icon('fa5s.chart-line'), 'New CMA', self)
        self.action_new_cma.setShortcut(QKeySequence('Ctrl+M'))
        self.action_new_cma.setToolTip(
            'Create a new Comparative Market Analysis (Ctrl+M)')
        self.action_new_cma.triggered.connect(self.new_cma)
        # Settings
        self.action_settings = QAction(
            qta.icon('fa5s.cog'), 'Settings...', self)
        self.action_settings.setShortcut(QKeySequence('Ctrl+S'))
        self.action_settings.setToolTip('Open settings (Ctrl+S)')
        self.action_settings.triggered.connect(self.open_settings)
        # AI Assistant Toggle
        self.action_toggle_ai = QAction(
            qta.icon('fa5s.robot'), 'AI Assistant', self)
        self.action_toggle_ai.setShortcut(QKeySequence('Ctrl+A'))
        self.action_toggle_ai.setToolTip('Toggle AI Assistant panel (Ctrl+A)')
        self.action_toggle_ai.setCheckable(True)
        self.action_toggle_ai.setChecked(True)
        self.action_toggle_ai.triggered.connect(self.toggle_ai_assistant)
        # About
        self.action_about = QAction(
            qta.icon('fa5s.info-circle'), 'About', self)
        self.action_about.setShortcut(QKeySequence('F1'))
        self.action_about.setToolTip('About this application (F1)')
        self.action_about.triggered.connect(self._show_about)
        # Exit
        self.action_exit = QAction(qta.icon('fa5s.times'), 'Exit', self)
        self.action_exit.setShortcut(QKeySequence('Ctrl+Q'))
        self.action_exit.setToolTip('Exit application (Ctrl+Q)')
        self.action_exit.triggered.connect(self.close)

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(self.action_refresh)
        file_menu.addAction(self.action_new_lead)
        file_menu.addAction(self.action_new_campaign)
        file_menu.addAction(self.action_new_cma)
        file_menu.addAction(self.action_settings)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)
        
        # View menu for UI toggles
        view_menu = menubar.addMenu('View')
        view_menu.addAction(self.action_toggle_ai)
        
        help_menu = menubar.addMenu('Help')
        help_menu.addAction(self.action_about)

    def _create_toolbar(self):
        toolbar = QToolBar('Main Toolbar')
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addAction(self.action_refresh)
        toolbar.addAction(self.action_new_lead)
        toolbar.addAction(self.action_new_campaign)
        toolbar.addAction(self.action_new_cma)
        toolbar.addSeparator()
        toolbar.addAction(self.action_toggle_ai)
        toolbar.addAction(self.action_settings)
        toolbar.addSeparator()
        toolbar.addAction(self.action_about)
        toolbar.addSeparator()
        toolbar.addAction(self.action_exit)
        self.addToolBar(toolbar)

    def refresh_all(self):
        """Refresh all tabs and update status bar with timestamp."""
        for tab in (self.leads_tab, self.marketing_tab, self.cma_tab, self.database_tab):
            if hasattr(tab, 'load_data'):
                tab.load_data()
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.statusBar().showMessage(f'Last refreshed: {ts}')

    def open_settings(self):
        cfg = {}
        try:
            cfg = json.load(open(self.config_path))
        except BaseException:
            pass
        dlg = SettingsDialog(cfg.get('api_url', ''), self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            new_url, new_theme = dlg.get_values()
            self.colonel_client.url = new_url
            self.theme = new_theme
            with open(self.config_path, 'w') as f:
                json.dump({'api_url': new_url, 'theme': new_theme}, f, indent=2)
            apply_stylesheet(QApplication.instance(), theme=new_theme)
            self.refresh_all()

    def new_cma(self):
        """Switch to CMA tab and reset for new analysis."""
        self.tabs.setCurrentWidget(self.cma_tab)
        # Clear form fields for new CMA (placeholder)
        print("Starting new CMA analysis...")

    def toggle_ai_assistant(self):
        """Toggle the AI Assistant dock widget visibility"""
        if self.ai_dock.isVisible():
            self.ai_dock.hide()
        else:
            self.ai_dock.show()
    
    def _show_about(self):
        QMessageBox.about(
            self,
            'About',
            'UC-1 Real Estate Commander\nVersion 0.1\nWith AI Assistant Integration')
