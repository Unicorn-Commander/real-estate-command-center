"""
Database Dashboard Tab with model/view, search, and export.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableView, QLabel, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from ui.database_model import DatabaseModel

class DatabaseTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        layout = QVBoxLayout(self)

        # Search and buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Filter tables...')
        top_layout.addWidget(self.search_input)
        top_layout.addSpacing(20)
        self.refresh_btn = QPushButton('Refresh')
        self.export_btn = QPushButton('Export CSV')
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.export_btn)
        layout.addLayout(top_layout)

        # Model and view
        self.model = DatabaseModel([])
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.table)

        # Connections
        self.refresh_btn.clicked.connect(self.load_data)
        self.export_btn.clicked.connect(self.export_csv)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)

        # Initial load
        self.load_data()

    def load_data(self):
        # Stub: fetch table stats from colonel_client if available
        tables = []
        if self.colonel_client and hasattr(self.colonel_client, 'list_tables'):
            tables = self.colonel_client.list_tables()
        else:
            # Sample data
            tables = [
                {'name': 'leads', 'rows': 123, 'last_updated': '2024-06-10'},
                {'name': 'campaigns', 'rows': 45, 'last_updated': '2024-06-08'},
                {'name': 'clients', 'rows': 67, 'last_updated': '2024-06-09'},
            ]
        self.model.update_tables(tables)

    def export_csv(self):
        # Stub: show confirmation
        QMessageBox.information(self, 'Export', 'CSV export not yet implemented.')

    def open_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        refresh = menu.addAction('Refresh Stats')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == refresh:
            self.load_data()
