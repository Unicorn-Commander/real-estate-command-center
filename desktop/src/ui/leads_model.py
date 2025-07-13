"""
QAbstractTableModel for Leads data.
"""
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class LeadsModel(QAbstractTableModel):
    HEADERS = ['ID', 'Name', 'Email', 'Phone', 'Source', 'Status', 'Notes']

    def __init__(self, leads=None, parent=None):
        super().__init__(parent)
        self._leads = leads or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._leads)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        lead = self._leads[index.row()]
        col = index.column()
        if col == 0:
            return lead.get('id')
        elif col == 1:
            return lead.get('name')
        elif col == 2:
            return lead.get('email')
        elif col == 3:
            return lead.get('phone')
        elif col == 4:
            return lead.get('source')
        elif col == 5:
            return lead.get('status')
        elif col == 6:
            return lead.get('notes')
        elif col == 4:
            return lead.get('source')
        elif col == 5:
            return lead.get('status')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def update_leads(self, leads):
        self.beginResetModel()
        self._leads = leads
        self.endResetModel()
