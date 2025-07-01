"""
Kanban Board Widget for Task Management.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDrag, QPixmap, QPainter
from ui.modern_widgets import ModernCard
from core.enhanced_colonel_client import EnhancedColonelClient
import json

class KanbanColumn(QVBoxLayout):
    def __init__(self, title: str, parent=None):
        super().__init__()
        self.setAlignment(Qt.AlignTop)
        self.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 5px;")
        self.addWidget(self.title_label)

        self.card_area = QVBoxLayout()
        self.card_area.setAlignment(Qt.AlignTop)
        self.card_area.setSpacing(8)
        self.addLayout(self.card_area)

    def add_card(self, card_widget):
        self.card_area.addWidget(card_widget)

class KanbanBoardWidget(QWidget):
    task_status_changed = Signal(int, str) # task_id, new_status

    def __init__(self, colonel_client: EnhancedColonelClient, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.setAcceptDrops(True)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.columns = {}
        self._create_columns()
        self.load_tasks()

    def _create_columns(self):
        statuses = ["To Do", "In Progress", "Completed", "Blocked"]
        for status in statuses:
            column_frame = QFrame()
            column_frame.setFixedWidth(250)
            column_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 8px; padding: 10px;")
            column_layout = QVBoxLayout(column_frame)
            column_layout.setContentsMargins(5, 5, 5, 5)

            kanban_column = KanbanColumn(status)
            column_layout.addLayout(kanban_column)
            column_layout.addStretch()

            self.main_layout.addWidget(column_frame)
            self.columns[status] = kanban_column

    def load_tasks(self):
        # Clear existing cards
        for column in self.columns.values():
            while column.card_area.count():
                child = column.card_area.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        tasks = self.colonel_client.list_tasks()
        for task in tasks:
            task_card = self._create_task_card(task)
            if task['status'] in self.columns:
                self.columns[task['status']].add_card(task_card)
            else:
                # Default to 'To Do' if status is unknown
                self.columns["To Do"].add_card(task_card)

    def _create_task_card(self, task: dict):
        card = ModernCard(
            title=task.get('title', 'No Title'),
            subtitle=f"Due: {task.get('due_date', 'N/A')}",
            icon="fa5s.tasks"
        )
        card.task_id = task['id']
        card.current_status = task['status']
        card.setCursor(Qt.OpenHandCursor)
        card.mousePressEvent = lambda event, c=card: self._start_drag(event, c)
        return card

    def _start_drag(self, event, card):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = card.mimeData()
            mime_data.setText(json.dumps({'task_id': card.task_id, 'current_status': card.current_status}))
            drag.setMimeData(mime_data)

            pixmap = QPixmap(card.size())
            card.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = json.loads(event.mimeData().text())
        task_id = mime_data['task_id']
        old_status = mime_data['current_status']

        # Determine which column the card was dropped into
        target_column = None
        for status, column_layout in self.columns.items():
            # Check if the drop position is within the column's frame
            # This is a simplified check, more robust would involve checking widget geometry
            if column_layout.geometry().contains(event.pos()):
                target_column = status
                break
        
        if target_column and target_column != old_status:
            # Update task status in the backend
            self.colonel_client.update_task(task_id, {'status': target_column})
            self.load_tasks() # Reload tasks to reflect changes
            self.task_status_changed.emit(task_id, target_column)
            event.acceptProposedAction()
        else:
            event.ignore()
