class MainWindow(QMainWindow):
    # ... existing code ...

    def create_marketing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Campaign creation
        campaign_group = QGroupBox("Create New Campaign")
        campaign_layout = QVBoxLayout(campaign_group)
        
        self.campaign_type = QComboBox()
        self.campaign_type.addItems([
            "Listing Promotion", 
            "Open House", 
            "Market Update",
            "Client Newsletter"
        ])
        campaign_layout.addWidget(QLabel("Campaign Type:"))
        campaign_layout.addWidget(self.campaign_type)
        
        self.template_selector = QComboBox()
        self.template_selector.addItems(["Modern", "Classic", "Luxury", "Minimalist"])
        campaign_layout.addWidget(QLabel("Template:"))
        campaign_layout.addWidget(self.template_selector)
        
        self.generate_btn = QPushButton("Generate Content")
        self.generate_btn.clicked.connect(self.generate_marketing)
        campaign_layout.addWidget(self.generate_btn)
        
        layout.addWidget(campaign_group)
        
        # Preview area
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview_area)
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_pdf = QPushButton("Export PDF")
        self.export_html = QPushButton("Export HTML")
        self.schedule_btn = QPushButton("Schedule Posts")
        export_layout.addWidget(self.export_pdf)
        export_layout.addWidget(self.export_html)
        export_layout.addWidget(self.schedule_btn)
        layout.addLayout(export_layout)
        
        return widget

    @Slot()
    def generate_marketing(self):
        campaign_type = self.campaign_type.currentText()
        template = self.template_selector.currentText()
        asyncio.create_task(self.create_marketing_content(campaign_type, template))

    async def create_marketing_content(self, campaign_type, template):
        """Generate marketing content using AI"""
        code = f'''
import json
from datetime import datetime

# This would use Ollama to generate content
prompt = f"Create a real estate marketing campaign for {{campaign_type}} using the {{template}} template."
# In practice, we'd use the Colonel's chat API

# For demo, return mock content
content = {{
    "text": f"✨ **New {campaign_type} Campaign** ✨\\n\\nBeautiful property now available...",
    "generated_at": datetime.now().isoformat()
}}

print(json.dumps(content))
'''
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            try:
                content = json.loads(result["output"])
                self.preview_area.setHtml(content["text"])
            except Exception as e:
                print(f"Error generating content: {e}")