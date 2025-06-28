"""
QAbstractTableModel for Database table stats.
"""
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class DatabaseModel(QAbstractTableModel):
    HEADERS = ['Table', 'Rows', 'Last Updated']

    def __init__(self, tables=None, parent=None):
        super().__init__(parent)
        self._tables = tables or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._tables)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        tbl = self._tables[index.row()]
        col = index.column()
        if col == 0:
            return tbl.get('name')
        elif col == 1:
            return tbl.get('rows')
        elif col == 2:
            return tbl.get('last_updated')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def update_tables(self, tables):
        self.beginResetModel()
        self._tables = tables
        self.endResetModel()
