"""
Leads Management Tab with model/view and search.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QTableView, QLabel
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from ui.leads_model import LeadsModel

class NewLeadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Lead")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(["New", "Contacted", "Qualified", "Lost"])

        layout.addRow("Name:", self.name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Status:", self.status_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'email': self.email_input.text().strip(),
            'status': self.status_input.currentText(),
        }

class LeadsTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        layout = QVBoxLayout(self)

        # Search and button bar
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Type to filter leads...')
        top_layout.addWidget(self.search_input)
        top_layout.addSpacing(20)
        self.refresh_btn = QPushButton("Refresh")
        self.new_btn = QPushButton("New Lead")
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.new_btn)
        layout.addLayout(top_layout)

        # Table view with model and proxy
        self.model = LeadsModel([])
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        # Context menu for edit/delete
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Connections
        self.refresh_btn.clicked.connect(self.load_data)
        self.new_btn.clicked.connect(self.on_new_lead)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)

        # Initial load
        self.load_data()

    def load_data(self):
        leads = self.colonel_client.list_leads() if self.colonel_client else []
        self.model.update_leads(leads)

    def on_new_lead(self):
        dlg = NewLeadDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.create_lead(data['name'], data['email'], data['status'])
            self.load_data()

    def open_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        edit_action = menu.addAction('Edit Lead')
        delete_action = menu.addAction('Delete Lead')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        row = self.proxy.mapToSource(idx).row()
        if action == edit_action:
            self.edit_lead(row)
        elif action == delete_action:
            self.delete_lead(row)

    def edit_lead(self, row):
        lead = self.model._leads[row]
        dlg = NewLeadDialog(self)
        dlg.name_input.setText(lead.get('name', ''))
        dlg.email_input.setText(lead.get('email', ''))
        idx = dlg.status_input.findText(lead.get('status', ''))
        if idx >= 0:
            dlg.status_input.setCurrentIndex(idx)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            # Update in client
            if self.colonel_client:
                lead['name'] = data['name']
                lead['email'] = data['email']
                lead['status'] = data['status']
            self.load_data()

    def delete_lead(self, row):
        from PySide6.QtWidgets import QMessageBox
        lead = self.model._leads[row]
        resp = QMessageBox.question(
            self, 'Delete Lead', f"Delete lead {lead.get('name')}?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes and self.colonel_client:
            # Remove from client store
            self.colonel_client._leads.pop(row)
            self.load_data()
