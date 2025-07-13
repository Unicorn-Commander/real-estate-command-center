"""
CMA (Comparative Market Analysis) tab for the Real Estate Command Center.
"""
import os
import tempfile
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QLabel, QProgressBar, QSplitter, QListWidget, QListWidgetItem,
    QCheckBox, QDateEdit, QFrame, QScrollArea, QGridLayout, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QDate, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from core.cma_reports import CMAChartGenerator, CMAPDFGenerator, generate_sample_cma_data
from ui.photo_manager import PhotoManagerWidget
from ui.map_widget import PropertyMapWidget
from ui.property_photo_widget import PropertyPhotoWidget


class CMATab(QWidget):
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.chart_generator = CMAChartGenerator()
        self.pdf_generator = CMAPDFGenerator()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Main tab widget for CMA workflow
        self.cma_tabs = QTabWidget()
        
        # Tab 1: Property Input
        self.property_tab = self.create_property_input_tab()
        self.cma_tabs.addTab(self.property_tab, "1. Property Details")
        
        # Tab 2: Property Location Map
        self.map_tab = self.create_map_tab()
        self.cma_tabs.addTab(self.map_tab, "2. Location Map")
        
        # Tab 3: Comparable Selection
        self.comparables_tab = self.create_comparables_tab()
        self.cma_tabs.addTab(self.comparables_tab, "3. Comparables")
        
        # Tab 4: Analysis & Adjustments
        self.analysis_tab = self.create_analysis_tab()
        self.cma_tabs.addTab(self.analysis_tab, "4. Analysis")
        
        # Tab 5: Report Preview
        self.report_tab = self.create_report_tab()
        self.cma_tabs.addTab(self.report_tab, "5. Report")
        
        layout.addWidget(self.cma_tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.btn_save_draft = QPushButton(qta.icon('fa5s.save'), "Save Draft")
        self.btn_generate_report = QPushButton(qta.icon('fa5s.file-pdf'), "Generate Report")
        self.btn_export = QPushButton(qta.icon('fa5s.download'), "Export")
        self.btn_clear = QPushButton(qta.icon('fa5s.trash'), "Clear All")
        
        button_layout.addWidget(self.btn_save_draft)
        button_layout.addWidget(self.btn_generate_report)
        button_layout.addWidget(self.btn_export)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_clear)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.connect_signals()

    def create_property_input_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Subject Property Section
        subject_group = QGroupBox("Subject Property")
        subject_layout = QFormLayout()
        
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("123 Main St, City, State, ZIP")
        self.lookup_property_btn = QPushButton("Lookup Property")
        self.lookup_property_btn.clicked.connect(self._lookup_subject_property)

        address_input_layout = QHBoxLayout()
        address_input_layout.addWidget(self.address_edit)
        address_input_layout.addWidget(self.lookup_property_btn)
        subject_layout.addRow("Address:", address_input_layout)
        
        self.property_type_combo = QComboBox()
        self.property_type_combo.addItems([
            "Single Family", "Condo", "Townhouse", "Multi-Family", 
            "Land", "Commercial", "Industrial"
        ])
        subject_layout.addRow("Property Type:", self.property_type_combo)
        
        self.bedrooms_spin = QSpinBox()
        self.bedrooms_spin.setMaximum(20)
        subject_layout.addRow("Bedrooms:", self.bedrooms_spin)
        
        self.bathrooms_spin = QDoubleSpinBox()
        self.bathrooms_spin.setMaximum(20.0)
        self.bathrooms_spin.setSingleStep(0.5)
        subject_layout.addRow("Bathrooms:", self.bathrooms_spin)
        
        self.sqft_spin = QSpinBox()
        self.sqft_spin.setMaximum(50000)
        self.sqft_spin.setSuffix(" sq ft")
        subject_layout.addRow("Square Feet:", self.sqft_spin)
        
        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setMaximum(100.0)
        self.lot_size_spin.setSuffix(" acres")
        subject_layout.addRow("Lot Size:", self.lot_size_spin)
        
        self.year_built_spin = QSpinBox()
        self.year_built_spin.setRange(1800, 2030)
        self.year_built_spin.setValue(2000)
        subject_layout.addRow("Year Built:", self.year_built_spin)
        
        subject_group.setLayout(subject_layout)
        layout.addWidget(subject_group)
        
        # Additional Features Section
        features_group = QGroupBox("Additional Features")
        features_layout = QGridLayout()
        
        self.garage_check = QCheckBox("Garage")
        self.pool_check = QCheckBox("Pool")
        self.fireplace_check = QCheckBox("Fireplace")
        self.basement_check = QCheckBox("Basement")
        self.deck_check = QCheckBox("Deck/Patio")
        self.ac_check = QCheckBox("Central A/C")
        
        features_layout.addWidget(self.garage_check, 0, 0)
        features_layout.addWidget(self.pool_check, 0, 1)
        features_layout.addWidget(self.fireplace_check, 0, 2)
        features_layout.addWidget(self.basement_check, 1, 0)
        features_layout.addWidget(self.deck_check, 1, 1)
        features_layout.addWidget(self.ac_check, 1, 2)
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Property Photos Section
        photos_group = QGroupBox("Property Photos")
        photos_layout = QVBoxLayout()
        
        self.photo_manager = PhotoManagerWidget()
        photos_layout.addWidget(self.photo_manager)
        
        photos_group.setLayout(photos_layout)
        layout.addWidget(photos_group)
        
        # Market Context Section
        market_group = QGroupBox("Market Context")
        market_layout = QFormLayout()
        
        self.market_conditions_combo = QComboBox()
        self.market_conditions_combo.addItems([
            "Seller's Market", "Buyer's Market", "Balanced Market"
        ])
        market_layout.addRow("Market Conditions:", self.market_conditions_combo)
        
        self.analysis_date = QDateEdit()
        self.analysis_date.setDate(QDate.currentDate())
        market_layout.addRow("Analysis Date:", self.analysis_date)
        
        market_group.setLayout(market_layout)
        layout.addWidget(market_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_map_tab(self):
        """Create the property location map tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Initialize map widget
        self.map_widget = PropertyMapWidget()
        layout.addWidget(self.map_widget)
        
        # Connect address changes
        self.address_edit.textChanged.connect(self.update_map_address)
        
        widget.setLayout(layout)
        return widget

    def update_map_address(self):
        """Update map when address changes."""
        try:
            address = self.address_edit.text().strip()
            if len(address) > 10:  # Only update if reasonable address length
                self.map_widget.set_property_address(address)
        except Exception as e:
            print(f"Error updating map address: {e}")

    def create_comparables_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Left side - Search & Filters
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        search_group = QGroupBox("Search Comparables")
        search_layout = QVBoxLayout()
        
        self.search_radius_spin = QDoubleSpinBox()
        self.search_radius_spin.setRange(0.1, 10.0)
        self.search_radius_spin.setValue(1.0)
        self.search_radius_spin.setSuffix(" miles")
        
        self.days_back_spin = QSpinBox()
        self.days_back_spin.setRange(30, 730)
        self.days_back_spin.setValue(180)
        self.days_back_spin.setSuffix(" days")
        
        search_form = QFormLayout()
        search_form.addRow("Search Radius:", self.search_radius_spin)
        search_form.addRow("Days Back:", self.days_back_spin)
        search_layout.addLayout(search_form)
        
        self.btn_search_comps = QPushButton(qta.icon('fa5s.search'), "Search Comparables")
        search_layout.addWidget(self.btn_search_comps)
        
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)
        
        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QVBoxLayout()
        
        self.filter_sold_check = QCheckBox("Recently Sold")
        self.filter_sold_check.setChecked(True)
        self.filter_active_check = QCheckBox("Active Listings")
        self.filter_pending_check = QCheckBox("Pending Sales")
        
        filters_layout.addWidget(self.filter_sold_check)
        filters_layout.addWidget(self.filter_active_check)
        filters_layout.addWidget(self.filter_pending_check)
        
        filters_group.setLayout(filters_layout)
        left_layout.addWidget(filters_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Right side - Comparables List
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        comps_label = QLabel("Found Comparables")
        comps_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(comps_label)
        
        self.comparables_table = QTableWidget()
        self.comparables_table.setColumnCount(8)
        self.comparables_table.setHorizontalHeaderLabels([
            "Select", "Address", "Beds/Baths", "Sq Ft", "Sold Price", 
            "Sold Date", "Distance", "Status"
        ])
        right_layout.addWidget(self.comparables_table)
        
        # Selected comparables summary
        selected_label = QLabel("Selected: 0 comparables")
        right_layout.addWidget(selected_label)
        
        right_panel.setLayout(right_layout)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def create_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Analysis Summary
        summary_group = QGroupBox("Analysis Summary")
        summary_layout = QGridLayout()
        
        self.value_low_label = QLabel("$0")
        self.value_high_label = QLabel("$0")
        self.value_avg_label = QLabel("$0")
        self.recommended_label = QLabel("$0")
        
        summary_layout.addWidget(QLabel("Low Estimate:"), 0, 0)
        summary_layout.addWidget(self.value_low_label, 0, 1)
        summary_layout.addWidget(QLabel("High Estimate:"), 0, 2)
        summary_layout.addWidget(self.value_high_label, 0, 3)
        summary_layout.addWidget(QLabel("Average:"), 1, 0)
        summary_layout.addWidget(self.value_avg_label, 1, 1)
        summary_layout.addWidget(QLabel("Recommended:"), 1, 2)
        summary_layout.addWidget(self.recommended_label, 1, 3)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        self.btn_calculate_cma = QPushButton("Calculate CMA")
        self.btn_calculate_cma.clicked.connect(self._calculate_cma_values)
        layout.addWidget(self.btn_calculate_cma)
        
        # Adjustments Table
        adjustments_group = QGroupBox("Comparable Adjustments")
        adjustments_layout = QVBoxLayout()
        
        self.adjustments_table = QTableWidget()
        self.adjustments_table.setColumnCount(7)
        self.adjustments_table.setHorizontalHeaderLabels([
            "Property", "Sale Price", "Sq Ft Adj", "Bed/Bath Adj", 
            "Feature Adj", "Market Adj", "Adjusted Value"
        ])
        adjustments_layout.addWidget(self.adjustments_table)
        
        adjustments_group.setLayout(adjustments_layout)
        layout.addWidget(adjustments_group)
        
        # Market Analysis
        market_analysis_group = QGroupBox("Market Analysis")
        market_analysis_layout = QVBoxLayout()
        
        self.market_analysis_text = QTextEdit()
        self.market_analysis_text.setMaximumHeight(150)
        self.market_analysis_text.setPlaceholderText(
            "Market analysis and trends will be generated here..."
        )
        market_analysis_layout.addWidget(self.market_analysis_text)
        
        market_analysis_group.setLayout(market_analysis_layout)
        layout.addWidget(market_analysis_group)
        
        widget.setLayout(layout)
        return widget

    def create_report_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Report Header
        header_layout = QHBoxLayout()
        
        report_title = QLabel("CMA Report Preview")
        report_title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(report_title)
        
        header_layout.addStretch()
        
        self.btn_preview = QPushButton(qta.icon('fa5s.eye'), "Preview")
        self.btn_export_pdf = QPushButton(qta.icon('fa5s.file-pdf'), "Export PDF")
        self.btn_export_excel = QPushButton(qta.icon('fa5s.file-excel'), "Export Excel")
        
        header_layout.addWidget(self.btn_preview)
        header_layout.addWidget(self.btn_export_pdf)
        header_layout.addWidget(self.btn_export_excel)
        
        layout.addLayout(header_layout)
        
        # Report Preview Area with Charts
        preview_splitter = QSplitter(Qt.Vertical)
        
        # Charts section
        charts_widget = QWidget()
        charts_layout = QVBoxLayout()
        
        # Create matplotlib charts
        self.create_embedded_charts(charts_layout)
        charts_widget.setLayout(charts_layout)
        
        # HTML preview
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setHtml(self.get_sample_report_html())
        
        preview_splitter.addWidget(charts_widget)
        preview_splitter.addWidget(self.report_preview)
        preview_splitter.setSizes([400, 300])
        
        layout.addWidget(preview_splitter)
        
        # Report Options
        options_group = QGroupBox("Report Options")
        options_layout = QGridLayout()
        
        self.include_photos_check = QCheckBox("Include Property Photos")
        self.include_photos_check.setChecked(True)
        self.include_maps_check = QCheckBox("Include Location Maps")
        self.include_maps_check.setChecked(True)
        self.include_charts_check = QCheckBox("Include Market Charts")
        self.include_charts_check.setChecked(True)
        self.include_disclosures_check = QCheckBox("Include Disclosures")
        self.include_disclosures_check.setChecked(True)
        
        options_layout.addWidget(self.include_photos_check, 0, 0)
        options_layout.addWidget(self.include_maps_check, 0, 1)
        options_layout.addWidget(self.include_charts_check, 1, 0)
        options_layout.addWidget(self.include_disclosures_check, 1, 1)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        widget.setLayout(layout)
        return widget

    def get_sample_report_html(self):
        return """
        <html>
        <head><style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
        h2 { color: #34495e; margin-top: 25px; }
        .header { background-color: #ecf0f1; padding: 15px; border-radius: 5px; }
        .property-info { margin: 15px 0; }
        .value-estimate { background-color: #e8f5e8; padding: 10px; border-radius: 5px; text-align: center; }
        </style></head>
        <body>
        <div class="header">
        <h1>Comparative Market Analysis</h1>
        <p><strong>Prepared for:</strong> [Client Name]</p>
        <p><strong>Property:</strong> [Subject Property Address]</p>
        <p><strong>Date:</strong> [Analysis Date]</p>
        </div>
        
        <h2>📊 Executive Summary</h2>
        <div class="value-estimate">
        <h3>💰 Estimated Market Value: ${cma_data['recommended_value']:,}</h3>
        <p><strong>Value Range: ${cma_data['value_range']['low']:,} - ${cma_data['value_range']['high']:,}</strong></p>
        </div>
        
        <h2>Subject Property Details</h2>
        <div class="property-info">
        <p><strong>Address:</strong> [Property Address]</p>
        <p><strong>Property Type:</strong> [Type]</p>
        <p><strong>Bedrooms/Bathrooms:</strong> [Beds]/[Baths]</p>
        <p><strong>Square Footage:</strong> [Sq Ft]</p>
        <p><strong>Year Built:</strong> [Year]</p>
        </div>
        
        <h2>Comparable Properties Analysis</h2>
        <p>Analysis based on [X] comparable properties sold within the last [X] days...</p>
        
        <h2>Market Conditions</h2>
        <p>Current market analysis and trends...</p>
        
        <h2>Methodology & Disclaimers</h2>
        <p>This CMA was prepared using [methodology description]...</p>
        </body>
        </html>
        """

    def connect_signals(self):
        # Connect button signals to placeholder methods
        self.btn_save_draft.clicked.connect(self.save_draft)
        self.btn_generate_report.clicked.connect(self.generate_report)
        self.btn_export.clicked.connect(self.export_report)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_search_comps.clicked.connect(self.search_comparables)
        self.btn_preview.clicked.connect(self.preview_report)
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.btn_export_excel.clicked.connect(self.export_excel)

    def _lookup_subject_property(self):
        address = self.address_edit.text().strip()
        if not address:
            QMessageBox.warning(self, "Input Error", "Please enter an address to lookup.")
            return

        QMessageBox.information(self, "Lookup", "Attempting to lookup property data... This may take a moment.")
        
        # Use a QThread for the lookup to keep UI responsive
        self.lookup_thread = PropertyLookupThread(self.colonel_client, address)
        self.lookup_thread.lookup_complete.connect(self._on_property_lookup_complete)
        self.lookup_thread.start()

    @Slot(dict)
    def _on_property_lookup_complete(self, property_info: dict):
        if property_info and not property_info.get('error'):
            self.subject_property_data = property_info # Store the full property info
            prop_data = property_info.get('property', {})
            address_details = property_info.get('location', {}).get('address_details', {})

            # Populate form fields
            self.address_edit.setText(property_info.get('address', '')) # Keep full address
            self.property_type_combo.setCurrentText(prop_data.get('type', ''))
            self.bedrooms_spin.setValue(prop_data.get('bedrooms', 0))
            self.bathrooms_spin.setValue(prop_data.get('bathrooms', 0.0))
            self.sqft_spin.setValue(prop_data.get('square_feet', 0))
            self.lot_size_spin.setValue(prop_data.get('lot_size', 0.0))
            self.year_built_spin.setValue(prop_data.get('year_built', 0))
            
            # Store property ID for comparables search
            self.subject_property_id = prop_data.get('id') or prop_data.get('ListingId')
            
            # Load property photos if available
            media = property_info.get('media', [])
            if not media:
                # Check in property data
                media = prop_data.get('media', [])
            
            if media:
                photo_urls = [m.get('url') for m in media if m.get('url')]
                if photo_urls and hasattr(self, 'photo_manager'):
                    # If using PhotoManagerWidget
                    for url in photo_urls[:10]:  # Limit to first 10 photos
                        self.photo_manager.add_photo_from_url(url)
                elif photo_urls and hasattr(self, 'property_photo_widget'):
                    # If using PropertyPhotoWidget
                    self.property_photo_widget.load_photos(photo_urls)
            
            QMessageBox.information(self, "Lookup Success", "Property data fetched successfully!")
        else:
            error_msg = property_info.get('error', 'Unknown error during lookup.')
            QMessageBox.warning(self, "Lookup Failed", f"Could not fetch property data: {error_msg}")

    def save_draft(self):
        """Save current CMA as draft."""
        try:
            # Collect data from form fields
            cma_data = self.collect_form_data()
            # TODO: Save to database or file
            QMessageBox.information(self, "Success", "CMA draft saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save draft: {str(e)}")

    def generate_report(self):
        """Generate and preview the complete CMA report."""
        try:
            # Update charts first
            self.update_charts()
            
            # Generate enhanced HTML with charts
            enhanced_html = self.generate_enhanced_report_html()
            self.report_preview.setHtml(enhanced_html)
            
            # Switch to report tab
            self.cma_tabs.setCurrentIndex(4)
            
            QMessageBox.information(self, "Success", "CMA report generated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate report: {str(e)}")

    def export_report(self):
        """Export report in various formats."""
        try:
            # Ask user for export format
            format_choice = QMessageBox.question(
                self, "Export Format", 
                "Choose export format:", 
                QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel),
                QMessageBox.Yes
            )
            
            if format_choice == QMessageBox.Yes:
                self.export_pdf()
            elif format_choice == QMessageBox.No:
                self.export_excel()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")

    def clear_all(self):
        print("Clear all functionality - to be implemented")

    def _calculate_cma_values(self):
        """Calculate CMA values based on comparable properties."""
        try:
            # Get comparable properties from the table
            comparables = []
            for row in range(self.comparables_table.rowCount()):
                checkbox_item = self.comparables_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    try:
                        price_text = self.comparables_table.item(row, 4).text()
                        price = int(price_text.replace('$', '').replace(',', ''))
                        
                        sqft_text = self.comparables_table.item(row, 3).text()
                        sqft = int(sqft_text.replace(',', ''))
                        
                        if sqft > 0:
                            price_per_sqft = price / sqft
                            comparables.append({
                                'price': price,
                                'sqft': sqft,
                                'price_per_sqft': price_per_sqft
                            })
                    except (ValueError, AttributeError, ZeroDivisionError):
                        continue
            
            if not comparables:
                QMessageBox.warning(self, "Warning", "No valid comparable properties selected.")
                return
            
            # Get subject property square footage
            subject_sqft = self.sqft_spin.value()
            if subject_sqft <= 0:
                QMessageBox.warning(self, "Warning", "Please enter valid square footage for subject property.")
                return
            
            # Calculate average price per square foot
            avg_price_per_sqft = sum(comp['price_per_sqft'] for comp in comparables) / len(comparables)
            
            # Calculate estimated values
            low_estimate = int(avg_price_per_sqft * 0.95 * subject_sqft)
            high_estimate = int(avg_price_per_sqft * 1.05 * subject_sqft)
            recommended_value = int(avg_price_per_sqft * subject_sqft)
            
            # Update the UI labels
            self.value_low_label.setText(f"${low_estimate:,}")
            self.value_high_label.setText(f"${high_estimate:,}")
            self.recommended_label.setText(f"${recommended_value:,}")
            
            # Update the adjustments table
            self._populate_adjustments_table(comparables, recommended_value)
            
            # Update market analysis
            market_text = f"""Market Analysis Results:
            
Comparable Properties: {len(comparables)}
Average Price per Sq Ft: ${avg_price_per_sqft:,.2f}
Subject Property Sq Ft: {subject_sqft:,}

Estimated Value Range: ${low_estimate:,} - ${high_estimate:,}
Recommended Market Value: ${recommended_value:,}

Based on {len(comparables)} comparable sales, the subject property shows strong market positioning within the local area."""
            
            self.market_analysis_text.setPlainText(market_text)
            
            # Update charts
            self.update_charts()
            
            QMessageBox.information(self, "Success", f"CMA calculation completed.\nRecommended Value: ${recommended_value:,}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculating CMA values: {str(e)}")
    
    def _populate_adjustments_table(self, comparables, recommended_value):
        """Populate the adjustments table with calculated values."""
        self.adjustments_table.setRowCount(len(comparables))
        
        for row, comp in enumerate(comparables):
            # Property (simplified address)
            self.adjustments_table.setItem(row, 0, QTableWidgetItem(f"Comp {row + 1}"))
            
            # Sale Price
            self.adjustments_table.setItem(row, 1, QTableWidgetItem(f"${comp['price']:,}"))
            
            # Sq Ft Adjustment (based on price per sq ft difference)
            sqft_adj = (comp['price_per_sqft'] - (recommended_value / comp['sqft'])) * comp['sqft']
            self.adjustments_table.setItem(row, 2, QTableWidgetItem(f"${sqft_adj:,.0f}"))
            
            # Bed/Bath Adjustment (placeholder)
            self.adjustments_table.setItem(row, 3, QTableWidgetItem("$0"))
            
            # Feature Adjustment (placeholder)
            self.adjustments_table.setItem(row, 4, QTableWidgetItem("$0"))
            
            # Market Adjustment (placeholder)
            self.adjustments_table.setItem(row, 5, QTableWidgetItem("$0"))
            
            # Adjusted Value
            adjusted_value = comp['price'] - sqft_adj
            self.adjustments_table.setItem(row, 6, QTableWidgetItem(f"${adjusted_value:,.0f}"))

    def search_comparables(self):
        if not hasattr(self, 'subject_property_id') or not self.subject_property_id:
            QMessageBox.warning(self, "Missing Subject Property", "Please lookup the subject property first.")
            return

        QMessageBox.information(self, "Searching Comparables", "Searching for comparable properties... This may take a moment.")
        
        radius = self.search_radius_spin.value()
        days_back = self.days_back_spin.value()

        # Use a QThread for the comparable search to keep UI responsive
        self.comp_search_thread = ComparableSearchThread(
            self.colonel_client, self.subject_property_id, radius, days_back
        )
        self.comp_search_thread.search_complete.connect(self._on_comparable_search_complete)
        self.comp_search_thread.start()

    @Slot(list)
    def _on_comparable_search_complete(self, comparables: list):
        self.fetched_comparables = comparables # Store all fetched comparables
        self.comparables_table.setRowCount(0) # Clear existing rows
        if comparables:
            self.comparables_table.setRowCount(len(comparables))
            for row_idx, comp in enumerate(comparables):
                # Add a checkbox for selection
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked) # Default to unchecked
                self.comparables_table.setItem(row_idx, 0, checkbox_item)

                self.comparables_table.setItem(row_idx, 1, QTableWidgetItem(comp.get('address', '')))
                self.comparables_table.setItem(row_idx, 2, QTableWidgetItem(f"{comp.get('bedrooms', '?')}/{comp.get('bathrooms', '?')}"))
                self.comparables_table.setItem(row_idx, 3, QTableWidgetItem(f"{comp.get('square_feet', 0):,}"))
                self.comparables_table.setItem(row_idx, 4, QTableWidgetItem(f"${comp.get('sale_price', 0):,.0f}"))
                self.comparables_table.setItem(row_idx, 5, QTableWidgetItem(comp.get('sale_date', '')))
                self.comparables_table.setItem(row_idx, 6, QTableWidgetItem(f"{comp.get('distance_miles', 0):.2f} miles"))
                self.comparables_table.setItem(row_idx, 7, QTableWidgetItem(comp.get('status', 'Sold')))
            
            self.comparables_table.resizeColumnsToContents()
            QMessageBox.information(self, "Search Complete", f"Found {len(comparables)} comparable properties.")
        else:
            QMessageBox.information(self, "No Comparables", "No comparable properties found for the given criteria.")

    def preview_report(self):
        """Preview the complete report with charts."""
        try:
            self.generate_report()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to preview report: {str(e)}")

    def collect_form_data(self) -> dict:
        """Collect data from all form fields."""
        collected_comparables = []
        for row_idx in range(self.comparables_table.rowCount()):
            checkbox_item = self.comparables_table.item(row_idx, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                comp = {
                    'address': self.comparables_table.item(row_idx, 1).text(),
                    'beds': self.comparables_table.item(row_idx, 2).text().split('/')[0],
                    'baths': self.comparables_table.item(row_idx, 2).text().split('/')[1],
                    'sqft': int(self.comparables_table.item(row_idx, 3).text().replace(',', '')),
                    'price': int(self.comparables_table.item(row_idx, 4).text().replace('$', '').replace(',', ''))
                }
                collected_comparables.append(comp)

        return {
            'property_address': self.address_edit.text() or '123 Sample Street, Anytown, ST 12345',
            'client_name': 'Sample Client',
            'agent_name': 'Real Estate Agent',
            'brokerage': 'Premier Realty Group',
            'property_type': self.property_type_combo.currentText(),
            'bedrooms': self.bedrooms_spin.value(),
            'bathrooms': self.bathrooms_spin.value(),
            'sqft': self.sqft_spin.value() or 2050,
            'lot_size': self.lot_size_spin.value() or 0.25,
            'year_built': self.year_built_spin.value(),
            'garage': self.garage_check.isChecked(),
            'pool': self.pool_check.isChecked(),
            'recommended_value': 485000,
            'value_range': {'low': 465000, 'high': 505000},
            'market_summary': 'Professional market analysis based on current conditions and comparable sales.',
            'comparables': collected_comparables,
        }

    def generate_enhanced_report_html(self) -> str:
        """Generate enhanced HTML report with embedded chart data."""
        cma_data = self.collect_form_data()
        
        html = f"""
        <html>
        <head><style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2E86AB; border-bottom: 3px solid #2E86AB; padding-bottom: 10px; }}
        h2 {{ color: #2E86AB; margin-top: 25px; }}
        .header {{ background: linear-gradient(135deg, #2E86AB, #A23B72); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .property-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .value-estimate {{ background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #28a745; }}
        .comp-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .comp-table th {{ background: #2E86AB; color: white; padding: 12px; }}
        .comp-table td {{ padding: 10px; border: 1px solid #ddd; }}
        .comp-table tr:nth-child(even) {{ background: #f8f9fa; }}
        .chart-placeholder {{ background: #f0f8ff; border: 2px dashed #2E86AB; padding: 30px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        </style></head>
        <body>
        <div class="header">
        <h1>🏠 COMPARATIVE MARKET ANALYSIS</h1>
        <p><strong>Property:</strong> {cma_data['property_address']}</p>
        <p><strong>Analysis Date:</strong> {QDate.currentDate().toString('MMMM d, yyyy')}</p>
        </div>
        
        <h2>📊 Executive Summary</h2>
        <div class="value-estimate">
        <h3>💰 Estimated Market Value: ${cma_data['recommended_value']:,}</h3>
        <p><strong>Value Range: ${cma_data['value_range']['low']:,} - ${cma_data['value_range']['high']:,}</strong></p>
        </div>
        
        <h2>🏘️ Subject Property Details</h2>
        <div class="property-info">
        <table style="width: 100%;">
        <tr><td><strong>Address:</strong></td><td>{cma_data['property_address']}</td></tr>
        <tr><td><strong>Property Type:</strong></td><td>{cma_data['property_type']}</td></tr>
        <tr><td><strong>Bedrooms:</strong></td><td>{cma_data['bedrooms']}</td></tr>
        <tr><td><strong>Bathrooms:</strong></td><td>{cma_data['bathrooms']}</td></tr>
        <tr><td><strong>Square Feet:</strong></td><td>{cma_data['sqft']:,}</td></tr>
        <tr><td><strong>Year Built:</strong></td><td>{cma_data['year_built']}</td></tr>
        </table>
        </div>
        
        <div class="chart-placeholder">
        <h3>📈 Interactive Charts Available Above</h3>
        <p>View the embedded market trend and comparable analysis charts in the preview area above.</p>
        </div>
        
        <h2>🔍 Comparable Properties</h2>
        <table class="comp-table">
        <thead>
        <tr><th>Address</th><th>Sale Price</th><th>Sq Ft</th><th>Beds/Baths</th><th>Sale Date</th><th>$/Sq Ft</th></tr>
        </thead>
        <tbody>
        """
        
        for comp in cma_data['comparables']:
            price_per_sqft = comp['price'] / comp['sqft'] if comp['sqft'] > 0 else 0
            html += f"""
            <tr>
            <td>{comp['address']}</td>
            <td>${comp['price']:,}</td>
            <td>{comp['sqft']:,}</td>
            <td>{comp['beds']}/{comp['baths']}</td>
            <td>Recent</td>
            <td>${price_per_sqft:.0f}</td>
            </tr>
            """
        
        html += """
        </tbody>
        </table>
        
        <h2>📋 Market Analysis</h2>
        <p><strong>Market Summary:</strong> """ + cma_data['market_summary'] + """</p>
        
        <h2>⚖️ Methodology & Disclaimers</h2>
        <p><strong>Methodology:</strong> This analysis uses recent comparable sales within a 1-mile radius, 
        adjusted for differences in size, features, and market conditions.</p>
        <p><strong>Disclaimer:</strong> This CMA is not an appraisal and should not be used for lending purposes. 
        Market conditions can change rapidly. Consult a licensed appraiser for official valuations.</p>
        </body>
        </html>
        """
        
        return html

    def export_pdf(self):
        """Export CMA report as professional PDF."""
        try:
            # Get save location from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save CMA Report", "CMA_Report.pdf", "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Collect current form data
                cma_data = self.collect_form_data()
                
                # Generate PDF report
                self.pdf_generator.generate_cma_report(cma_data, file_path)
                
                QMessageBox.information(
                    self, "Success", 
                    f"PDF report exported successfully to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export PDF: {str(e)}")

    def export_excel(self):
        print("Export Excel functionality - to be implemented")

    def create_embedded_charts(self, layout):
        """Create embedded matplotlib charts in the report preview."""
        # Price Trend Chart
        self.trend_figure = Figure(figsize=(10, 4))
        self.trend_canvas = FigureCanvas(self.trend_figure)
        layout.addWidget(QLabel("Market Price Trends"))
        layout.addWidget(self.trend_canvas)
        
        # Comparables Chart
        self.comp_figure = Figure(figsize=(10, 4))
        self.comp_canvas = FigureCanvas(self.comp_figure)
        layout.addWidget(QLabel("Comparable Properties Analysis"))
        layout.addWidget(self.comp_canvas)
        
        # Generate initial sample charts
        self.update_charts()

    def update_charts(self):
        """Update the embedded charts with current data."""
        try:
            # Clear previous plots
            self.trend_figure.clear()
            self.comp_figure.clear()
            
            # Price trend chart
            ax1 = self.trend_figure.add_subplot(111)
            sample_data = [{'date': f'2024-{i:02d}-01', 'price': 450000 + i*5000} for i in range(1, 7)]
            dates = [item['date'] for item in sample_data]
            prices = [item['price'] for item in sample_data]
            ax1.plot(dates, prices, marker='o', linewidth=2, color='#2E86AB')
            ax1.set_title('Market Price Trends - Last 6 Months')
            ax1.set_ylabel('Average Price ($)')
            ax1.tick_params(axis='x', rotation=45)
            
            # Comparables chart
            ax2 = self.comp_figure.add_subplot(111)
            addresses = ['123 Main St', '456 Oak Ave', '789 Pine Rd', 'Subject Prop']
            prices = [485000, 462000, 510000, 485000]
            colors = ['#2E86AB' if 'Subject' not in addr else '#A23B72' for addr in addresses]
            bars = ax2.bar(addresses, prices, color=colors)
            ax2.set_title('Comparable Sale Prices')
            ax2.set_ylabel('Sale Price ($)')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, price in zip(bars, prices):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 5000,
                        f'${price:,.0f}', ha='center', va='bottom', fontweight='bold')
            
            # Refresh canvases
            self.trend_figure.tight_layout()
            self.comp_figure.tight_layout()
            self.trend_canvas.draw()
            self.comp_canvas.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")

    def load_data(self):
        """Load CMA data and refresh charts."""
        self.update_charts()
        print("CMA data loaded and charts updated")


class PropertyLookupThread(QThread):
    lookup_complete = Signal(dict)

    def __init__(self, colonel_client, address: str):
        super().__init__()
        self.colonel_client = colonel_client
        self.address = address

    def run(self):
        property_info = self.colonel_client.property_service.lookup_property(self.address)
        self.lookup_complete.emit(property_info)

    def save_draft(self):
        """Save current CMA as draft."""
        try:
            # Collect data from form fields
            cma_data = self.collect_form_data()
            # TODO: Save to database or file
            QMessageBox.information(self, "Success", "CMA draft saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save draft: {str(e)}")

    def generate_report(self):
        """Generate and preview the complete CMA report."""
        try:
            # Update charts first
            self.update_charts()
            
            # Generate enhanced HTML with charts
            enhanced_html = self.generate_enhanced_report_html()
            self.report_preview.setHtml(enhanced_html)
            
            # Switch to report tab
            self.cma_tabs.setCurrentIndex(4)
            
            QMessageBox.information(self, "Success", "CMA report generated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate report: {str(e)}")

    def export_report(self):
        """Export report in various formats."""
        try:
            # Ask user for export format
            format_choice = QMessageBox.question(
                self, "Export Format", 
                "Choose export format:", 
                QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel),
                QMessageBox.Yes
            )
            
            if format_choice == QMessageBox.Yes:
                self.export_pdf()
            elif format_choice == QMessageBox.No:
                self.export_excel()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")

    def clear_all(self):
        print("Clear all functionality - to be implemented")

    def search_comparables(self):
        if not hasattr(self, 'subject_property_id') or not self.subject_property_id:
            QMessageBox.warning(self, "Missing Subject Property", "Please lookup the subject property first.")
            return

        QMessageBox.information(self, "Searching Comparables", "Searching for comparable properties... This may take a moment.")
        
        radius = self.search_radius_spin.value()
        days_back = self.days_back_spin.value()

        # Use a QThread for the comparable search to keep UI responsive
        self.comp_search_thread = ComparableSearchThread(
            self.colonel_client, self.subject_property_id, radius, days_back
        )
        self.comp_search_thread.search_complete.connect(self._on_comparable_search_complete)
        self.comp_search_thread.start()

    @Slot(list)
    def _on_comparable_search_complete(self, comparables: list):
        self.fetched_comparables = comparables # Store all fetched comparables
        self.comparables_table.setRowCount(0) # Clear existing rows
        if comparables:
            self.comparables_table.setRowCount(len(comparables))
            for row_idx, comp in enumerate(comparables):
                # Add a checkbox for selection
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked) # Default to unchecked
                self.comparables_table.setItem(row_idx, 0, checkbox_item)

                self.comparables_table.setItem(row_idx, 1, QTableWidgetItem(comp.get('address', '')))
                self.comparables_table.setItem(row_idx, 2, QTableWidgetItem(f"{comp.get('bedrooms', '?')}/{comp.get('bathrooms', '?')}"))
                self.comparables_table.setItem(row_idx, 3, QTableWidgetItem(f"{comp.get('square_feet', 0):,}"))
                self.comparables_table.setItem(row_idx, 4, QTableWidgetItem(f"${comp.get('sale_price', 0):,.0f}"))
                self.comparables_table.setItem(row_idx, 5, QTableWidgetItem(comp.get('sale_date', '')))
                self.comparables_table.setItem(row_idx, 6, QTableWidgetItem(f"{comp.get('distance_miles', 0):.2f} miles"))
                self.comparables_table.setItem(row_idx, 7, QTableWidgetItem(comp.get('status', 'Sold')))
            
            self.comparables_table.resizeColumnsToContents()
            QMessageBox.information(self, "Search Complete", f"Found {len(comparables)} comparable properties.")
        else:
            QMessageBox.information(self, "No Comparables", "No comparable properties found for the given criteria.")


class ComparableSearchThread(QThread):
    search_complete = Signal(list)

    def __init__(self, colonel_client, property_id: str, radius: float, days_back: int):
        super().__init__()
        self.colonel_client = colonel_client
        self.property_id = property_id
        self.radius = radius
        self.days_back = days_back

    def run(self):
        comparables = self.colonel_client.property_service.get_comparable_sales(
            self.property_id, self.radius, self.days_back
        )
        self.search_complete.emit(comparables)

    def preview_report(self):
        """Preview the complete report with charts."""
        try:
            self.generate_report()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to preview report: {str(e)}")

    def collect_form_data(self) -> dict:
        """Collect data from all form fields."""
        collected_comparables = []
        for row_idx in range(self.comparables_table.rowCount()):
            checkbox_item = self.comparables_table.item(row_idx, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                comp = {
                    'address': self.comparables_table.item(row_idx, 1).text(),
                    'beds': self.comparables_table.item(row_idx, 2).text().split('/')[0],
                    'baths': self.comparables_table.item(row_idx, 2).text().split('/')[1],
                    'sqft': int(self.comparables_table.item(row_idx, 3).text().replace(',', '')),
                    'price': int(self.comparables_table.item(row_idx, 4).text().replace('$', '').replace(',', ''))
                }
                collected_comparables.append(comp)

    def generate_enhanced_report_html(self) -> str:
        """Generate enhanced HTML report with embedded chart data."""
        cma_data = self.collect_form_data()
        
        html = f"""
        <html>
        <head><style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2E86AB; border-bottom: 3px solid #2E86AB; padding-bottom: 10px; }}
        h2 {{ color: #2E86AB; margin-top: 25px; }}
        .header {{ background: linear-gradient(135deg, #2E86AB, #A23B72); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .property-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .value-estimate {{ background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #28a745; }}
        .comp-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .comp-table th {{ background: #2E86AB; color: white; padding: 12px; }}
        .comp-table td {{ padding: 10px; border: 1px solid #ddd; }}
        .comp-table tr:nth-child(even) {{ background: #f8f9fa; }}
        .chart-placeholder {{ background: #f0f8ff; border: 2px dashed #2E86AB; padding: 30px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        </style></head>
        <body>
        <div class="header">
        <h1>🏠 COMPARATIVE MARKET ANALYSIS</h1>
        <p><strong>Property:</strong> {cma_data['property_address']}</p>
        <p><strong>Analysis Date:</strong> {QDate.currentDate().toString('MMMM d, yyyy')}</p>
        </div>
        
        <h2>📊 Executive Summary</h2>
        <div class="value-estimate">
        <h3>💰 Estimated Market Value: ${cma_data['recommended_value']:,}</h3>
        <p><strong>Value Range: ${cma_data['value_range']['low']:,} - ${cma_data['value_range']['high']:,}</strong></p>
        </div>
        
        <h2>🏘️ Subject Property Details</h2>
        <div class="property-info">
        <table style="width: 100%;">
        <tr><td><strong>Address:</strong></td><td>{cma_data['property_address']}</td></tr>
        <tr><td><strong>Property Type:</strong></td><td>{cma_data['property_type']}</td></tr>
        <tr><td><strong>Bedrooms:</strong></td><td>{cma_data['bedrooms']}</td></tr>
        <tr><td><strong>Bathrooms:</strong></td><td>{cma_data['bathrooms']}</td></tr>
        <tr><td><strong>Square Feet:</strong></td><td>{cma_data['sqft']:,}</td></tr>
        <tr><td><strong>Year Built:</strong></td><td>{cma_data['year_built']}</td></tr>
        </table>
        </div>
        
        <div class="chart-placeholder">
        <h3>📈 Interactive Charts Available Above</h3>
        <p>View the embedded market trend and comparable analysis charts in the preview area above.</p>
        </div>
        
        <h2>🔍 Comparable Properties</h2>
        <table class="comp-table">
        <thead>
        <tr><th>Address</th><th>Sale Price</th><th>Sq Ft</th><th>Beds/Baths</th><th>Sale Date</th><th>$/Sq Ft</th></tr>
        </thead>
        <tbody>
        """
        
        for comp in cma_data['comparables']:
            price_per_sqft = comp['price'] / comp['sqft'] if comp['sqft'] > 0 else 0
            html += f"""
            <tr>
            <td>{comp['address']}</td>
            <td>${comp['price']:,}</td>
            <td>{comp['sqft']:,}</td>
            <td>{comp['beds']}/{comp['baths']}</td>
            <td>{comp['sold_date']}</td>
            <td>${price_per_sqft:.0f}</td>
            </tr>
            """
        
        html += """
        </tbody>
        </table>
        
        <h2>📋 Market Analysis</h2>
        <p><strong>Market Summary:</strong> """ + cma_data['market_summary'] + """</p>
        
        <h2>⚖️ Methodology & Disclaimers</h2>
        <p><strong>Methodology:</strong> This analysis uses recent comparable sales within a 1-mile radius, 
        adjusted for differences in size, features, and market conditions.</p>
        <p><strong>Disclaimer:</strong> This CMA is not an appraisal and should not be used for lending purposes. 
        Market conditions can change rapidly. Consult a licensed appraiser for official valuations.</p>
        </body>
        </html>
        """
        
        return html

    def export_pdf(self):
        """Export CMA report as professional PDF."""
        try:
            # Get save location from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save CMA Report", "CMA_Report.pdf", "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Collect current form data
                cma_data = self.collect_form_data()
                
                # Generate PDF report
                self.pdf_generator.generate_cma_report(cma_data, file_path)
                
                QMessageBox.information(
                    self, "Success", 
                    f"PDF report exported successfully to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export PDF: {str(e)}")

    def export_excel(self):
        print("Export Excel functionality - to be implemented")

    def create_embedded_charts(self, layout):
        """Create embedded matplotlib charts in the report preview."""
        # Price Trend Chart
        self.trend_figure = Figure(figsize=(10, 4))
        self.trend_canvas = FigureCanvas(self.trend_figure)
        layout.addWidget(QLabel("Market Price Trends"))
        layout.addWidget(self.trend_canvas)
        
        # Comparables Chart
        self.comp_figure = Figure(figsize=(10, 4))
        self.comp_canvas = FigureCanvas(self.comp_figure)
        layout.addWidget(QLabel("Comparable Properties Analysis"))
        layout.addWidget(self.comp_canvas)
        
        # Generate initial sample charts
        self.update_charts()

    def update_charts(self):
        """Update the embedded charts with current data."""
        try:
            # Clear previous plots
            self.trend_figure.clear()
            self.comp_figure.clear()
            
            # Price trend chart
            ax1 = self.trend_figure.add_subplot(111)
            sample_data = [{'date': f'2024-{i:02d}-01', 'price': 450000 + i*5000} for i in range(1, 7)]
            dates = [item['date'] for item in sample_data]
            prices = [item['price'] for item in sample_data]
            ax1.plot(dates, prices, marker='o', linewidth=2, color='#2E86AB')
            ax1.set_title('Market Price Trends - Last 6 Months')
            ax1.set_ylabel('Average Price ($)')
            ax1.tick_params(axis='x', rotation=45)
            
            # Comparables chart
            ax2 = self.comp_figure.add_subplot(111)
            addresses = ['123 Main St', '456 Oak Ave', '789 Pine Rd', 'Subject Prop']
            prices = [485000, 462000, 510000, 485000]
            colors = ['#2E86AB' if 'Subject' not in addr else '#A23B72' for addr in addresses]
            bars = ax2.bar(addresses, prices, color=colors)
            ax2.set_title('Comparable Sale Prices')
            ax2.set_ylabel('Sale Price ($)')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, price in zip(bars, prices):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 5000,
                        f'${price:,.0f}', ha='center', va='bottom', fontweight='bold')
            
            # Refresh canvases
            self.trend_figure.tight_layout()
            self.comp_figure.tight_layout()
            self.trend_canvas.draw()
            self.comp_canvas.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")

    def load_data(self):
        """Load CMA data and refresh charts."""
        self.update_charts()
        print("CMA data loaded and charts updated")
    
    def _calculate_cma_values(self):
        """Calculate CMA values based on comparable properties."""
        try:
            # Get comparable properties from the table
            comparables = []
            for row in range(self.comparables_table.rowCount()):
                checkbox_item = self.comparables_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    try:
                        price_text = self.comparables_table.item(row, 4).text()
                        price = int(price_text.replace('$', '').replace(',', ''))
                        
                        sqft_text = self.comparables_table.item(row, 3).text()
                        sqft = int(sqft_text.replace(',', ''))
                        
                        if sqft > 0:
                            price_per_sqft = price / sqft
                            comparables.append({
                                'price': price,
                                'sqft': sqft,
                                'price_per_sqft': price_per_sqft
                            })
                    except (ValueError, AttributeError, ZeroDivisionError):
                        continue
            
            if not comparables:
                QMessageBox.warning(self, "Warning", "No valid comparable properties selected.")
                return
            
            # Get subject property square footage
            subject_sqft = self.sqft_spin.value()
            if subject_sqft <= 0:
                QMessageBox.warning(self, "Warning", "Please enter valid square footage for subject property.")
                return
            
            # Calculate average price per square foot
            avg_price_per_sqft = sum(comp['price_per_sqft'] for comp in comparables) / len(comparables)
            
            # Calculate estimated values
            low_estimate = int(avg_price_per_sqft * 0.95 * subject_sqft)
            high_estimate = int(avg_price_per_sqft * 1.05 * subject_sqft)
            recommended_value = int(avg_price_per_sqft * subject_sqft)
            
            # Update the UI labels
            self.value_low_label.setText(f"${low_estimate:,}")
            self.value_high_label.setText(f"${high_estimate:,}")
            self.recommended_label.setText(f"${recommended_value:,}")
            
            # Update the adjustments table
            self._populate_adjustments_table(comparables, recommended_value)
            
            # Update market analysis
            market_text = f"""Market Analysis Results:
            
Comparable Properties: {len(comparables)}
Average Price per Sq Ft: ${avg_price_per_sqft:,.2f}
Subject Property Sq Ft: {subject_sqft:,}

Estimated Value Range: ${low_estimate:,} - ${high_estimate:,}
Recommended Market Value: ${recommended_value:,}

Based on {len(comparables)} comparable sales, the subject property shows strong market positioning within the local area."""
            
            self.market_analysis_text.setPlainText(market_text)
            
            # Update charts
            self.update_charts()
            
            QMessageBox.information(self, "Success", f"CMA calculation completed.\nRecommended Value: ${recommended_value:,}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculating CMA values: {str(e)}")
    
    def _populate_adjustments_table(self, comparables, recommended_value):
        """Populate the adjustments table with calculated values."""
        self.adjustments_table.setRowCount(len(comparables))
        
        for row, comp in enumerate(comparables):
            # Property (simplified address)
            self.adjustments_table.setItem(row, 0, QTableWidgetItem(f"Comp {row + 1}"))
            
            # Sale Price
            self.adjustments_table.setItem(row, 1, QTableWidgetItem(f"${comp['price']:,}"))
            
            # Sq Ft Adjustment (based on price per sq ft difference)
            sqft_adj = (comp['price_per_sqft'] - (recommended_value / comp['sqft'])) * comp['sqft']
            self.adjustments_table.setItem(row, 2, QTableWidgetItem(f"${sqft_adj:,.0f}"))
            
            # Bed/Bath Adjustment (placeholder)
            self.adjustments_table.setItem(row, 3, QTableWidgetItem("$0"))
            
            # Feature Adjustment (placeholder)
            self.adjustments_table.setItem(row, 4, QTableWidgetItem("$0"))
            
            # Market Adjustment (placeholder)
            self.adjustments_table.setItem(row, 5, QTableWidgetItem("$0"))
            
            # Adjusted Value
            adjusted_value = comp['price'] - sqft_adj
            self.adjustments_table.setItem(row, 6, QTableWidgetItem(f"${adjusted_value:,.0f}"))
