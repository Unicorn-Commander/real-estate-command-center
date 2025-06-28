"""
Interactive map widget for property location visualization in CMA reports.
"""
import os
import folium
from typing import Dict, List, Tuple, Optional
import tempfile
import webbrowser
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QSplitter, QFrame, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView


class GeocodeThread(QThread):
    """Background thread for geocoding addresses."""
    
    location_found = Signal(float, float, str)  # lat, lng, formatted_address
    geocoding_failed = Signal(str)  # error message
    
    def __init__(self, address: str):
        super().__init__()
        self.address = address
    
    def run(self):
        """Geocode address using a simple approach."""
        try:
            # For demo purposes, use approximate coordinates based on common city names
            # In production, this would use a real geocoding API like Google Maps or OpenStreetMap
            demo_locations = {
                'new york': (40.7128, -74.0060),
                'los angeles': (34.0522, -118.2437),
                'chicago': (41.8781, -87.6298),
                'houston': (29.7604, -95.3698),
                'phoenix': (33.4484, -112.0740),
                'philadelphia': (39.9526, -75.1652),
                'san antonio': (29.4241, -98.4936),
                'san diego': (32.7157, -117.1611),
                'dallas': (32.7767, -96.7970),
                'san jose': (37.3382, -121.8863),
                'boston': (42.3601, -71.0589),
                'seattle': (47.6062, -122.3321),
                'denver': (39.7392, -104.9903),
                'atlanta': (33.7490, -84.3880),
                'miami': (25.7617, -80.1918)
            }
            
            # Simple lookup for demo
            address_lower = self.address.lower()
            for city, coords in demo_locations.items():
                if city in address_lower:
                    self.location_found.emit(coords[0], coords[1], f"{self.address} (Approximate)")
                    return
            
            # Default location if no match found (San Francisco)
            self.location_found.emit(37.7749, -122.4194, f"{self.address} (Default Location)")
            
        except Exception as e:
            self.geocoding_failed.emit(f"Geocoding failed: {str(e)}")


class PropertyMapWidget(QWidget):
    """Interactive map widget for displaying property locations and comparables."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_file = None
        self.subject_location = None
        self.comparable_locations = []
        
        self.init_ui()
        self.setup_signals()
    
    def init_ui(self):
        """Initialize the map widget UI."""
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Property Location Map")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Map controls
        self.btn_refresh_map = QPushButton(qta.icon('fa5s.sync'), "Refresh")
        self.btn_fullscreen = QPushButton(qta.icon('fa5s.expand'), "Fullscreen")
        self.btn_export_map = QPushButton(qta.icon('fa5s.download'), "Export")
        
        header_layout.addWidget(self.btn_refresh_map)
        header_layout.addWidget(self.btn_fullscreen)
        header_layout.addWidget(self.btn_export_map)
        
        layout.addLayout(header_layout)
        
        # Address input section
        address_group = QGroupBox("Property Address")
        address_layout = QHBoxLayout()
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter property address to map...")
        
        self.btn_geocode = QPushButton(qta.icon('fa5s.map-marker'), "Locate")
        self.btn_geocode.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a5490;
            }
        """)
        
        address_layout.addWidget(self.address_input)
        address_layout.addWidget(self.btn_geocode)
        
        address_group.setLayout(address_layout)
        layout.addWidget(address_group)
        
        # Map display area
        map_group = QGroupBox("Interactive Map")
        map_layout = QVBoxLayout()
        
        # Web view for displaying the map
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)
        map_layout.addWidget(self.web_view)
        
        # Map options
        options_layout = QHBoxLayout()
        
        self.show_subject_check = QCheckBox("Subject Property")
        self.show_subject_check.setChecked(True)
        self.show_comparables_check = QCheckBox("Comparable Properties")
        self.show_comparables_check.setChecked(True)
        self.show_amenities_check = QCheckBox("Local Amenities")
        self.show_schools_check = QCheckBox("Schools")
        
        options_layout.addWidget(self.show_subject_check)
        options_layout.addWidget(self.show_comparables_check)
        options_layout.addWidget(self.show_amenities_check)
        options_layout.addWidget(self.show_schools_check)
        options_layout.addStretch()
        
        map_layout.addLayout(options_layout)
        
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
        # Status and info
        self.status_label = QLabel("Enter an address to display on the map")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Load initial default map
        self.create_default_map()\n    \n    def setup_signals(self):\n        \"\"\"Connect signals and slots.\"\"\"\n        self.btn_geocode.clicked.connect(self.geocode_address)\n        self.btn_refresh_map.clicked.connect(self.refresh_map)\n        self.btn_fullscreen.clicked.connect(self.open_fullscreen_map)\n        self.btn_export_map.clicked.connect(self.export_map)\n        \n        # Map option checkboxes\n        self.show_subject_check.toggled.connect(self.refresh_map)\n        self.show_comparables_check.toggled.connect(self.refresh_map)\n        self.show_amenities_check.toggled.connect(self.refresh_map)\n        self.show_schools_check.toggled.connect(self.refresh_map)\n        \n        # Enter key in address input\n        self.address_input.returnPressed.connect(self.geocode_address)\n    \n    def create_default_map(self):\n        \"\"\"Create a default map centered on a major city.\"\"\"\n        try:\n            # Create folium map centered on San Francisco\n            m = folium.Map(\n                location=[37.7749, -122.4194],\n                zoom_start=12,\n                tiles='OpenStreetMap'\n            )\n            \n            # Add a sample marker\n            folium.Marker(\n                [37.7749, -122.4194],\n                popup=\"Sample Location\",\n                tooltip=\"Click for property details\",\n                icon=folium.Icon(color='blue', icon='home', prefix='fa')\n            ).add_to(m)\n            \n            # Save and display map\n            self.save_and_display_map(m)\n            self.status_label.setText(\"Default map loaded - Enter address to customize\")\n            \n        except Exception as e:\n            self.status_label.setText(f\"Error creating default map: {str(e)}\")\n    \n    def geocode_address(self):\n        \"\"\"Geocode the entered address and update map.\"\"\"\n        address = self.address_input.text().strip()\n        if not address:\n            QMessageBox.warning(self, \"Input Required\", \"Please enter an address to locate.\")\n            return\n        \n        self.status_label.setText(\"Locating address...\")\n        self.btn_geocode.setEnabled(False)\n        \n        # Start geocoding thread\n        self.geocode_thread = GeocodeThread(address)\n        self.geocode_thread.location_found.connect(self.on_location_found)\n        self.geocode_thread.geocoding_failed.connect(self.on_geocoding_failed)\n        self.geocode_thread.start()\n    \n    def on_location_found(self, lat: float, lng: float, formatted_address: str):\n        \"\"\"Handle successful geocoding result.\"\"\"\n        self.subject_location = (lat, lng, formatted_address)\n        self.create_property_map()\n        self.status_label.setText(f\"Property located: {formatted_address}\")\n        self.btn_geocode.setEnabled(True)\n    \n    def on_geocoding_failed(self, error_message: str):\n        \"\"\"Handle geocoding failure.\"\"\"\n        self.status_label.setText(f\"Geocoding failed: {error_message}\")\n        self.btn_geocode.setEnabled(True)\n        QMessageBox.warning(self, \"Geocoding Error\", error_message)\n    \n    def create_property_map(self):\n        \"\"\"Create a detailed property map with subject and comparables.\"\"\"\n        if not self.subject_location:\n            return\n        \n        try:\n            lat, lng, address = self.subject_location\n            \n            # Create map centered on subject property\n            m = folium.Map(\n                location=[lat, lng],\n                zoom_start=14,\n                tiles='OpenStreetMap'\n            )\n            \n            # Add subject property marker\n            if self.show_subject_check.isChecked():\n                folium.Marker(\n                    [lat, lng],\n                    popup=f\"<b>Subject Property</b><br>{address}\",\n                    tooltip=\"Subject Property\",\n                    icon=folium.Icon(color='red', icon='home', prefix='fa')\n                ).add_to(m)\n            \n            # Add comparable properties\n            if self.show_comparables_check.isChecked():\n                self.add_comparable_markers(m, lat, lng)\n            \n            # Add local amenities\n            if self.show_amenities_check.isChecked():\n                self.add_amenity_markers(m, lat, lng)\n            \n            # Add schools\n            if self.show_schools_check.isChecked():\n                self.add_school_markers(m, lat, lng)\n            \n            # Add search radius circle\n            folium.Circle(\n                location=[lat, lng],\n                radius=1609,  # 1 mile in meters\n                popup=\"1 mile search radius\",\n                color=\"blue\",\n                fill=True,\n                fillOpacity=0.1\n            ).add_to(m)\n            \n            # Save and display updated map\n            self.save_and_display_map(m)\n            \n        except Exception as e:\n            self.status_label.setText(f\"Error creating property map: {str(e)}\")\n    \n    def add_comparable_markers(self, m, center_lat: float, center_lng: float):\n        \"\"\"Add comparable property markers around the subject property.\"\"\"\n        # Sample comparable properties (in production, these would come from MLS data)\n        comparables = [\n            (center_lat + 0.005, center_lng + 0.003, \"456 Nearby Ave\", \"$475,000\", \"Sold 05/15/24\"),\n            (center_lat - 0.003, center_lng + 0.007, \"789 Close St\", \"$495,000\", \"Sold 04/22/24\"),\n            (center_lat + 0.008, center_lng - 0.002, \"321 Similar Rd\", \"$462,000\", \"Sold 06/01/24\"),\n        ]\n        \n        for lat, lng, address, price, date in comparables:\n            folium.Marker(\n                [lat, lng],\n                popup=f\"<b>Comparable Sale</b><br>{address}<br>{price}<br>{date}\",\n                tooltip=f\"Comparable: {price}\",\n                icon=folium.Icon(color='green', icon='dollar-sign', prefix='fa')\n            ).add_to(m)\n    \n    def add_amenity_markers(self, m, center_lat: float, center_lng: float):\n        \"\"\"Add local amenity markers.\"\"\"\n        amenities = [\n            (center_lat + 0.004, center_lng + 0.006, \"Shopping Center\", \"shopping-cart\"),\n            (center_lat - 0.006, center_lng - 0.004, \"Community Park\", \"tree\"),\n            (center_lat + 0.002, center_lng - 0.008, \"Medical Center\", \"hospital\"),\n        ]\n        \n        for lat, lng, name, icon in amenities:\n            folium.Marker(\n                [lat, lng],\n                popup=f\"<b>{name}</b>\",\n                tooltip=name,\n                icon=folium.Icon(color='purple', icon=icon, prefix='fa')\n            ).add_to(m)\n    \n    def add_school_markers(self, m, center_lat: float, center_lng: float):\n        \"\"\"Add school markers.\"\"\"\n        schools = [\n            (center_lat + 0.007, center_lng + 0.001, \"Elementary School\", \"A\"),\n            (center_lat - 0.002, center_lng + 0.009, \"Middle School\", \"B+\"),\n            (center_lat + 0.001, center_lng - 0.006, \"High School\", \"A-\"),\n        ]\n        \n        for lat, lng, name, rating in schools:\n            folium.Marker(\n                [lat, lng],\n                popup=f\"<b>{name}</b><br>Rating: {rating}\",\n                tooltip=f\"{name} ({rating})\",\n                icon=folium.Icon(color='orange', icon='graduation-cap', prefix='fa')\n            ).add_to(m)\n    \n    def save_and_display_map(self, folium_map):\n        \"\"\"Save folium map to HTML and display in web view.\"\"\"\n        try:\n            # Create temporary HTML file\n            if self.map_file:\n                try:\n                    os.unlink(self.map_file)\n                except:\n                    pass\n            \n            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:\n                folium_map.save(f.name)\n                self.map_file = f.name\n            \n            # Load in web view\n            self.web_view.load(QUrl.fromLocalFile(self.map_file))\n            \n        except Exception as e:\n            self.status_label.setText(f\"Error displaying map: {str(e)}\")\n    \n    def refresh_map(self):\n        \"\"\"Refresh the map with current settings.\"\"\"\n        if self.subject_location:\n            self.create_property_map()\n        else:\n            self.create_default_map()\n    \n    def open_fullscreen_map(self):\n        \"\"\"Open the map in the default browser for fullscreen viewing.\"\"\"\n        if self.map_file and os.path.exists(self.map_file):\n            try:\n                webbrowser.open(f\"file://{self.map_file}\")\n            except Exception as e:\n                QMessageBox.warning(self, \"Error\", f\"Failed to open map in browser: {str(e)}\")\n        else:\n            QMessageBox.warning(self, \"No Map\", \"No map available to display.\")\n    \n    def export_map(self):\n        \"\"\"Export the current map to a file.\"\"\"\n        if not self.map_file or not os.path.exists(self.map_file):\n            QMessageBox.warning(self, \"No Map\", \"No map available to export.\")\n            return\n        \n        from PySide6.QtWidgets import QFileDialog\n        \n        file_path, _ = QFileDialog.getSaveFileName(\n            self, \"Save Map\", \"property_map.html\", \"HTML Files (*.html);;All Files (*)\"\n        )\n        \n        if file_path:\n            try:\n                import shutil\n                shutil.copy2(self.map_file, file_path)\n                QMessageBox.information(\n                    self, \"Success\", \n                    f\"Map exported successfully to:\\n{file_path}\"\n                )\n            except Exception as e:\n                QMessageBox.warning(self, \"Error\", f\"Failed to export map: {str(e)}\")\n    \n    def set_property_address(self, address: str):\n        \"\"\"Set the property address from external source.\"\"\"\n        self.address_input.setText(address)\n        if address.strip():\n            self.geocode_address()\n    \n    def get_map_data_for_report(self) -> Dict:\n        \"\"\"Get map data for inclusion in CMA reports.\"\"\"\n        return {\n            'subject_location': self.subject_location,\n            'comparable_locations': self.comparable_locations,\n            'map_file': self.map_file if self.map_file and os.path.exists(self.map_file) else None\n        }\n    \n    def cleanup(self):\n        \"\"\"Clean up temporary files.\"\"\"\n        if self.map_file and os.path.exists(self.map_file):\n            try:\n                os.unlink(self.map_file)\n            except:\n                pass\n    \n    def __del__(self):\n        \"\"\"Destructor to clean up temporary files.\"\"\"\n        self.cleanup()"