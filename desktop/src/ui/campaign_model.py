"""
QAbstractTableModel for Campaign data.
"""
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class CampaignModel(QAbstractTableModel):
    HEADERS = ['ID', 'Name', 'Status', 'Start Date']

    def __init__(self, campaigns=None, parent=None):
        super().__init__(parent)
        self._campaigns = campaigns or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._campaigns)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        camp = self._campaigns[index.row()]
        col = index.column()
        if col == 0:
            return camp.get('id')
        elif col == 1:
            return camp.get('name')
        elif col == 2:
            return camp.get('status')
        elif col == 3:
            return camp.get('start_date')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def update_campaigns(self, campaigns):
        self.beginResetModel()
        self._campaigns = campaigns
        self.endResetModel()
