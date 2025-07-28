"""
Modern Main Window for Magic Commander: Real Estate Edition
Professional AI-powered real estate management platform
"""
import os
import json
from datetime import datetime
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QMenu, QMessageBox, QDialog, QDockWidget, QLabel,
    QHBoxLayout, QWidget, QFrame, QVBoxLayout, QSplitter
)
from PySide6.QtGui import QKeySequence, QAction, QFont, QPixmap, QColor, QBrush
from PySide6.QtCore import QSize, Qt, QTimer, Slot
from qt_material import apply_stylesheet
from ui.leads_tab import LeadsTab
from ui.marketing_tab import MarketingTab
from ui.database_tab import DatabaseTab
from ui.dashboard_tab import DashboardTab
from ui.cma_tab import CMATab
from ui.properties_tab import PropertiesTab
from ui.tasks_tab import TasksTab
from ui.settings_dialog import SettingsDialog
from ui.enhanced_settings_dialog import EnhancedSettingsDialog
from ui.welcome_screen import WelcomeScreen
from ui.modern_theme import apply_modern_theme, get_brand_color
from core.settings_manager import settings_manager
from ui.ai_chat_widget import AIChatWidget
from ui.docker_status_widget import DockerStatusWidget
from ui.agents_tab import AgentsTab
from ui.api_key_dialog import APIKeyDialog
from ui.documents_tab import DocumentsTab
from ui.automation_tab import DocumentAutomationTab
from ui.calendar_tab import CalendarTab
from ui.email_integration_tab import EmailIntegrationTab
from ui.analytics_tab import AnalyticsTab
from ui.transactions_tab import TransactionsTab
from ui.document_vault_tab import DocumentVaultTab
from ui.commission_tab import CommissionTab
from ui.client_portal_tab import ClientPortalTab
from ui.user_management_tab import UserManagementTab
from ui.lead_routing_tab import LeadRoutingTab
from ui.team_collaboration_tab import TeamCollaborationTab


class MainWindow(QMainWindow):
    def __init__(self, colonel_client, theme=None, config_path=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        
        # Initialize settings manager
        self.settings_manager = settings_manager
        self.current_settings = self.settings_manager.get_all_settings()
        
        # Modern theming
        self.theme = theme or self.current_settings.get('application', {}).get('theme', 'modern')
        self.config_path = config_path
        
        # Set up environment variables from settings
        self.settings_manager.setup_environment_variables()

        # Apply modern theme
        if self.theme == 'modern':
            apply_modern_theme(QApplication.instance())
        else:
            # Fallback to qt-material theme
            apply_stylesheet(QApplication.instance(), theme=self.theme)

        # Show welcome screen
        self._show_welcome_screen()

        # Modern window setup
        self.setWindowTitle("Magic Commander: Real Estate Edition")
        self.resize(1400, 900)  # Larger for modern layout
        self.setMinimumSize(1200, 800)

        # Create modern UI structure
        self._create_modern_layout()
        
        # Actions, menus, toolbar
        self._create_actions()
        self._create_menu()
        self._create_toolbar()

        # Initial status and validation
        self._validate_and_update_status()
        
        # Connect to agent notifications
        self._setup_agent_notifications()
    
    def _show_welcome_screen(self):
        """Show the modern welcome screen"""
        welcome = WelcomeScreen(self)
        welcome.exec()
    
    def _create_modern_layout(self):
        """Create modern layout with improved visual hierarchy"""
        # Central widget with splitter for main content and AI assistant
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Header with branding
        self._create_header()
        main_layout.addWidget(self.header_frame)
        
        # Content splitter (tabs + AI assistant)
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Main tabs area
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Add tab icons for better visual hierarchy
        # Use enhanced dashboard instead of basic one
        try:
            from ui.enhanced_dashboard import EnhancedDashboard
            self.dashboard_tab = EnhancedDashboard(self.colonel_client)
        except ImportError:
            # Fallback to original dashboard
            self.dashboard_tab = DashboardTab(self.colonel_client)
        
        self.leads_tab = LeadsTab(self.colonel_client)
        self.marketing_tab = MarketingTab(self.colonel_client)
        self.cma_tab = CMATab(self.colonel_client)
        self.database_tab = DatabaseTab(self.colonel_client)
        self.properties_tab = PropertiesTab(self.colonel_client)
        self.tasks_tab = TasksTab(self.colonel_client)
        self.agents_tab = AgentsTab(self.colonel_client)
        self.documents_tab = DocumentsTab()
        self.automation_tab = DocumentAutomationTab()
        self.calendar_tab = CalendarTab()
        self.email_tab = EmailIntegrationTab()
        self.analytics_tab = AnalyticsTab(self.colonel_client)
        self.transactions_tab = TransactionsTab(self.colonel_client)
        self.document_vault_tab = DocumentVaultTab()
        self.commission_tab = CommissionTab()
        self.client_portal_tab = ClientPortalTab()
        self.user_management_tab = UserManagementTab()
        self.lead_routing_tab = LeadRoutingTab()
        self.team_collaboration_tab = TeamCollaborationTab()
        
        # Add tabs with icons
        self.tabs.addTab(self.dashboard_tab, qta.icon('fa5s.tachometer-alt', color='#8B5CF6'), 'Dashboard')
        self.tabs.addTab(self.leads_tab, qta.icon('fa5s.users', color='#06B6D4'), 'Leads')
        self.tabs.addTab(self.marketing_tab, qta.icon('fa5s.bullhorn', color='#EC4899'), 'Marketing')
        self.tabs.addTab(self.cma_tab, qta.icon('fa5s.chart-line', color='#10B981'), 'CMA')
        self.tabs.addTab(self.database_tab, qta.icon('fa5s.database', color='#EF4444'), 'Database')
        self.tabs.addTab(self.properties_tab, qta.icon('fa5s.home', color='#F59E0B'), 'Properties')
        self.tabs.addTab(self.tasks_tab, qta.icon('fa5s.tasks', color='#6B7280'), 'Tasks')
        self.tabs.addTab(self.agents_tab, qta.icon('fa5s.robot', color='#8B5CF6'), 'AI Agents')
        self.tabs.addTab(self.documents_tab, qta.icon('fa5s.file-alt', color='#14B8A6'), 'Documents')
        self.tabs.addTab(self.automation_tab, qta.icon('fa5s.magic', color='#A855F7'), 'Automation')
        self.tabs.addTab(self.calendar_tab, qta.icon('fa5s.calendar-alt', color='#10B981'), 'Calendar')
        self.tabs.addTab(self.email_tab, qta.icon('fa5s.envelope', color='#3B82F6'), 'Email')
        self.tabs.addTab(self.analytics_tab, qta.icon('fa5s.chart-pie', color='#EC4899'), 'Analytics')
        self.tabs.addTab(self.transactions_tab, qta.icon('fa5s.handshake', color='#F97316'), 'Transactions')
        self.tabs.addTab(self.document_vault_tab, qta.icon('fa5s.lock', color='#8B5CF6'), 'Document Vault')
        self.tabs.addTab(self.commission_tab, qta.icon('fa5s.percentage', color='#059669'), 'Commissions')
        self.tabs.addTab(self.client_portal_tab, qta.icon('fa5s.user-circle', color='#3B82F6'), 'Client Portal')
        self.tabs.addTab(self.user_management_tab, qta.icon('fa5s.users-cog', color='#DC2626'), 'User Management')
        self.tabs.addTab(self.lead_routing_tab, qta.icon('fa5s.route', color='#10B981'), 'Lead Routing')
        self.tabs.addTab(self.team_collaboration_tab, qta.icon('fa5s.users-cog', color='#7C3AED'), 'Team Collaboration')
        
        self.content_splitter.addWidget(self.tabs)
        
        # AI Assistant panel (integrated, not dock)
        self._create_ai_assistant_panel()
        self.content_splitter.addWidget(self.ai_panel)
        
        # Set splitter proportions (70% main content, 30% AI)
        self.content_splitter.setSizes([1000, 400])
        self.content_splitter.setCollapsible(0, False)  # Don't allow main content to collapse
        
        main_layout.addWidget(self.content_splitter)
        
        # Modern status bar
        self._create_modern_status_bar()
    
    def _create_header(self):
        """Create modern header with branding and quick actions"""
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(60)
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_brand_color('bg_secondary')}, 
                    stop:1 {get_brand_color('bg_primary')});
                border: none;
                border-bottom: 2px solid {get_brand_color('unicorn_primary')};
                border-radius: 0;
            }}
        """)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo/Brand area
        brand_layout = QHBoxLayout()
        
        # Magic icon
        logo_label = QLabel()
        magic_icon = qta.icon('fa5s.magic', color='#8B5CF6', scale_factor=1.5)
        logo_label.setPixmap(magic_icon.pixmap(32, 32))
        brand_layout.addWidget(logo_label)
        
        # Brand text
        title_label = QLabel("Magic Commander")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('gray_100')};
                font-size: 20px;
                font-weight: bold;
                margin-left: 8px;
            }}
        """)
        brand_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Real Estate Edition")
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('unicorn_primary')};
                font-size: 12px;
                font-weight: 500;
                margin-left: 4px;
                margin-top: 8px;
            }}
        """)
        brand_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(brand_layout)
        header_layout.addStretch()
        
        # Status indicators in header
        self.header_status = QLabel()
        self.header_status.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('gray_300')};
                font-size: 12px;
                padding: 4px 8px;
                background-color: {get_brand_color('bg_tertiary')};
                border-radius: 12px;
            }}
        """)
        header_layout.addWidget(self.header_status)
    
    def _create_ai_assistant_panel(self):
        """Create integrated AI assistant panel"""
        self.ai_panel = QFrame()
        self.ai_panel.setMinimumWidth(350)
        self.ai_panel.setMaximumWidth(500)
        
        ai_layout = QVBoxLayout(self.ai_panel)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(0)
        
        # AI panel header
        ai_header = QFrame()
        ai_header.setFixedHeight(40)
        ai_header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_brand_color('unicorn_primary')}, 
                    stop:1 {get_brand_color('unicorn_secondary')});
                border: none;
                border-radius: 8px 8px 0 0;
            }}
        """)
        
        ai_header_layout = QHBoxLayout(ai_header)
        ai_header_layout.setContentsMargins(12, 8, 12, 8)
        
        # AI icon and title
        ai_icon = QLabel()
        robot_icon = qta.icon('fa5s.robot', color='white')
        ai_icon.setPixmap(robot_icon.pixmap(20, 20))
        ai_header_layout.addWidget(ai_icon)
        
        ai_title = QLabel("AI Assistant")
        ai_title.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                margin-left: 8px;
            }
        """)
        ai_header_layout.addWidget(ai_title)
        ai_header_layout.addStretch()
        
        ai_layout.addWidget(ai_header)
        
        # AI chat widget
        self.ai_chat_widget = AIChatWidget(colonel_client=self.colonel_client)
        ai_layout.addWidget(self.ai_chat_widget)
    
    def _create_modern_status_bar(self):
        """Create modern status bar with enhanced information"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(12, 4, 12, 4)
        
        # AI status
        self.ai_status_label = QLabel()
        status_layout.addWidget(self.ai_status_label)
        
        # Separator
        sep1 = QLabel("•")
        sep1.setStyleSheet(f"color: {get_brand_color('gray_600')};")
        status_layout.addWidget(sep1)
        
        # MLS status
        self.mls_status_label = QLabel()
        status_layout.addWidget(self.mls_status_label)
        
        # Separator
        sep2 = QLabel("•")
        sep2.setStyleSheet(f"color: {get_brand_color('gray_600')};")
        status_layout.addWidget(sep2)
        
        # Data status
        self.data_status_label = QLabel()
        status_layout.addWidget(self.data_status_label)
        
        # Separator
        sep3 = QLabel("•")
        sep3.setStyleSheet(f"color: {get_brand_color('gray_600')};")
        status_layout.addWidget(sep3)
        
        # Docker services status
        self.docker_status_widget = DockerStatusWidget()
        status_layout.addWidget(self.docker_status_widget)
        
        status_layout.addStretch()
        
        # Timestamp
        self.timestamp_label = QLabel()
        self.timestamp_label.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('gray_500')};
                font-size: 11px;
                font-style: italic;
            }}
        """)
        status_layout.addWidget(self.timestamp_label)
        
        self.statusBar().addPermanentWidget(status_widget, 1)
        self._update_status_bar()

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
        # New Property
        self.action_new_property = QAction(
            qta.icon('fa5s.plus-square'), 'New Property', self)
        self.action_new_property.setShortcut(QKeySequence('Ctrl+P'))
        self.action_new_property.setToolTip('Add a new property (Ctrl+P)')
        self.action_new_property.triggered.connect(self.properties_tab.on_new_property)
        # New Task
        self.action_new_task = QAction(
            qta.icon('fa5s.check-square'), 'New Task', self)
        self.action_new_task.setShortcut(QKeySequence('Ctrl+T'))
        self.action_new_task.setToolTip('Add a new task (Ctrl+T)')
        self.action_new_task.triggered.connect(self.tasks_tab.on_new_task)
        # Settings
        self.action_settings = QAction(
            qta.icon('fa5s.cog'), 'Settings...', self)
        self.action_settings.setShortcut(QKeySequence('Ctrl+S'))
        self.action_settings.setToolTip('Open settings (Ctrl+S)')
        self.action_settings.triggered.connect(self.open_settings)
        
        # API Keys
        self.action_api_keys = QAction(
            qta.icon('fa5s.key'), 'API Keys...', self)
        self.action_api_keys.setShortcut(QKeySequence('Ctrl+K'))
        self.action_api_keys.setToolTip('Manage API keys (Ctrl+K)')
        self.action_api_keys.triggered.connect(self._show_api_keys)
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
        file_menu.addAction(self.action_new_property)
        file_menu.addAction(self.action_new_task)
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
        toolbar.addAction(self.action_new_property)
        toolbar.addAction(self.action_new_task)
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
        for tab in (self.leads_tab, self.marketing_tab, self.cma_tab, self.database_tab, self.properties_tab, self.tasks_tab):
            if hasattr(tab, 'load_data'):
                tab.load_data()
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.statusBar().showMessage(f'Last refreshed: {ts}')

    def open_settings(self):
        """Open enhanced settings dialog"""
        dlg = EnhancedSettingsDialog(self.current_settings, self)
        dlg.settings_changed.connect(self._on_settings_changed)
        
        if dlg.exec() == QDialog.Accepted:
            new_settings = dlg.get_final_settings()
            self._apply_new_settings(new_settings)
    
    def _on_settings_changed(self, new_settings):
        """Handle settings changes from dialog"""
        self._apply_new_settings(new_settings)
    
    def _apply_new_settings(self, new_settings):
        """Apply new settings throughout the application"""
        # Update settings manager
        self.settings_manager.update_settings(new_settings)
        self.current_settings = new_settings
        
        # Set up environment variables
        self.settings_manager.setup_environment_variables()
        
        # Update theme if changed
        new_theme = new_settings.get('application', {}).get('theme', self.theme)
        if new_theme != self.theme:
            self.theme = new_theme
            apply_stylesheet(QApplication.instance(), theme=new_theme)
        
        # Update colonel client if it supports settings updates
        if hasattr(self.colonel_client, 'update_settings'):
            self.colonel_client.update_settings(new_settings)
        
        # Update AI chat widget
        if hasattr(self.ai_chat_widget, 'update_settings'):
            self.ai_chat_widget.update_settings(new_settings)
        
        # Refresh all data
        self.refresh_all()
        
        # Update status bar
        self._validate_and_update_status()
        
        # Legacy config file support
        if self.config_path:
            try:
                legacy_settings = self.settings_manager.get_legacy_settings()
                with open(self.config_path, 'w') as f:
                    json.dump(legacy_settings, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not update legacy config: {e}")
    
    def _update_status_bar(self):
        """Update modern status bar with current system status"""
        # AI Backend status
        if hasattr(self.colonel_client, 'get_backend_status'):
            backend_status = self.colonel_client.get_backend_status()
            backend_type = backend_status.get('backend_type', 'Unknown')
            agent_count = backend_status.get('available_agents', 0)
            total_agents = backend_status.get('total_agents', 4)
            
            ai_color = get_brand_color('success') if agent_count == total_agents else get_brand_color('warning')
            ai_status = f"AI: {backend_type.replace('_', ' ').title()} ({agent_count}/{total_agents})"
            self.ai_status_label.setText(ai_status)
            self.ai_status_label.setStyleSheet(f"color: {ai_color}; font-weight: 500;")
        else:
            # Legacy status
            try:
                ok = self.colonel_client.ping()
                ai_color = get_brand_color('success') if ok else get_brand_color('error')
                ai_status = f"API: {'Connected' if ok else 'Disconnected'}"
                self.ai_status_label.setText(ai_status)
                self.ai_status_label.setStyleSheet(f"color: {ai_color}; font-weight: 500;")
            except Exception:
                self.ai_status_label.setText("API: Error")
                self.ai_status_label.setStyleSheet(f"color: {get_brand_color('error')}; font-weight: 500;")
        
        # MLS Provider status
        mls_provider = self.current_settings.get('mls_providers', {}).get('preferred_provider', 'Unknown')
        has_key = bool(self.current_settings.get('mls_providers', {}).get(f'{mls_provider}_api_key'))
        mls_color = get_brand_color('success') if has_key else get_brand_color('warning')
        mls_status = f"MLS: {mls_provider.title()}" + (" ✓" if has_key else " ⚠")
        self.mls_status_label.setText(mls_status)
        self.mls_status_label.setStyleSheet(f"color: {mls_color}; font-weight: 500;")
        
        # Public data status
        public_enabled = self.current_settings.get('public_data', {}).get('enable_scraping', True)
        data_color = get_brand_color('success') if public_enabled else get_brand_color('gray_500')
        data_status = f"Public Data: {'Enabled' if public_enabled else 'Disabled'}"
        self.data_status_label.setText(data_status)
        self.data_status_label.setStyleSheet(f"color: {data_color}; font-weight: 500;")
        
        # Update header status
        total_systems = 3
        working_systems = sum([
            agent_count == total_agents if hasattr(self.colonel_client, 'get_backend_status') else (self.colonel_client.ping() if hasattr(self.colonel_client, 'ping') else False),
            has_key,
            public_enabled
        ])
        
        header_status_color = get_brand_color('success') if working_systems == total_systems else get_brand_color('warning')
        header_status_text = f"Systems: {working_systems}/{total_systems} Ready"
        self.header_status.setText(header_status_text)
        self.header_status.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
                background-color: {header_status_color};
                border-radius: 12px;
            }}
        """)
        
        # Update timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.timestamp_label.setText(f"Last updated: {timestamp}")
    
    def _validate_and_update_status(self):
        """Validate current settings and update status bar"""
        issues = self.settings_manager.validate_settings()
        
        if issues:
            # Show warnings for critical issues
            warning_messages = []
            for category, message in issues.items():
                warning_messages.append(f"{category.upper()}: {message}")
            
            if warning_messages:
                QMessageBox.warning(
                    self,
                    'Configuration Issues',
                    'Some configuration issues were detected:\n\n' + 
                    '\n'.join(warning_messages) + 
                    '\n\nYou can configure these in Settings (Ctrl+S).'
                )
        
        self._update_status_bar()

    def new_cma(self):
        """Switch to CMA tab and reset for new analysis."""
        self.tabs.setCurrentWidget(self.cma_tab)
        # Clear form fields for new CMA (placeholder)
        print("Starting new CMA analysis...")

    def toggle_ai_assistant(self):
        """Toggle the AI Assistant panel visibility"""
        if self.ai_panel.isVisible():
            self.ai_panel.hide()
        else:
            self.ai_panel.show()
    
    def _show_about(self):
        """Show modern about dialog with branding"""
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle("About Magic Commander: Real Estate Edition")
        about_msg.setTextFormat(Qt.RichText)
        
        # Create modern about content
        about_text = f"""
        <div style="text-align: center; padding: 20px;">
            <h2 style="color: {get_brand_color('unicorn_primary')}; margin-bottom: 10px;">
                🦄 Magic Commander: Real Estate Edition
            </h2>
            <p style="color: {get_brand_color('gray_300')}; font-size: 14px; margin-bottom: 20px;">
                Professional AI-Powered Real Estate Management Platform
            </p>
            
            <div style="background: {get_brand_color('bg_tertiary')}; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p style="color: {get_brand_color('gray_100')}; margin: 5px 0;"><strong>Version:</strong> 3.0.0 (Enhanced)</p>
                <p style="color: {get_brand_color('gray_100')}; margin: 5px 0;"><strong>Status:</strong> Production Ready</p>
                <p style="color: {get_brand_color('gray_100')}; margin: 5px 0;"><strong>AI Integration:</strong> Integrated Colonel</p>
            </div>
            
            <div style="margin-top: 20px;">
                <p style="color: {get_brand_color('unicorn_secondary')}; font-weight: bold; margin: 5px 0;">
                    Powered by Unicorn Commander Platform
                </p>
                <p style="color: {get_brand_color('unicorn_accent')}; font-weight: bold; margin: 5px 0;">
                    Created by Magic Unicorn Tech
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid {get_brand_color('gray_700')};">
                <p style="color: {get_brand_color('gray_400')}; font-size: 12px;">
                    Revolutionary Real Estate Platform • Zero Monthly Costs<br>
                    Multi-Provider MLS • AI Tool Calling • Professional Reports
                </p>
            </div>
        </div>
        """
        
        about_msg.setText(about_text)
        about_msg.setStandardButtons(QMessageBox.Ok)
        about_msg.exec()
    
    def _show_api_keys(self):
        """Show the API key management dialog"""
        dialog = APIKeyDialog(self)
        dialog.keys_updated.connect(self._on_api_keys_updated)
        dialog.exec()
    
    def _on_api_keys_updated(self):
        """Handle API keys being updated"""
        # Refresh UI elements that depend on API keys
        self._update_status_bar()
        # Notify tabs that may need to refresh
        if hasattr(self.dashboard_tab, 'refresh'):
            self.dashboard_tab.refresh()
    
    def _setup_agent_notifications(self):
        """Connect to agent manager for notifications"""
        try:
            agent_manager = self.colonel_client.get_agent_manager()
            
            # Connect to notification signals
            agent_manager.agent_notification.connect(self._show_agent_notification)
            agent_manager.agent_error.connect(self._show_agent_error)
            
            # Create notification widget
            self._create_notification_widget()
            
        except Exception as e:
            print(f"Failed to setup agent notifications: {e}")
    
    def _create_notification_widget(self):
        """Create a notification area for agent messages"""
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QDockWidget
        from PySide6.QtCore import QTimer
        
        # Create notification dock widget
        self.notification_dock = QDockWidget("Agent Notifications", self)
        self.notification_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Notification list
        self.notification_list = QListWidget()
        self.notification_list.setMaximumHeight(150)
        self.notification_dock.setWidget(self.notification_list)
        
        # Add to main window
        self.addDockWidget(Qt.RightDockWidgetArea, self.notification_dock)
        self.notification_dock.hide()  # Hidden by default
        
        # Timer to auto-hide notifications
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._hide_old_notifications)
        self.notification_timer.start(30000)  # Check every 30 seconds
    
    @Slot(str, str, str)
    def _show_agent_notification(self, agent_name: str, notification_type: str, message: str):
        """Show agent notification in UI"""
        # Add to notification list
        timestamp = datetime.now().strftime("%H:%M")
        item_text = f"[{timestamp}] {agent_name}: {message}"
        
        item = QListWidgetItem(item_text)
        
        # Color code by type
        color_map = {
            "info": QColor(0, 123, 255),      # Blue
            "success": QColor(40, 167, 69),   # Green
            "warning": QColor(255, 193, 7),   # Yellow
            "error": QColor(220, 53, 69)      # Red
        }
        
        if notification_type in color_map:
            item.setForeground(QBrush(color_map[notification_type]))
        
        # Add timestamp as data for cleanup
        item.setData(Qt.UserRole, datetime.now())
        
        self.notification_list.insertItem(0, item)  # Add at top
        
        # Show dock if hidden
        if not self.notification_dock.isVisible():
            self.notification_dock.show()
        
        # Also show in status bar briefly
        self.statusBar().showMessage(f"{agent_name}: {message}", 5000)
    
    @Slot(str, str)
    def _show_agent_error(self, agent_name: str, error: str):
        """Show agent error in UI"""
        self._show_agent_notification(agent_name, "error", error)
        
        # Also show error dialog for critical errors
        if "critical" in error.lower() or "failed" in error.lower():
            QMessageBox.warning(self, f"Agent Error - {agent_name}", error)
    
    def _hide_old_notifications(self):
        """Remove notifications older than 5 minutes"""
        current_time = datetime.now()
        items_to_remove = []
        
        for i in range(self.notification_list.count()):
            item = self.notification_list.item(i)
            timestamp = item.data(Qt.UserRole)
            
            if timestamp and (current_time - timestamp).seconds > 300:  # 5 minutes
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.notification_list.takeItem(self.notification_list.row(item))
        
        # Hide dock if empty
        if self.notification_list.count() == 0:
            self.notification_dock.hide()
