"""
Marketing Automation Tab with model/view, search, and context actions.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableView, QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMenu, QMessageBox, QGroupBox, QTextEdit, QDateEdit
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, Slot, QDate
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
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.description_input = QTextEdit()
        self.target_audience_input = QLineEdit()

        layout.addRow('Name:', self.name_input)
        layout.addRow('Status:', self.status_input)
        layout.addRow('Start Date:', self.start_date_input)
        layout.addRow('Description:', self.description_input)
        layout.addRow('Target Audience:', self.target_audience_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'status': self.status_input.currentText(),
            'start_date': self.start_date_input.date().toString(Qt.ISODate),
            'description': self.description_input.toPlainText().strip(),
            'target_audience': self.target_audience_input.text().strip(),
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

        # Content Generation Group
        content_group = QGroupBox("AI Content Generation")
        content_layout = QFormLayout(content_group)

        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems(["Email", "SMS", "Social Media Post"])
        content_layout.addRow("Content Type:", self.content_type_combo)

        self.content_prompt_input = QLineEdit()
        self.content_prompt_input.setPlaceholderText("e.g., Promote a new listing at 123 Main St")
        content_layout.addRow("Prompt:", self.content_prompt_input)

        self.generate_content_btn = QPushButton("Generate Content")
        self.generate_content_btn.clicked.connect(self.generate_marketing_content)
        content_layout.addRow(self.generate_content_btn)

        self.generated_content_output = QTextEdit()
        self.generated_content_output.setReadOnly(True)
        self.generated_content_output.setPlaceholderText("Generated content will appear here...")
        content_layout.addRow("Generated Content:", self.generated_content_output)

        # Communication Group
        comm_group = QGroupBox("Send Communication")
        comm_layout = QFormLayout(comm_group)

        self.recipient_email_input = QLineEdit()
        self.recipient_email_input.setPlaceholderText("recipient@example.com")
        comm_layout.addRow("Recipient Email:", self.recipient_email_input)

        self.email_subject_input = QLineEdit()
        self.email_subject_input.setPlaceholderText("Subject of the email")
        comm_layout.addRow("Email Subject:", self.email_subject_input)

        self.send_email_btn = QPushButton("Send Email")
        self.send_email_btn.clicked.connect(self.send_email)
        comm_layout.addRow(self.send_email_btn)

        self.recipient_sms_input = QLineEdit()
        self.recipient_sms_input.setPlaceholderText("+15551234567")
        comm_layout.addRow("Recipient SMS:", self.recipient_sms_input)

        self.send_sms_btn = QPushButton("Send SMS")
        self.send_sms_btn.clicked.connect(self.send_sms)
        comm_layout.addRow(self.send_sms_btn)

        layout.addWidget(content_group)
        layout.addWidget(comm_group)

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

    @Slot()
    def generate_marketing_content(self):
        content_type = self.content_type_combo.currentText()
        prompt = self.content_prompt_input.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt for content generation.")
            return
        
        QMessageBox.information(self, "Generating Content", "Generating marketing content... This may take a moment.")
        asyncio.create_task(self._fetch_generated_content(content_type, prompt))

    async def _fetch_generated_content(self, content_type: str, prompt: str):
        try:
            generated_text = await self.colonel_client.generate_marketing_content(content_type, prompt)
            self.generated_content_output.setText(generated_text)
            QMessageBox.information(self, "Content Generated", "Marketing content generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during content generation: {e}")

    @Slot()
    def send_email(self):
        recipient = self.recipient_email_input.text().strip()
        subject = self.email_subject_input.text().strip()
        body = self.generated_content_output.toPlainText().strip()

        if not recipient or not subject or not body:
            QMessageBox.warning(self, "Input Error", "Please fill in recipient, subject, and generate content before sending email.")
            return
        
        QMessageBox.information(self, "Sending Email", "Attempting to send email...")
        asyncio.create_task(self._send_email_async(recipient, subject, body))

    async def _send_email_async(self, recipient: str, subject: str, body: str):
        try:
            success = await self.colonel_client.send_email(recipient, subject, body)
            if success:
                QMessageBox.information(self, "Email Sent", "Email sent successfully!")
            else:
                QMessageBox.warning(self, "Email Failed", "Failed to send email. Check logs for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while sending email: {e}")

    @Slot()
    def send_sms(self):
        recipient_phone = self.recipient_sms_input.text().strip()
        message = self.generated_content_output.toPlainText().strip()

        if not recipient_phone or not message:
            QMessageBox.warning(self, "Input Error", "Please fill in recipient phone and generate content before sending SMS.")
            return
        
        QMessageBox.information(self, "Sending SMS", "Attempting to send SMS...")
        asyncio.create_task(self._send_sms_async(recipient_phone, message))

    async def _send_sms_async(self, recipient_phone: str, message: str):
        try:
            success = await self.colonel_client.send_sms(recipient_phone, message)
            if success:
                QMessageBox.information(self, "SMS Sent", "SMS sent successfully!")
            else:
                QMessageBox.warning(self, "SMS Failed", "Failed to send SMS. Check logs for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while sending SMS: {e}")

    def load_data(self):
        campaigns = self.colonel_client.list_campaigns() if self.colonel_client else []
        self.model.update_campaigns(campaigns)

    def on_new_campaign(self):
        dlg = NewCampaignDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.create_campaign(**data)
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
        
        # Set date from string
        start_date_str = camp.get('start_date', '')
        if start_date_str:
            try:
                date_obj = QDate.fromString(start_date_str, Qt.ISODate)
                if date_obj.isValid():
                    dlg.start_date_input.setDate(date_obj)
            except Exception as e:
                print(f"Error parsing date: {e}")

        dlg.description_input.setPlainText(camp.get('description', ''))
        dlg.target_audience_input.setText(camp.get('target_audience', ''))
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
