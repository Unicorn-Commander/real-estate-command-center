"""
Tasks Management Tab with model/view and search.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableView, QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMenu, QMessageBox,
    QTextEdit, QDateEdit, QStackedWidget
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QDate, Slot
from ui.tasks_model import TasksModel
from ui.kanban_board_widget import KanbanBoardWidget
from core.enhanced_colonel_client import EnhancedColonelClient

class NewTaskDialog(QDialog):
    def __init__(self, colonel_client: EnhancedColonelClient, parent=None, task_data=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.setWindowTitle("New Task" if task_data is None else "Edit Task")
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.description_input = QTextEdit()
        self.due_date_input = QDateEdit(calendarPopup=True)
        self.due_date_input.setDate(QDate.currentDate())
        self.status_input = QComboBox()
        self.status_input.addItems(["To Do", "In Progress", "Completed", "Blocked"])
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High", "Urgent"])
        self.assigned_to_input = QLineEdit()
        self.lead_id_input = QLineEdit()
        self.property_id_input = QLineEdit()

        self.layout.addRow("Title:", self.title_input)
        self.layout.addRow("Description:", self.description_input)
        self.layout.addRow("Due Date:", self.due_date_input)
        self.layout.addRow("Status:", self.status_input)
        self.layout.addRow("Priority:", self.priority_input)
        self.layout.addRow("Assigned To:", self.assigned_to_input)
        self.layout.addRow("Lead ID:", self.lead_id_input)
        self.layout.addRow("Property ID:", self.property_id_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        if task_data:
            self._load_task_data(task_data)

    def _load_task_data(self, data):
        self.title_input.setText(data.get('title', ''))
        self.description_input.setText(data.get('description', ''))
        if data.get('due_date'):
            self.due_date_input.setDate(QDate.fromString(str(data['due_date']), Qt.ISODate))
        self.status_input.setCurrentText(data.get('status', ''))
        self.priority_input.setCurrentText(data.get('priority', ''))
        self.assigned_to_input.setText(data.get('assigned_to', ''))
        self.lead_id_input.setText(str(data.get('lead_id', '')) if data.get('lead_id') else '')
        self.property_id_input.setText(str(data.get('property_id', '')) if data.get('property_id') else '')

    def get_data(self):
        return {
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'due_date': self.due_date_input.date().toString(Qt.ISODate), # Store as YYYY-MM-DD string
            'status': self.status_input.currentText(),
            'priority': self.priority_input.currentText(),
            'assigned_to': self.assigned_to_input.text().strip(),
            'lead_id': int(self.lead_id_input.text().strip()) if self.lead_id_input.text().strip() else None,
            'property_id': int(self.property_id_input.text().strip()) if self.property_id_input.text().strip() else None,
        }

class TasksTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        layout = QVBoxLayout(self)

        # Search and button bar
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Type to filter tasks...')
        top_layout.addWidget(self.search_input)
        top_layout.addSpacing(20)
        self.refresh_btn = QPushButton("Refresh")
        self.new_btn = QPushButton("New Task")
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.new_btn)
        layout.addLayout(top_layout)

        # View selection buttons
        view_layout = QHBoxLayout()
        self.table_view_btn = QPushButton("Table View")
        self.table_view_btn.clicked.connect(self.show_table_view)
        view_layout.addWidget(self.table_view_btn)

        self.kanban_view_btn = QPushButton("Kanban View")
        self.kanban_view_btn.clicked.connect(self.show_kanban_view)
        view_layout.addWidget(self.kanban_view_btn)
        view_layout.addStretch()
        layout.addLayout(view_layout)

        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Table view
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.model = TasksModel([])
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        table_layout.addWidget(self.table)
        self.stacked_widget.addWidget(table_widget)

        # Kanban board view
        self.kanban_board = KanbanBoardWidget(self.colonel_client)
        self.kanban_board.task_status_changed.connect(self.load_data) # Reload data when status changes
        self.stacked_widget.addWidget(self.kanban_board)

        # Connections
        self.refresh_btn.clicked.connect(self.load_data)
        self.new_btn.clicked.connect(self.on_new_task)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)

        # Initial load and show default view
        self.load_data()
        self.show_table_view()

    def load_data(self):
        tasks = self.colonel_client.list_tasks() if self.colonel_client else []
        self.model.update_tasks(tasks)
        self.kanban_board.load_tasks()

    @Slot()
    def show_table_view(self):
        self.stacked_widget.setCurrentWidget(self.table.parentWidget())

    @Slot()
    def show_kanban_view(self):
        self.stacked_widget.setCurrentWidget(self.kanban_board)

    def load_data(self):
        tasks = self.colonel_client.list_tasks() if self.colonel_client else []
        self.model.update_tasks(tasks)

    def on_new_task(self):
        dlg = NewTaskDialog(self.colonel_client, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.create_task(data)
            self.load_data()

    def open_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        edit_action = menu.addAction('Edit Task')
        delete_action = menu.addAction('Delete Task')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        row = self.proxy.mapToSource(idx).row()
        if action == edit_action:
            self.edit_task(row)
        elif action == delete_action:
            self.delete_task(row)

    def edit_task(self, row):
        task = self.model._tasks[row]
        dlg = NewTaskDialog(self.colonel_client, self, task_data=task)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.update_task(task['id'], data)
            self.load_data()

    def delete_task(self, row):
        from PySide6.QtWidgets import QMessageBox
        task = self.model._tasks[row]
        resp = QMessageBox.question(
            self, 'Delete Task', f"Delete task {task.get('title')}?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes and self.colonel_client:
            self.colonel_client.delete_task(task['id'])
            self.load_data()
