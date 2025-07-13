"""
Properties Management Tab with model/view and search.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QTableView, QLabel, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal, Slot
from ui.properties_model import PropertiesModel
from core.enhanced_colonel_client import EnhancedColonelClient
import asyncio

class NewPropertyDialog(QDialog):
    property_data_fetched = Signal(dict)

    def __init__(self, colonel_client: EnhancedColonelClient, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.setWindowTitle("New Property")
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., 123 Main St, Anytown, CA 90210")
        self.lookup_btn = QPushButton("Lookup Property")
        self.lookup_btn.clicked.connect(self.lookup_property_data)

        address_layout = QHBoxLayout()
        address_layout.addWidget(self.address_input)
        address_layout.addWidget(self.lookup_btn)
        self.layout.addRow("Address:", address_layout)

        self.city_input = QLineEdit()
        self.state_input = QLineEdit()
        self.zip_input = QLineEdit()
        self.property_type_input = QComboBox()
        self.property_type_input.addItems(["Single Family", "Condo", "Townhouse", "Multi Family", "Land", "Commercial", "Other"])
        self.bedrooms_input = QSpinBox()
        self.bedrooms_input.setRange(0, 10)
        self.bathrooms_input = QDoubleSpinBox()
        self.bathrooms_input.setRange(0.0, 10.0)
        self.bathrooms_input.setSingleStep(0.5)
        self.square_feet_input = QSpinBox()
        self.square_feet_input.setRange(0, 100000)
        self.square_feet_input.setSingleStep(100)
        self.lot_size_input = QSpinBox()
        self.lot_size_input.setRange(0, 1000000)
        self.lot_size_input.setSingleStep(1000)
        self.year_built_input = QSpinBox()
        self.year_built_input.setRange(1700, 2100)
        self.listing_price_input = QSpinBox()
        self.listing_price_input.setRange(0, 1000000000)
        self.listing_price_input.setSingleStep(1000)
        self.listing_price_input.setPrefix("$")
        self.listing_status_input = QComboBox()
        self.listing_status_input.addItems(["Active", "Pending", "Sold", "Off Market", "Coming Soon"])
        self.mls_id_input = QLineEdit()

        self.layout.addRow("City:", self.city_input)
        self.layout.addRow("State:", self.state_input)
        self.layout.addRow("Zip Code:", self.zip_input)
        self.layout.addRow("Property Type:", self.property_type_input)
        self.layout.addRow("Bedrooms:", self.bedrooms_input)
        self.layout.addRow("Bathrooms:", self.bathrooms_input)
        self.layout.addRow("Square Feet:", self.square_feet_input)
        self.layout.addRow("Lot Size (sqft):", self.lot_size_input)
        self.layout.addRow("Year Built:", self.year_built_input)
        self.layout.addRow("Listing Price:", self.listing_price_input)
        self.layout.addRow("Listing Status:", self.listing_status_input)
        self.layout.addRow("MLS ID:", self.mls_id_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.property_data_fetched.connect(self.fill_form_with_data)

    def get_data(self):
        return {
            'address': self.address_input.text().strip(),
            'city': self.city_input.text().strip(),
            'state': self.state_input.text().strip(),
            'zip_code': self.zip_input.text().strip(),
            'property_type': self.property_type_input.currentText(),
            'bedrooms': self.bedrooms_input.value(),
            'bathrooms': self.bathrooms_input.value(),
            'square_feet': self.square_feet_input.value(),
            'lot_size': self.lot_size_input.value(),
            'year_built': self.year_built_input.value(),
            'listing_price': self.listing_price_input.value(),
            'listing_status': self.listing_status_input.currentText(),
            'mls_id': self.mls_id_input.text().strip(),
        }

    @Slot()
    def lookup_property_data(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Input Error", "Please enter an address to lookup.")
            return
        
        QMessageBox.information(self, "Lookup", "Attempting to lookup property data... This may take a moment.")
        asyncio.create_task(self._fetch_property_data(address))

    async def _fetch_property_data(self, address: str):
        try:
            # Use the property_service from the colonel_client
            property_info = self.colonel_client.property_service.lookup_property(address)
            if property_info and not property_info.get('error'):
                self.property_data_fetched.emit(property_info)
                QMessageBox.information(self, "Lookup Success", "Property data fetched successfully!")
            else:
                error_msg = property_info.get('error', 'Unknown error during lookup.')
                QMessageBox.warning(self, "Lookup Failed", f"Could not fetch property data: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during property lookup: {e}")

    @Slot(dict)
    def fill_form_with_data(self, data: dict):
        prop_data = data.get('property', {})
        market_data = data.get('market', {})
        address_details = data.get('location', {}).get('address_details', {})

        self.city_input.setText(address_details.get('city', ''))
        self.state_input.setText(address_details.get('state', ''))
        self.zip_input.setText(address_details.get('postcode', ''))
        
        # Map property type
        prop_type = prop_data.get('type', '')
        idx = self.property_type_input.findText(prop_type, Qt.MatchContains)
        if idx >= 0: self.property_type_input.setCurrentIndex(idx)

        self.bedrooms_input.setValue(prop_data.get('bedrooms', 0))
        self.bathrooms_input.setValue(prop_data.get('bathrooms', 0.0))
        self.square_feet_input.setValue(prop_data.get('square_feet', 0))
        self.lot_size_input.setValue(prop_data.get('lot_size', 0))
        self.year_built_input.setValue(prop_data.get('year_built', 0))
        self.listing_price_input.setValue(prop_data.get('estimated_value', 0))
        
        # Attempt to infer status if not directly available
        if prop_data.get('status'):
            idx = self.listing_status_input.findText(prop_data['status'], Qt.MatchContains)
            if idx >= 0: self.listing_status_input.setCurrentIndex(idx)
        
        self.mls_id_input.setText(prop_data.get('mls_id', ''))

class PropertiesTab(QWidget):
    def __init__(self, colonel_client=None, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        layout = QVBoxLayout(self)

        # Search and button bar
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Type to filter properties...')
        top_layout.addWidget(self.search_input)
        top_layout.addSpacing(20)
        self.refresh_btn = QPushButton("Refresh")
        self.new_btn = QPushButton("New Property")
        top_layout.addWidget(self.refresh_btn)
        top_layout.addWidget(self.new_btn)
        layout.addLayout(top_layout)

        # Table view with model and proxy
        self.model = PropertiesModel([])
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        # Context menu for edit/delete
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Connections
        self.refresh_btn.clicked.connect(self.load_data)
        self.new_btn.clicked.connect(self.on_new_property)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)

        # Initial load
        self.load_data()

    def load_data(self):
        properties = self.colonel_client.list_properties() if self.colonel_client else []
        self.model.update_properties(properties)

    def on_new_property(self):
        dlg = NewPropertyDialog(self.colonel_client, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.create_property(data)
            self.load_data()

    def open_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        edit_action = menu.addAction('Edit Property')
        delete_action = menu.addAction('Delete Property')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        row = self.proxy.mapToSource(idx).row()
        if action == edit_action:
            self.edit_property(row)
        elif action == delete_action:
            self.delete_property(row)

    def edit_property(self, row):
        prop = self.proxy.mapToSource(self.table.model().index(row, 0)).data(Qt.UserRole)
        if not prop:
            QMessageBox.warning(self, "Edit Property", "Could not retrieve property data for editing.")
            return

        dlg = NewPropertyDialog(self.colonel_client, self)
        # Populate dialog with existing data
        dlg.address_input.setText(prop.get('address', ''))
        dlg.city_input.setText(prop.get('city', ''))
        dlg.state_input.setText(prop.get('state', ''))
        dlg.zip_input.setText(prop.get('zip_code', ''))
        dlg.property_type_input.setCurrentText(prop.get('property_type', ''))
        dlg.bedrooms_input.setValue(prop.get('bedrooms', 0))
        dlg.bathrooms_input.setValue(prop.get('bathrooms', 0.0))
        dlg.square_feet_input.setValue(prop.get('square_feet', 0))
        dlg.lot_size_input.setValue(prop.get('lot_size', 0))
        dlg.year_built_input.setValue(prop.get('year_built', 0))
        dlg.listing_price_input.setValue(prop.get('listing_price', 0.0))
        dlg.listing_status_input.setCurrentText(prop.get('listing_status', ''))
        dlg.mls_id_input.setText(prop.get('mls_id', ''))

        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if self.colonel_client:
                self.colonel_client.update_property(prop['id'], data)
            self.load_data()

    def delete_property(self, row):
        from PySide6.QtWidgets import QMessageBox
        prop = self.model._properties[row]
        resp = QMessageBox.question(
            self, 'Delete Property', f"Delete property {prop.get('address')}?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes and self.colonel_client:
            self.colonel_client.delete_property(prop['id'])
            self.load_data()
