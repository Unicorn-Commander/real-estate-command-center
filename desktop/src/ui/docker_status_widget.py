"""
Docker Services Status Widget for Real Estate Command Center
Shows real-time status of PostgreSQL and SearXNG containers
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenu
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction, QIcon
import qtawesome as qta
from core.docker_integration import docker_services
import logging

logger = logging.getLogger(__name__)

class DockerStatusWidget(QWidget):
    """Widget showing Docker services status in the status bar"""
    
    services_changed = Signal(dict)  # Emitted when services status changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_status = {}
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Set up the UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Docker icon
        self.docker_icon = QLabel()
        self.docker_icon.setPixmap(qta.icon('fa5s.database', color='#0db7ed').pixmap(16, 16))
        layout.addWidget(self.docker_icon)
        
        # Services label
        self.services_label = QLabel("Services:")
        layout.addWidget(self.services_label)
        
        # PostgreSQL status
        self.db_icon = QLabel()
        self.db_label = QLabel("PostgreSQL")
        self.db_label.setStyleSheet("margin-left: 5px;")
        layout.addWidget(self.db_icon)
        layout.addWidget(self.db_label)
        
        # SearXNG status
        self.searxng_icon = QLabel()
        self.searxng_label = QLabel("SearXNG")
        self.searxng_label.setStyleSheet("margin-left: 10px;")
        layout.addWidget(self.searxng_icon)
        layout.addWidget(self.searxng_label)
        
        # Manage button
        self.manage_button = QPushButton("Manage")
        self.manage_button.setFlat(True)
        self.manage_button.setStyleSheet("""
            QPushButton {
                padding: 2px 8px;
                margin-left: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.manage_button.clicked.connect(self.show_manage_menu)
        layout.addWidget(self.manage_button)
        
        self.setLayout(layout)
        
        # Initial status check
        self.update_status()
        
    def setup_timer(self):
        """Set up timer for periodic status checks"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # Check every 5 seconds
        
    def update_status(self):
        """Update the status display"""
        try:
            status = docker_services.check_services_status()
            
            # Check if status changed
            if status != self.last_status:
                self.last_status = status
                self.services_changed.emit(status)
            
            # Update Docker status
            if not status.get('docker'):
                self.docker_icon.setPixmap(qta.icon('fa5s.exclamation-triangle', color='orange').pixmap(16, 16))
                self.services_label.setText("Docker not found")
                self.db_icon.hide()
                self.db_label.hide()
                self.searxng_icon.hide()
                self.searxng_label.hide()
                self.manage_button.hide()
                return
            else:
                self.docker_icon.setPixmap(qta.icon('fa5s.database', color='#0db7ed').pixmap(16, 16))
                self.services_label.setText("Services:")
                self.db_icon.show()
                self.db_label.show()
                self.searxng_icon.show()
                self.searxng_label.show()
                self.manage_button.show()
            
            # Update PostgreSQL status
            if status.get('postgresql'):
                self.db_icon.setPixmap(qta.icon('fa5s.database', color='green').pixmap(16, 16))
                self.db_label.setToolTip("PostgreSQL is running")
            else:
                self.db_icon.setPixmap(qta.icon('fa5s.database', color='red').pixmap(16, 16))
                self.db_label.setToolTip("PostgreSQL is not running")
            
            # Update SearXNG status
            if status.get('searxng'):
                self.searxng_icon.setPixmap(qta.icon('fa5s.search', color='green').pixmap(16, 16))
                self.searxng_label.setToolTip("SearXNG is running")
            else:
                self.searxng_icon.setPixmap(qta.icon('fa5s.search', color='red').pixmap(16, 16))
                self.searxng_label.setToolTip("SearXNG is not running")
                
        except Exception as e:
            logger.error(f"Error updating Docker status: {e}")
            
    def show_manage_menu(self):
        """Show the management menu"""
        menu = QMenu(self)
        
        # Get current status
        status = docker_services.check_services_status()
        
        # Start/Stop all services
        if status.get('postgresql') or status.get('searxng'):
            stop_action = QAction(qta.icon('fa5s.stop', color='red'), "Stop All Services", self)
            stop_action.triggered.connect(self.stop_services)
            menu.addAction(stop_action)
            
            restart_action = QAction(qta.icon('fa5s.sync', color='orange'), "Restart All Services", self)
            restart_action.triggered.connect(self.restart_services)
            menu.addAction(restart_action)
        else:
            start_action = QAction(qta.icon('fa5s.play', color='green'), "Start All Services", self)
            start_action.triggered.connect(self.start_services)
            menu.addAction(start_action)
        
        menu.addSeparator()
        
        # Service info
        info_action = QAction(qta.icon('fa5s.info-circle'), "Service Information", self)
        info_action.triggered.connect(self.show_service_info)
        menu.addAction(info_action)
        
        # Test connections
        test_action = QAction(qta.icon('fa5s.plug'), "Test Connections", self)
        test_action.triggered.connect(self.test_connections)
        menu.addAction(test_action)
        
        # Show menu at button
        menu.exec(self.manage_button.mapToGlobal(self.manage_button.rect().bottomLeft()))
        
    def start_services(self):
        """Start Docker services"""
        self.manage_button.setText("Starting...")
        self.manage_button.setEnabled(False)
        
        if docker_services.start_services():
            QMessageBox.information(self, "Success", "Docker services started successfully!")
        else:
            QMessageBox.warning(self, "Error", "Failed to start Docker services. Check the logs for details.")
        
        self.manage_button.setText("Manage")
        self.manage_button.setEnabled(True)
        self.update_status()
        
    def stop_services(self):
        """Stop Docker services"""
        reply = QMessageBox.question(
            self, 
            "Confirm Stop", 
            "Are you sure you want to stop all Docker services?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.manage_button.setText("Stopping...")
            self.manage_button.setEnabled(False)
            
            if docker_services.stop_services():
                QMessageBox.information(self, "Success", "Docker services stopped successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to stop Docker services. Check the logs for details.")
            
            self.manage_button.setText("Manage")
            self.manage_button.setEnabled(True)
            self.update_status()
            
    def restart_services(self):
        """Restart Docker services"""
        self.manage_button.setText("Restarting...")
        self.manage_button.setEnabled(False)
        
        docker_services.stop_services()
        if docker_services.start_services():
            QMessageBox.information(self, "Success", "Docker services restarted successfully!")
        else:
            QMessageBox.warning(self, "Error", "Failed to restart Docker services. Check the logs for details.")
        
        self.manage_button.setText("Manage")
        self.manage_button.setEnabled(True)
        self.update_status()
        
    def show_service_info(self):
        """Show detailed service information"""
        info = docker_services.get_service_info()
        
        msg = "Docker Services Information\n" + "="*30 + "\n\n"
        
        if info['docker_installed']:
            msg += "✓ Docker is installed\n\n"
        else:
            msg += "✗ Docker is not installed\n\n"
        
        # PostgreSQL info
        pg_info = info['services']['postgresql']
        msg += "PostgreSQL:\n"
        msg += f"  Status: {'Running' if pg_info['running'] else 'Not running'}\n"
        if pg_info['running']:
            msg += f"  Connection: {'✓ OK' if pg_info['connection_test'] else '✗ Failed'}\n"
        msg += f"  Host: {pg_info['config']['host']}\n"
        msg += f"  Port: {pg_info['config']['port']}\n"
        msg += f"  Database: {pg_info['config']['database']}\n\n"
        
        # SearXNG info
        sx_info = info['services']['searxng']
        msg += "SearXNG:\n"
        msg += f"  Status: {'Running' if sx_info['running'] else 'Not running'}\n"
        if sx_info['running']:
            msg += f"  Connection: {'✓ OK' if sx_info['connection_test'] else '✗ Failed'}\n"
        msg += f"  URL: {sx_info['url']}\n"
        
        QMessageBox.information(self, "Service Information", msg)
        
    def test_connections(self):
        """Test connections to services"""
        self.manage_button.setText("Testing...")
        self.manage_button.setEnabled(False)
        
        results = []
        
        # Test PostgreSQL
        if docker_services.test_postgresql_connection():
            results.append("✓ PostgreSQL connection successful")
        else:
            results.append("✗ PostgreSQL connection failed")
        
        # Test SearXNG
        if docker_services.test_searxng_connection():
            results.append("✓ SearXNG connection successful")
        else:
            results.append("✗ SearXNG connection failed")
        
        self.manage_button.setText("Manage")
        self.manage_button.setEnabled(True)
        
        QMessageBox.information(
            self, 
            "Connection Test Results", 
            "\n".join(results)
        )