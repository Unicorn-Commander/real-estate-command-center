"""
Marketing Automation Tab with model/view, search, and context actions.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableView, QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from ui.campaign_model import CampaignModel

class NewCampaignDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('New Campaign')
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Planned', 'Active', 'Completed', 'Paused'])
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText('YYYY-MM-DD')

        layout.addRow('Name:', self.name_input)
        layout.addRow('Status:', self.status_input)
        layout.addRow('Start Date:', self.date_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'status': self.status_input.currentText(),
            'start_date': self.date_input.text().strip(),
        }

class MarketingTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        layout = QVBoxLayout(self)

        # Search and buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Filter campaigns...')
        top_layout.addWidget(self.search_input)
        top_layout.addSpacing(20)
        self.refresh_btn = QPushButton('Refresh Campaigns')
        self.new_btn = QPushButton('New Campaign')
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.new_btn)
        layout.addLayout(top_layout)

        # Model and view
        self.model = CampaignModel([])
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.table)

        # Connections
        self.refresh_btn.clicked.connect(self.load_data)
        self.new_btn.clicked.connect(self.on_new_campaign)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)

        # Initial load
        self.load_data()

    def load_data(self):
        campaigns = self.colonel_client.list_campaigns() if self.colonel_client else []
        self.model.update_campaigns(campaigns)

    def on_new_campaign(self):
        dlg = NewCampaignDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.create_campaign(data['name'], data['status'], data['start_date'])
            self.load_data()

    def open_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        edit = menu.addAction('Edit Campaign')
        delete = menu.addAction('Delete Campaign')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        row = self.proxy.mapToSource(idx).row()
        if action == edit:
            self.edit_campaign(row)
        elif action == delete:
            self.delete_campaign(row)

    def edit_campaign(self, row):
        camp = self.model._campaigns[row]
        dlg = NewCampaignDialog(self)
        dlg.name_input.setText(camp.get('name', ''))
        idx = dlg.status_input.findText(camp.get('status', ''))
        if idx >= 0:
            dlg.status_input.setCurrentIndex(idx)
        dlg.date_input.setText(camp.get('start_date', ''))
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.update_campaign(camp['id'], data)
            self.load_data()

    def delete_campaign(self, row):
        camp = self.model._campaigns[row]
        resp = QMessageBox.question(
            self, 'Delete Campaign', f"Delete campaign {camp.get('name')}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes and self.colonel_client:
            self.colonel_client.delete_campaign(camp['id'])
            self.load_data()
