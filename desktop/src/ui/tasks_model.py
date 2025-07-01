"""
QAbstractTableModel for Tasks data.
"""
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class TasksModel(QAbstractTableModel):
    HEADERS = [
        'ID', 'Title', 'Description', 'Due Date', 'Status', 'Priority', 'Assigned To', 'Lead ID', 'Property ID'
    ]

    def __init__(self, tasks=None, parent=None):
        super().__init__(parent)
        self._tasks = tasks or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._tasks)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        task = self._tasks[index.row()]
        col = index.column()
        
        if col == 0: return task.get('id')
        elif col == 1: return task.get('title')
        elif col == 2: return task.get('description')
        elif col == 3: return str(task.get('due_date', '')) # Convert date to string
        elif col == 4: return task.get('status')
        elif col == 5: return task.get('priority')
        elif col == 6: return task.get('assigned_to')
        elif col == 7: return task.get('lead_id')
        elif col == 8: return task.get('property_id')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def update_tasks(self, tasks):
        self.beginResetModel()
        self._tasks = tasks
        self.endResetModel()
