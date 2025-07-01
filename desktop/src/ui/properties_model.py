"""
QAbstractTableModel for Properties data.
"""
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class PropertiesModel(QAbstractTableModel):
    HEADERS = [
        'ID', 'Address', 'City', 'State', 'Zip', 'Type', 'Beds', 'Baths',
        'SqFt', 'Lot Size', 'Year Built', 'Price', 'Status', 'MLS ID'
    ]

    def __init__(self, properties=None, parent=None):
        super().__init__(parent)
        self._properties = properties or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._properties)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        prop = self._properties[index.row()]
        col = index.column()
        
        if col == 0: return prop.get('id')
        elif col == 1: return prop.get('address')
        elif col == 2: return prop.get('city')
        elif col == 3: return prop.get('state')
        elif col == 4: return prop.get('zip_code')
        elif col == 5: return prop.get('property_type')
        elif col == 6: return prop.get('bedrooms')
        elif col == 7: return prop.get('bathrooms')
        elif col == 8: return prop.get('square_feet')
        elif col == 9: return prop.get('lot_size')
        elif col == 10: return prop.get('year_built')
        elif col == 11: return f"${prop.get('listing_price', 0):,.0f}"
        elif col == 12: return prop.get('listing_status')
        elif col == 13: return prop.get('mls_id')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def update_properties(self, properties):
        self.beginResetModel()
        self._properties = properties
        self.endResetModel()
