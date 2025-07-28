"""
User Management Tab for Real Estate Command Center
Multi-user support with role-based permissions interface
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit, QLabel, QGroupBox,
    QFrame, QSplitter, QTabWidget, QToolBar, QProgressBar,
    QHeaderView, QMessageBox, QDateEdit, QSpinBox, QTextEdit,
    QListWidget, QListWidgetItem, QStackedWidget, QCheckBox,
    QDialog, QDialogButtonBox, QFormLayout, QCalendarWidget,
    QTreeWidget, QTreeWidgetItem, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot, QDate, QDateTime
from PySide6.QtGui import QAction, QIcon, QFont, QPalette, QColor, QPixmap
import qtawesome as qta
from datetime import datetime, timedelta
import json

from core.user_management import (
    get_user_manager, User, UserRole, Permission, ROLE_PERMISSIONS
)


class UserLoginDialog(QDialog):
    """User login dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = get_user_manager()
        self.setWindowTitle("Real Estate Command Center - Login")
        self.setModal(True)
        self.resize(400, 300)
        self.authenticated_user = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the login dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("User Authentication")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #059669; margin-bottom: 20px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Login form
        form_group = QGroupBox("Login Credentials")
        form_layout = QFormLayout(form_group)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username or email")
        form_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        layout.addWidget(form_group)
        
        # Demo users section (for testing)
        demo_group = QGroupBox("Demo Users (Development)")
        demo_layout = QVBoxLayout(demo_group)
        
        demo_note = QLabel("Default admin: username 'admin', password 'admin123'")
        demo_note.setStyleSheet("color: #6B7280; font-style: italic;")
        demo_layout.addWidget(demo_note)
        
        # Quick login buttons for common roles
        demo_users = [
            ("admin", "admin123", "Administrator"),
            ("agent1", "password123", "Senior Agent"),
            ("assistant1", "password123", "Assistant")
        ]
        
        for username, password, role in demo_users:
            demo_btn = QPushButton(f"Login as {role} ({username})")
            demo_btn.clicked.connect(lambda checked, u=username, p=password: self._quick_login(u, p))
            demo_layout.addWidget(demo_btn)
        
        layout.addWidget(demo_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setIcon(qta.icon('fa5s.sign-in-alt'))
        self.login_btn.clicked.connect(self._attempt_login)
        self.login_btn.setDefault(True)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        # Connect enter key
        self.password_edit.returnPressed.connect(self._attempt_login)
    
    def _attempt_login(self):
        """Attempt to login with entered credentials"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            self.status_label.setText("Please enter both username and password.")
            return
        
        self._perform_login(username, password)
    
    def _quick_login(self, username: str, password: str):
        """Quick login with predefined credentials"""
        self.username_edit.setText(username)
        self.password_edit.setText(password)
        self._perform_login(username, password)
    
    def _perform_login(self, username: str, password: str):
        """Perform the actual login"""
        try:
            session = self.user_manager.authenticate(username, password, "127.0.0.1")
            
            if session:
                self.authenticated_user = self.user_manager.current_user
                self.status_label.setText("")
                self.accept()
            else:
                self.status_label.setText("Invalid username or password.")
        
        except Exception as e:
            self.status_label.setText(f"Login error: {str(e)}")


class CreateUserDialog(QDialog):
    """Dialog for creating new users"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = get_user_manager()
        self.setWindowTitle("Create New User")
        self.setModal(True)
        self.resize(500, 600)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user creation dialog UI"""
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Unique username")
        basic_layout.addRow("Username:", self.username_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@company.com")
        basic_layout.addRow("Email:", self.email_edit)
        
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Full Name")
        basic_layout.addRow("Full Name:", self.full_name_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password (min 6 characters)")
        self.password_edit.setEchoMode(QLineEdit.Password)
        basic_layout.addRow("Password:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        basic_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        layout.addWidget(basic_group)
        
        # Role and permissions
        role_group = QGroupBox("Role and Access")
        role_layout = QFormLayout(role_group)
        
        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value.replace('_', ' ').title(), role)
        role_layout.addRow("Role:", self.role_combo)
        
        # Role description
        self.role_description = QLabel()
        self.role_description.setWordWrap(True)
        self.role_description.setStyleSheet("color: #6B7280; font-size: 12px;")
        role_layout.addRow("Description:", self.role_description)
        
        # Connect role change to update description
        self.role_combo.currentTextChanged.connect(self._update_role_description)
        self._update_role_description()
        
        layout.addWidget(role_group)
        
        # Profile information
        profile_group = QGroupBox("Profile Information (Optional)")
        profile_layout = QFormLayout(profile_group)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("(555) 123-4567")
        profile_layout.addRow("Phone:", self.phone_edit)
        
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("Sales, Marketing, etc.")
        profile_layout.addRow("Department:", self.department_edit)
        
        layout.addWidget(profile_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._create_user)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _update_role_description(self):
        """Update role description based on selected role"""
        role = self.role_combo.currentData()
        if role:
            descriptions = {
                UserRole.ADMIN: "Full system access including user management and system configuration.",
                UserRole.BROKER: "Access to all transactions and reports, user oversight capabilities.",
                UserRole.TEAM_LEAD: "Manage team activities, assign leads, view team performance.",
                UserRole.SENIOR_AGENT: "Full agent capabilities plus campaign creation and extended reporting.",
                UserRole.AGENT: "Standard agent access - manage own leads, transactions, and commissions.",
                UserRole.ASSISTANT: "Support role with limited access to help with administrative tasks.",
                UserRole.TRAINEE: "Read-only access for learning and training purposes.",
                UserRole.VIEWER: "View-only access to assigned resources."
            }
            self.role_description.setText(descriptions.get(role, ""))
    
    def _create_user(self):
        """Create the new user"""
        # Validate inputs
        if not all([self.username_edit.text(), self.email_edit.text(), 
                   self.full_name_edit.text(), self.password_edit.text()]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        if self.password_edit.text() != self.confirm_password_edit.text():
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return
        
        if len(self.password_edit.text()) < 6:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 6 characters.")
            return
        
        try:
            user = self.user_manager.create_user(
                username=self.username_edit.text(),
                email=self.email_edit.text(),
                password=self.password_edit.text(),
                full_name=self.full_name_edit.text(),
                role=self.role_combo.currentData(),
                created_by=self.user_manager.current_user.user_id if self.user_manager.current_user else None
            )
            
            # Update profile information
            if self.phone_edit.text() or self.department_edit.text():
                self.user_manager.update_user(
                    user.user_id,
                    phone=self.phone_edit.text(),
                    department=self.department_edit.text()
                )
            
            QMessageBox.information(
                self,
                "User Created",
                f"User '{user.username}' has been created successfully."
            )
            
            self.accept()
        
        except ValueError as e:
            QMessageBox.warning(self, "Creation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"Failed to create user: {str(e)}")


class EditUserDialog(QDialog):
    """Dialog for editing existing users"""
    
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.user_manager = get_user_manager()
        self.setWindowTitle(f"Edit User - {user.full_name}")
        self.setModal(True)
        self.resize(500, 700)
        
        self._create_ui()
        self._populate_fields()
    
    def _create_ui(self):
        """Create the edit user dialog UI"""
        layout = QVBoxLayout(self)
        
        # Tabs for different sections
        self.tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        self.username_edit = QLineEdit()
        basic_layout.addRow("Username:", self.username_edit)
        
        self.email_edit = QLineEdit()
        basic_layout.addRow("Email:", self.email_edit)
        
        self.full_name_edit = QLineEdit()
        basic_layout.addRow("Full Name:", self.full_name_edit)
        
        self.phone_edit = QLineEdit()
        basic_layout.addRow("Phone:", self.phone_edit)
        
        self.department_edit = QLineEdit()
        basic_layout.addRow("Department:", self.department_edit)
        
        self.is_active_check = QCheckBox("Account Active")
        basic_layout.addRow("Status:", self.is_active_check)
        
        self.tabs.addTab(basic_tab, "Basic Info")
        
        # Role & Permissions Tab
        role_tab = QWidget()
        role_layout = QVBoxLayout(role_tab)
        
        # Role selection
        role_group = QGroupBox("Role")
        role_group_layout = QFormLayout(role_group)
        
        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value.replace('_', ' ').title(), role)
        role_group_layout.addRow("Role:", self.role_combo)
        
        role_layout.addWidget(role_group)
        
        # Custom permissions
        permissions_group = QGroupBox("Custom Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        
        # Additional permissions
        add_perms_label = QLabel("Additional Permissions:")
        permissions_layout.addWidget(add_perms_label)
        
        self.additional_permissions = QListWidget()
        self.additional_permissions.setMaximumHeight(150)
        permissions_layout.addWidget(self.additional_permissions)
        
        # Disabled permissions
        disabled_perms_label = QLabel("Disabled Permissions:")
        permissions_layout.addWidget(disabled_perms_label)
        
        self.disabled_permissions = QListWidget()
        self.disabled_permissions.setMaximumHeight(150)
        permissions_layout.addWidget(self.disabled_permissions)
        
        role_layout.addWidget(permissions_group)
        
        self.tabs.addTab(role_tab, "Role & Permissions")
        
        # Activity Tab
        activity_tab = QWidget()
        activity_layout = QVBoxLayout(activity_tab)
        
        # User statistics
        stats_group = QGroupBox("User Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.created_at_label = QLabel()
        stats_layout.addRow("Created:", self.created_at_label)
        
        self.last_login_label = QLabel()
        stats_layout.addRow("Last Login:", self.last_login_label)
        
        self.failed_attempts_label = QLabel()
        stats_layout.addRow("Failed Login Attempts:", self.failed_attempts_label)
        
        activity_layout.addWidget(stats_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_group_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        activity_group_layout.addWidget(self.activity_list)
        
        activity_layout.addWidget(activity_group)
        
        self.tabs.addTab(activity_tab, "Activity")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Changes")
        save_btn.setIcon(qta.icon('fa5s.save'))
        save_btn.clicked.connect(self._save_changes)
        
        reset_password_btn = QPushButton("Reset Password")
        reset_password_btn.setIcon(qta.icon('fa5s.key'))
        reset_password_btn.clicked.connect(self._reset_password)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_password_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Populate permission lists
        self._populate_permission_lists()
    
    def _populate_fields(self):
        """Populate fields with user data"""
        self.username_edit.setText(self.user.username)
        self.email_edit.setText(self.user.email)
        self.full_name_edit.setText(self.user.full_name)
        self.phone_edit.setText(self.user.phone)
        self.department_edit.setText(self.user.department)
        self.is_active_check.setChecked(self.user.is_active)
        
        # Set role
        for i in range(self.role_combo.count()):
            if self.role_combo.itemData(i) == self.user.role:
                self.role_combo.setCurrentIndex(i)
                break
        
        # Activity information
        self.created_at_label.setText(self.user.created_at.strftime("%Y-%m-%d %H:%M"))
        self.last_login_label.setText(
            self.user.last_login.strftime("%Y-%m-%d %H:%M") if self.user.last_login else "Never"
        )
        self.failed_attempts_label.setText(str(self.user.failed_login_attempts))
        
        # Recent activity
        for activity in self.user.activity_log[-10:]:  # Last 10 activities
            item_text = f"[{activity.timestamp.strftime('%m-%d %H:%M')}] {activity.action} - {activity.resource}"
            self.activity_list.addItem(item_text)
    
    def _populate_permission_lists(self):
        """Populate the permission lists"""
        # All permissions for selection
        all_permissions = list(Permission)
        
        for permission in all_permissions:
            # Additional permissions (not from role)
            if permission in self.user.custom_permissions:
                item = QListWidgetItem(permission.value.replace('_', ' ').title())
                item.setData(Qt.UserRole, permission)
                item.setCheckState(Qt.Checked)
                self.additional_permissions.addItem(item)
            else:
                item = QListWidgetItem(permission.value.replace('_', ' ').title())
                item.setData(Qt.UserRole, permission)
                item.setCheckState(Qt.Unchecked)
                self.additional_permissions.addItem(item)
            
            # Disabled permissions
            if permission in self.user.disabled_permissions:
                item = QListWidgetItem(permission.value.replace('_', ' ').title())
                item.setData(Qt.UserRole, permission)
                item.setCheckState(Qt.Checked)
                self.disabled_permissions.addItem(item)
            else:
                item = QListWidgetItem(permission.value.replace('_', ' ').title())
                item.setData(Qt.UserRole, permission)
                item.setCheckState(Qt.Unchecked)
                self.disabled_permissions.addItem(item)
    
    def _save_changes(self):
        """Save user changes"""
        try:
            # Collect custom permissions
            custom_perms = set()
            for i in range(self.additional_permissions.count()):
                item = self.additional_permissions.item(i)
                if item.checkState() == Qt.Checked:
                    custom_perms.add(item.data(Qt.UserRole))
            
            # Collect disabled permissions
            disabled_perms = set()
            for i in range(self.disabled_permissions.count()):
                item = self.disabled_permissions.item(i)
                if item.checkState() == Qt.Checked:
                    disabled_perms.add(item.data(Qt.UserRole))
            
            # Update user
            self.user_manager.update_user(
                self.user.user_id,
                username=self.username_edit.text(),
                email=self.email_edit.text(),
                full_name=self.full_name_edit.text(),
                phone=self.phone_edit.text(),
                department=self.department_edit.text(),
                is_active=self.is_active_check.isChecked(),
                role=self.role_combo.currentData(),
                custom_permissions=custom_perms,
                disabled_permissions=disabled_perms
            )
            
            QMessageBox.information(self, "Changes Saved", "User information has been updated.")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save changes: {str(e)}")
    
    def _reset_password(self):
        """Reset user password"""
        password, ok = QLineEdit().getText(
            self, 
            "Reset Password", 
            "Enter new password:",
            QLineEdit.Password
        )
        
        if ok and password:
            if len(password) < 6:
                QMessageBox.warning(self, "Invalid Password", "Password must be at least 6 characters.")
                return
            
            try:
                self.user_manager.update_user(self.user.user_id, password=password)
                QMessageBox.information(self, "Password Reset", "Password has been reset successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Reset Error", f"Failed to reset password: {str(e)}")


class UserManagementTab(QWidget):
    """Main user management tab"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = get_user_manager()
        
        self._create_ui()
        
        # Load data after UI is created
        if hasattr(self, 'users_table'):
            self._load_users()
        
        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def _create_ui(self):
        """Create the user management UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Check if current user has permission to manage users
        if not self.user_manager.check_permission(Permission.MANAGE_USERS):
            # Show limited view for non-admin users
            self._create_limited_view(layout)
            return
        
        # Toolbar
        self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Main tabs
        self.tabs = QTabWidget()
        
        # Users tab
        self.users_widget = self._create_users_tab()
        self.tabs.addTab(self.users_widget, qta.icon('fa5s.users'), "Users")
        
        # Roles & Permissions tab
        self.roles_widget = self._create_roles_tab()
        self.tabs.addTab(self.roles_widget, qta.icon('fa5s.user-shield'), "Roles & Permissions")
        
        # Activity tab
        self.activity_widget = self._create_activity_tab()
        self.tabs.addTab(self.activity_widget, qta.icon('fa5s.history'), "Activity")
        
        # Statistics tab
        self.stats_widget = self._create_statistics_tab()
        self.tabs.addTab(self.stats_widget, qta.icon('fa5s.chart-bar'), "Statistics")
        
        layout.addWidget(self.tabs)
    
    def _create_limited_view(self, layout):
        """Create limited view for non-admin users"""
        # Header
        header_label = QLabel("User Information")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669; margin: 20px;")
        layout.addWidget(header_label)
        
        # Current user info
        if self.user_manager.current_user:
            user_group = QGroupBox("Your Account")
            user_layout = QFormLayout(user_group)
            
            user_layout.addRow("Name:", QLabel(self.user_manager.current_user.full_name))
            user_layout.addRow("Username:", QLabel(self.user_manager.current_user.username))
            user_layout.addRow("Email:", QLabel(self.user_manager.current_user.email))
            user_layout.addRow("Role:", QLabel(self.user_manager.current_user.role.value.replace('_', ' ').title()))
            user_layout.addRow("Department:", QLabel(self.user_manager.current_user.department or "Not specified"))
            
            last_login = self.user_manager.current_user.last_login
            user_layout.addRow("Last Login:", QLabel(
                last_login.strftime("%Y-%m-%d %H:%M") if last_login else "This session"
            ))
            
            layout.addWidget(user_group)
        
        # Permissions
        perms_group = QGroupBox("Your Permissions")
        perms_layout = QVBoxLayout(perms_group)
        
        if self.user_manager.current_user:
            permissions = self.user_manager.current_user.effective_permissions
            for permission in sorted(permissions, key=lambda p: p.value):
                perm_label = QLabel(f"• {permission.value.replace('_', ' ').title()}")
                perm_label.setStyleSheet("color: #059669;")
                perms_layout.addWidget(perm_label)
        
        layout.addWidget(perms_group)
        layout.addStretch()
    
    def _create_toolbar(self):
        """Create the toolbar"""
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Create user
        create_action = QAction(qta.icon('fa5s.user-plus'), "Create User", self)
        create_action.setToolTip("Create new user")
        create_action.triggered.connect(self._create_user)
        self.toolbar.addAction(create_action)
        
        self.toolbar.addSeparator()
        
        # Edit user
        edit_action = QAction(qta.icon('fa5s.user-edit'), "Edit User", self)
        edit_action.setToolTip("Edit selected user")
        edit_action.triggered.connect(self._edit_user)
        self.toolbar.addAction(edit_action)
        
        # Delete user
        delete_action = QAction(qta.icon('fa5s.user-times'), "Deactivate User", self)
        delete_action.setToolTip("Deactivate selected user")
        delete_action.triggered.connect(self._deactivate_user)
        self.toolbar.addAction(delete_action)
        
        self.toolbar.addSeparator()
        
        # Refresh
        refresh_action = QAction(qta.icon('fa5s.sync'), "Refresh", self)
        refresh_action.triggered.connect(self._refresh_data)
        self.toolbar.addAction(refresh_action)
        
        # Filter controls
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Filter:"))
        
        self.role_filter = QComboBox()
        self.role_filter.addItem("All Roles", None)
        for role in UserRole:
            self.role_filter.addItem(role.value.replace('_', ' ').title(), role)
        self.role_filter.currentTextChanged.connect(self._apply_filters)
        self.toolbar.addWidget(self.role_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Users", "Active Only", "Inactive Only"])
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        self.toolbar.addWidget(self.status_filter)
    
    def _create_users_tab(self):
        """Create the users management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "Name", "Username", "Email", "Role", "Department", "Status", "Last Login", "Actions"
        ])
        
        # Configure table
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.users_table.setColumnWidth(7, 150)
        
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.users_table)
        
        return widget
    
    def _create_roles_tab(self):
        """Create the roles and permissions tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Role permissions matrix
        matrix_group = QGroupBox("Role Permissions Matrix")
        matrix_layout = QVBoxLayout(matrix_group)
        
        self.permissions_table = QTableWidget()
        
        # Set up permissions matrix
        roles = list(UserRole)
        permissions = list(Permission)
        
        self.permissions_table.setRowCount(len(permissions))
        self.permissions_table.setColumnCount(len(roles) + 1)
        
        # Headers
        headers = ["Permission"] + [role.value.replace('_', ' ').title() for role in roles]
        self.permissions_table.setHorizontalHeaderLabels(headers)
        
        # Populate matrix
        for row, permission in enumerate(permissions):
            # Permission name
            perm_item = QTableWidgetItem(permission.value.replace('_', ' ').title())
            self.permissions_table.setItem(row, 0, perm_item)
            
            # Check each role
            for col, role in enumerate(roles):
                role_permissions = ROLE_PERMISSIONS.get(role, [])
                has_permission = permission in role_permissions
                
                check_item = QTableWidgetItem("✓" if has_permission else "")
                if has_permission:
                    check_item.setBackground(QColor(209, 250, 229))  # Green
                else:
                    check_item.setBackground(QColor(254, 242, 242))  # Red
                
                check_item.setTextAlignment(Qt.AlignCenter)
                self.permissions_table.setItem(row, col + 1, check_item)
        
        # Configure matrix table
        matrix_header = self.permissions_table.horizontalHeader()
        matrix_header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(roles) + 1):
            matrix_header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        matrix_layout.addWidget(self.permissions_table)
        layout.addWidget(matrix_group)
        
        return widget
    
    def _create_activity_tab(self):
        """Create the activity monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Activity list
        self.activity_list = QListWidget()
        layout.addWidget(self.activity_list)
        
        return widget
    
    def _create_statistics_tab(self):
        """Create the statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistics display
        self.stats_layout = QGridLayout()
        
        # User count cards
        self.total_users_card = self._create_stat_card("Total Users", "0", "#3B82F6")
        self.active_users_card = self._create_stat_card("Active Users", "0", "#10B981")
        self.recent_logins_card = self._create_stat_card("Recent Logins", "0", "#F59E0B")
        self.active_sessions_card = self._create_stat_card("Active Sessions", "0", "#8B5CF6")
        
        self.stats_layout.addWidget(self.total_users_card, 0, 0)
        self.stats_layout.addWidget(self.active_users_card, 0, 1)
        self.stats_layout.addWidget(self.recent_logins_card, 1, 0)
        self.stats_layout.addWidget(self.active_sessions_card, 1, 1)
        
        layout.addLayout(self.stats_layout)
        
        # Role distribution
        self.role_group = QGroupBox("Users by Role")
        self.role_layout = QFormLayout(self.role_group)
        layout.addWidget(self.role_group)
        
        layout.addStretch()
        return widget
    
    def _create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #6B7280; font-weight: 500;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
    
    def _load_users(self):
        """Load and display users"""
        self.current_users = self.user_manager.list_users(include_inactive=True)
        self._populate_users_table()
        self._update_statistics()
        self._update_activity()
    
    def _populate_users_table(self):
        """Populate the users table"""
        self.users_table.setRowCount(len(self.current_users))
        
        for row, user in enumerate(self.current_users):
            # Name
            name_item = QTableWidgetItem(user.full_name)
            name_item.setData(Qt.UserRole, user.user_id)
            self.users_table.setItem(row, 0, name_item)
            
            # Username
            username_item = QTableWidgetItem(user.username)
            self.users_table.setItem(row, 1, username_item)
            
            # Email
            email_item = QTableWidgetItem(user.email)
            self.users_table.setItem(row, 2, email_item)
            
            # Role
            role_item = QTableWidgetItem(user.role.value.replace('_', ' ').title())
            self.users_table.setItem(row, 3, role_item)
            
            # Department
            dept_item = QTableWidgetItem(user.department or "")
            self.users_table.setItem(row, 4, dept_item)
            
            # Status
            status_item = QTableWidgetItem("Active" if user.is_active else "Inactive")
            if user.is_active:
                status_item.setBackground(QColor(209, 250, 229))  # Green
            else:
                status_item.setBackground(QColor(254, 242, 242))  # Red
            self.users_table.setItem(row, 5, status_item)
            
            # Last login
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            login_item = QTableWidgetItem(last_login)
            self.users_table.setItem(row, 6, login_item)
            
            # Actions
            actions_widget = self._create_user_actions(user)
            self.users_table.setCellWidget(row, 7, actions_widget)
    
    def _create_user_actions(self, user: User):
        """Create action buttons for user row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(qta.icon('fa5s.edit'))
        edit_btn.setToolTip("Edit user")
        edit_btn.setMaximumSize(30, 25)
        edit_btn.clicked.connect(lambda: self._edit_specific_user(user))
        layout.addWidget(edit_btn)
        
        # Deactivate button
        if user.is_active:
            deactivate_btn = QPushButton()
            deactivate_btn.setIcon(qta.icon('fa5s.user-times'))
            deactivate_btn.setToolTip("Deactivate user")
            deactivate_btn.setMaximumSize(30, 25)
            deactivate_btn.clicked.connect(lambda: self._deactivate_specific_user(user))
            layout.addWidget(deactivate_btn)
        
        layout.addStretch()
        return widget
    
    def _update_statistics(self):
        """Update statistics display"""
        stats = self.user_manager.get_user_statistics()
        
        # Update cards
        self.total_users_card.value_label.setText(str(stats['total_users']))
        self.active_users_card.value_label.setText(str(stats['active_users']))
        self.recent_logins_card.value_label.setText(str(stats['recent_logins']))
        self.active_sessions_card.value_label.setText(str(stats['active_sessions']))
        
        # Update role distribution
        self._clear_form_layout(self.role_layout)
        for role, count in stats['role_counts'].items():
            if count > 0:
                self.role_layout.addRow(
                    role.replace('_', ' ').title() + ":",
                    QLabel(str(count))
                )
    
    def _update_activity(self):
        """Update activity display"""
        self.activity_list.clear()
        
        # Collect recent activities from all users
        all_activities = []
        for user in self.current_users:
            for activity in user.activity_log[-5:]:  # Last 5 per user
                all_activities.append((user.full_name, activity))
        
        # Sort by timestamp
        all_activities.sort(key=lambda x: x[1].timestamp, reverse=True)
        
        # Display recent activities
        for user_name, activity in all_activities[:20]:  # Top 20
            item_text = f"[{activity.timestamp.strftime('%m-%d %H:%M')}] {user_name}: {activity.action} - {activity.resource}"
            self.activity_list.addItem(item_text)
    
    def _clear_form_layout(self, layout):
        """Clear all items from a form layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _create_user(self):
        """Create a new user"""
        dialog = CreateUserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_data()
    
    def _edit_user(self):
        """Edit selected user"""
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a user to edit.")
            return
        
        user_id = self.users_table.item(selected_row, 0).data(Qt.UserRole)
        user = self.user_manager.get_user(user_id)
        
        if user:
            self._edit_specific_user(user)
    
    def _edit_specific_user(self, user: User):
        """Edit a specific user"""
        dialog = EditUserDialog(user, self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_data()
    
    def _deactivate_user(self):
        """Deactivate selected user"""
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a user to deactivate.")
            return
        
        user_id = self.users_table.item(selected_row, 0).data(Qt.UserRole)
        user = self.user_manager.get_user(user_id)
        
        if user:
            self._deactivate_specific_user(user)
    
    def _deactivate_specific_user(self, user: User):
        """Deactivate a specific user"""
        reply = QMessageBox.question(
            self,
            "Deactivate User",
            f"Are you sure you want to deactivate {user.full_name}?\n\nThis will prevent them from logging in.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.user_manager.delete_user(user.user_id):
                QMessageBox.information(self, "User Deactivated", f"{user.full_name} has been deactivated.")
                self._refresh_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to deactivate user.")
    
    def _apply_filters(self):
        """Apply current filters to user list"""
        all_users = self.user_manager.list_users(include_inactive=True)
        
        # Role filter
        role_filter = self.role_filter.currentData()
        if role_filter:
            all_users = [u for u in all_users if u.role == role_filter]
        
        # Status filter
        status_filter = self.status_filter.currentText()
        if status_filter == "Active Only":
            all_users = [u for u in all_users if u.is_active]
        elif status_filter == "Inactive Only":
            all_users = [u for u in all_users if not u.is_active]
        
        self.current_users = all_users
        self._populate_users_table()
    
    def _refresh_data(self):
        """Refresh all user data"""
        try:
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "Refresh Error", f"Failed to refresh user data:\n{str(e)}")