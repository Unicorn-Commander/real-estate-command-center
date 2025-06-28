"""
Settings dialog for API endpoint and theme selection.
"""
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox

class SettingsDialog(QDialog):
    def __init__(self, current_url: str, current_theme: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setModal(True)
        self.resize(400, 150)
        layout = QFormLayout(self)

        # API endpoint
        self.url_input = QLineEdit(current_url)
        layout.addRow('API Endpoint:', self.url_input)

        # Theme selector
        self.theme_combo = QComboBox()
        themes = ['dark_amber.xml', 'light_blue.xml', 'dark_light.xml', 'light_pink.xml']
        self.theme_combo.addItems(themes)
        if current_theme in themes:
            self.theme_combo.setCurrentText(current_theme)
        layout.addRow('Theme:', self.theme_combo)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return self.url_input.text().strip(), self.theme_combo.currentText()
