"""
Dashboard Tab showing key metrics.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout

class DashboardTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel = colonel_client
        layout = QVBoxLayout(self)
        header = QLabel('<h2>Dashboard</h2>')
        layout.addWidget(header)

        # Sample KPI cards
        grid = QGridLayout()
        kpis = [
            ('Total Leads', lambda: len(self.colonel.list_leads()) if self.colonel else 0),
            ('Active Campaigns', lambda: len([c for c in self.colonel.list_campaigns() if c['status']=='Active']) if self.colonel else 0),
            ('Qualified Leads', lambda: len([l for l in self.colonel.list_leads() if l['status']=='Qualified']) if self.colonel else 0),
            ('Pending Tasks', lambda: 5),  # placeholder
        ]
        for i, (title, func) in enumerate(kpis):
            box = QGroupBox()
            box_layout = QVBoxLayout()
            val = func()
            box_layout.addWidget(QLabel(f'<h3>{val}</h3>'))
            box_layout.addWidget(QLabel(title))
            box.setLayout(box_layout)
            grid.addWidget(box, i//2, i%2)

        layout.addLayout(grid)
        layout.addStretch()
