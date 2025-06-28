# desktop/src/ui/main_window.py
class MainWindow(QMainWindow):
    # ... existing code ...

    def create_leads_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.new_lead_btn = QPushButton("New Lead")
        self.new_lead_btn.clicked.connect(self.new_lead)
        toolbar.addWidget(self.new_lead_btn)
        
        self.import_btn = QPushButton("Import Leads")
        toolbar.addWidget(self.import_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Lead table
        self.lead_table = QTableWidget()
        self.lead_table.setColumnCount(6)
        self.lead_table.setHorizontalHeaderLabels([
            "Name", "Phone", "Email", "Source", "Status", "Last Contact"
        ])
        self.lead_table.setSortingEnabled(True)
        layout.addWidget(self.lead_table)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Leads")
        self.refresh_btn.clicked.connect(self.refresh_leads)
        layout.addWidget(self.refresh_btn)
        
        return widget

    @Slot()
    def refresh_leads(self):
        asyncio.create_task(self.fetch_leads())

    async def fetch_leads(self):
        """Fetch leads from database"""
        code = '''
import json
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://realestate:commander123@localhost:5432/realestate_db")
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT name, phone, email, source, status, last_contact FROM leads ORDER BY last_contact DESC LIMIT 50"
    ))
    leads = [dict(row) for row in result.mappings()]
    print(json.dumps(leads))
'''
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            try:
                leads = json.loads(result["output"])
                self.lead_table.setRowCount(len(leads))
                for row, lead in enumerate(leads):
                    self.lead_table.setItem(row, 0, QTableWidgetItem(lead["name"]))
                    self.lead_table.setItem(row, 1, QTableWidgetItem(lead["phone"]))
                    self.lead_table.setItem(row, 2, QTableWidgetItem(lead["email"]))
                    self.lead_table.setItem(row, 3, QTableWidgetItem(lead["source"]))
                    self.lead_table.setItem(row, 4, QTableWidgetItem(lead["status"]))
                    self.lead_table.setItem(row, 5, QTableWidgetItem(str(lead["last_contact"])))
            except Exception as e:
                print(f"Error loading leads: {e}")