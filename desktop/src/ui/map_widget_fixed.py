"""
Interactive map widget for property location visualization in CMA reports.
Fixed version that properly handles Leaflet.js loading in QWebEngineView.
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
from PySide6.QtWebEngineCore import QWebEngineSettings


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
        
        # Create a persistent temporary file for the map
        self._temp_map_file_obj = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        self.map_file = self._temp_map_file_obj.name
        self._temp_map_file_obj.close()

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
        
        # Configure web view settings to allow external content
        settings = self.web_view.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        # Add console message handler for debugging
        self.web_view.page().javaScriptConsoleMessage = self.handle_console_message
        
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
        
        # Load initial default map with a delay to ensure widget is ready
        QTimer.singleShot(100, self.create_default_map)
    
    def handle_console_message(self, level, message, line, source):
        """Handle JavaScript console messages for debugging."""
        level_names = {0: "Info", 1: "Warning", 2: "Error"}
        level_name = level_names.get(level, "Unknown")
        
        # Log to console for debugging
        print(f"Map Widget JS {level_name} (line {line}): {message}")
        
        # Update status label for critical errors
        if level == 2 and "L is not defined" in message:
            self.status_label.setText("Map loading issue detected. Retrying...")
            # Retry loading after a delay
            QTimer.singleShot(1000, self.refresh_map)
    
    def setup_signals(self):
        """Connect signals and slots."""
        self.btn_geocode.clicked.connect(self.geocode_address)
        self.btn_refresh_map.clicked.connect(self.refresh_map)
        self.btn_fullscreen.clicked.connect(self.open_fullscreen_map)
        self.btn_export_map.clicked.connect(self.export_map)
        
        # Map option checkboxes
        self.show_subject_check.toggled.connect(self.refresh_map)
        self.show_comparables_check.toggled.connect(self.refresh_map)
        self.show_amenities_check.toggled.connect(self.refresh_map)
        self.show_schools_check.toggled.connect(self.refresh_map)
        
        # Enter key in address input
        self.address_input.returnPressed.connect(self.geocode_address)
    
    def create_default_map(self):
        """Create a default map centered on a major city."""
        try:
            # Create folium map centered on San Francisco
            m = folium.Map(
                location=[37.7749, -122.4194],
                zoom_start=12,
                tiles='OpenStreetMap'
            )
            
            # Add a sample marker
            folium.Marker(
                [37.7749, -122.4194],
                popup="Sample Location",
                tooltip="Click for property details",
                icon=folium.Icon(color='blue', icon='home', prefix='fa')
            ).add_to(m)
            
            # Save and display map
            self.save_and_display_map(m)
            self.status_label.setText("Default map loaded - Enter address to customize")
            
        except Exception as e:
            self.status_label.setText(f"Error creating default map: {str(e)}")
    
    def geocode_address(self):
        """Geocode the entered address and update map."""
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Input Required", "Please enter an address to locate.")
            return
        
        self.status_label.setText("Locating address...")
        self.btn_geocode.setEnabled(False)
        
        # Start geocoding thread
        self.geocode_thread = GeocodeThread(address)
        self.geocode_thread.location_found.connect(self.on_location_found)
        self.geocode_thread.geocoding_failed.connect(self.on_geocoding_failed)
        self.geocode_thread.start()
    
    def on_location_found(self, lat: float, lng: float, formatted_address: str):
        """Handle successful geocoding result."""
        self.subject_location = (lat, lng, formatted_address)
        self.create_property_map()
        self.status_label.setText(f"Property located: {formatted_address}")
        self.btn_geocode.setEnabled(True)
    
    def on_geocoding_failed(self, error_message: str):
        """Handle geocoding failure."""
        self.status_label.setText(f"Geocoding failed: {error_message}")
        self.btn_geocode.setEnabled(True)
        QMessageBox.warning(self, "Geocoding Error", error_message)
    
    def create_property_map(self):
        """Create a detailed property map with subject and comparables."""
        if not self.subject_location:
            return
        
        try:
            lat, lng, address = self.subject_location
            
            # Create map centered on subject property
            m = folium.Map(
                location=[lat, lng],
                zoom_start=14,
                tiles='OpenStreetMap'
            )
            
            # Add subject property marker
            if self.show_subject_check.isChecked():
                folium.Marker(
                    [lat, lng],
                    popup=f"<b>Subject Property</b><br>{address}",
                    tooltip="Subject Property",
                    icon=folium.Icon(color='red', icon='home', prefix='fa')
                ).add_to(m)
            
            # Add comparable properties
            if self.show_comparables_check.isChecked():
                self.add_comparable_markers(m, lat, lng)
            
            # Add local amenities
            if self.show_amenities_check.isChecked():
                self.add_amenity_markers(m, lat, lng)
            
            # Add schools
            if self.show_schools_check.isChecked():
                self.add_school_markers(m, lat, lng)
            
            # Add search radius circle
            folium.Circle(
                location=[lat, lng],
                radius=1609,  # 1 mile in meters
                popup="1 mile search radius",
                color="blue",
                fill=True,
                fillOpacity=0.1
            ).add_to(m)
            
            # Save and display updated map
            self.save_and_display_map(m)
            
        except Exception as e:
            self.status_label.setText(f"Error creating property map: {str(e)}")
    
    def add_comparable_markers(self, m, center_lat: float, center_lng: float):
        """Add comparable property markers around the subject property."""
        # Sample comparable properties (in production, these would come from MLS data)
        comparables = [
            (center_lat + 0.005, center_lng + 0.003, "456 Nearby Ave", "$475,000", "Sold 05/15/24"),
            (center_lat - 0.003, center_lng + 0.007, "789 Close St", "$495,000", "Sold 04/22/24"),
            (center_lat + 0.008, center_lng - 0.002, "321 Similar Rd", "$462,000", "Sold 06/01/24"),
        ]
        
        for lat, lng, address, price, date in comparables:
            folium.Marker(
                [lat, lng],
                popup=f"<b>Comparable Sale</b><br>{address}<br>{price}<br>{date}",
                tooltip=f"Comparable: {price}",
                icon=folium.Icon(color='green', icon='dollar-sign', prefix='fa')
            ).add_to(m)
    
    def add_amenity_markers(self, m, center_lat: float, center_lng: float):
        """Add local amenity markers."""
        amenities = [
            (center_lat + 0.004, center_lng + 0.006, "Shopping Center", "shopping-cart"),
            (center_lat - 0.006, center_lng - 0.004, "Community Park", "tree"),
            (center_lat + 0.002, center_lng - 0.008, "Medical Center", "hospital"),
        ]
        
        for lat, lng, name, icon in amenities:
            folium.Marker(
                [lat, lng],
                popup=f"<b>{name}</b>",
                tooltip=name,
                icon=folium.Icon(color='purple', icon=icon, prefix='fa')
            ).add_to(m)
    
    def add_school_markers(self, m, center_lat: float, center_lng: float):
        """Add school markers."""
        schools = [
            (center_lat + 0.007, center_lng + 0.001, "Elementary School", "A"),
            (center_lat - 0.002, center_lng + 0.009, "Middle School", "B+"),
            (center_lat + 0.001, center_lng - 0.006, "High School", "A-"),
        ]
        
        for lat, lng, name, rating in schools:
            folium.Marker(
                [lat, lng],
                popup=f"<b>{name}</b><br>Rating: {rating}",
                tooltip=f"{name} ({rating})",
                icon=folium.Icon(color='orange', icon='graduation-cap', prefix='fa')
            ).add_to(m)
    
    def save_and_display_map(self, folium_map):
        """Save folium map to HTML and display in web view."""
        try:
            # Get the HTML representation
            html = folium_map.get_root().render()
            
            # Add a wrapper to ensure Leaflet loads properly
            wrapped_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {html.split('<head>')[1].split('</head>')[0]}
    <script>
        // Wait for Leaflet to load before executing map code
        function initializeMap() {{
            if (typeof L === 'undefined') {{
                console.log('Leaflet not loaded yet, retrying...');
                setTimeout(initializeMap, 100);
                return;
            }}
            console.log('Leaflet loaded, initializing map...');
            {html.split('<script>')[1].split('</script>')[0]}
        }}
        
        // Start initialization when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                setTimeout(initializeMap, 100);
            }});
        }} else {{
            setTimeout(initializeMap, 100);
        }}
    </script>
</head>
<body>
    {html.split('<body>')[1].split('</body>')[0]}
</body>
</html>
"""
            
            # Save the wrapped HTML
            with open(self.map_file, 'w') as f:
                f.write(wrapped_html)
            
            # Load in web view
            self.web_view.load(QUrl.fromLocalFile(self.map_file))
            
        except Exception as e:
            self.status_label.setText(f"Error displaying map: {str(e)}")
    
    def refresh_map(self):
        """Refresh the map with current settings."""
        if self.subject_location:
            self.create_property_map()
        else:
            self.create_default_map()
    
    def open_fullscreen_map(self):
        """Open the map in the default browser for fullscreen viewing."""
        if self.map_file and os.path.exists(self.map_file):
            try:
                webbrowser.open(f"file://{self.map_file}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open map in browser: {str(e)}")
        else:
            QMessageBox.warning(self, "No Map", "No map available to display.")
    
    def export_map(self):
        """Export the current map to a file."""
        if not self.map_file or not os.path.exists(self.map_file):
            QMessageBox.warning(self, "No Map", "No map available to export.")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Map", "property_map.html", "HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.map_file, file_path)
                QMessageBox.information(
                    self, "Success", 
                    f"Map exported successfully to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export map: {str(e)}")
    
    def set_property_address(self, address: str):
        """Set the property address from external source."""
        self.address_input.setText(address)
        if address.strip():
            self.geocode_address()
    
    def get_map_data_for_report(self) -> Dict:
        """Get map data for inclusion in CMA reports."""
        return {
            'subject_location': self.subject_location,
            'comparable_locations': self.comparable_locations,
            'map_file': self.map_file if self.map_file and os.path.exists(self.map_file) else None
        }
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.map_file and os.path.exists(self.map_file):
            try:
                os.unlink(self.map_file)
            except Exception as e:
                print(f"Error cleaning up map file: {e}")
    
    def __del__(self):
        """Destructor to clean up temporary files."""
        self.cleanup()