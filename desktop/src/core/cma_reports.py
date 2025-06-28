"""
Professional CMA report generation with charts and PDF export.
"""
import os
import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from io import BytesIO
import base64


class CMAChartGenerator:
    """Generate professional charts for CMA reports."""
    
    def __init__(self):
        # Set professional styling
        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E41']
        
    def create_price_trend_chart(self, data: List[Dict], save_path: str = None) -> str:
        """Create a price trend chart over time."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data if none provided
        if not data:
            dates = [datetime.date(2024, i, 1) for i in range(1, 13)]
            prices = [450000, 455000, 462000, 458000, 465000, 470000, 
                     475000, 480000, 478000, 485000, 490000, 495000]
        else:
            dates = [item['date'] for item in data]
            prices = [item['price'] for item in data]
        
        ax.plot(dates, prices, marker='o', linewidth=3, markersize=8, 
                color=self.colors[0], markerfacecolor=self.colors[1])
        
        ax.set_title('Market Price Trends - Last 12 Months', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average Sale Price ($)', fontsize=12, fontweight='bold')
        
        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Format x-axis for dates
        if dates and isinstance(dates[0], datetime.date):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            # Return base64 encoded image for embedding
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            return f"data:image/png;base64,{image_base64}"
    
    def create_comparables_chart(self, comparables: List[Dict], save_path: str = None) -> str:
        """Create a chart comparing property values."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Sample data if none provided
        if not comparables:
            comparables = [
                {'address': '123 Main St', 'price': 485000, 'sqft': 2100, 'price_per_sqft': 231},
                {'address': '456 Oak Ave', 'price': 462000, 'sqft': 1950, 'price_per_sqft': 237},
                {'address': '789 Pine Rd', 'price': 510000, 'sqft': 2200, 'price_per_sqft': 232},
                {'address': 'Subject Property', 'price': 485000, 'sqft': 2050, 'price_per_sqft': 237}
            ]
        
        addresses = [comp['address'][:15] + '...' if len(comp['address']) > 15 
                    else comp['address'] for comp in comparables]
        prices = [comp['price'] for comp in comparables]
        price_per_sqft = [comp['price_per_sqft'] for comp in comparables]
        
        # Chart 1: Sale Prices
        bars1 = ax1.bar(addresses, prices, color=[self.colors[0] if 'Subject' not in addr 
                                                 else self.colors[1] for addr in addresses])
        ax1.set_title('Comparable Sale Prices', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Sale Price ($)', fontsize=12, fontweight='bold')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add value labels on bars
        for bar, price in zip(bars1, prices):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 5000,
                    f'${price:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        # Chart 2: Price per Sq Ft
        bars2 = ax2.bar(addresses, price_per_sqft, color=[self.colors[2] if 'Subject' not in addr 
                                                         else self.colors[3] for addr in addresses])
        ax2.set_title('Price per Square Foot', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Price per Sq Ft ($)', fontsize=12, fontweight='bold')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}'))
        
        # Add value labels on bars
        for bar, ppsf in zip(bars2, price_per_sqft):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'${ppsf:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # Rotate x-axis labels
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            return f"data:image/png;base64,{image_base64}"
    
    def create_market_analysis_chart(self, market_data: Dict, save_path: str = None) -> str:
        """Create market analysis dashboard."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Sample data if none provided
        if not market_data:
            market_data = {
                'days_on_market': [25, 30, 22, 28, 35, 20],
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'inventory_levels': {'Active': 45, 'Pending': 23, 'Sold': 67},
                'price_ranges': {'$400-450K': 15, '$450-500K': 25, '$500-550K': 18, '$550K+': 12}
            }
        
        # Chart 1: Days on Market Trend
        ax1.plot(market_data['months'], market_data['days_on_market'], 
                marker='o', linewidth=3, color=self.colors[0])
        ax1.set_title('Average Days on Market', fontweight='bold')
        ax1.set_ylabel('Days')
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Current Inventory
        inventory_data = market_data['inventory_levels']
        ax2.pie(inventory_data.values(), labels=inventory_data.keys(), autopct='%1.1f%%',
                colors=self.colors[:len(inventory_data)])
        ax2.set_title('Current Market Inventory', fontweight='bold')
        
        # Chart 3: Price Range Distribution
        price_data = market_data['price_ranges']
        ax3.bar(price_data.keys(), price_data.values(), color=self.colors[1])
        ax3.set_title('Sales by Price Range', fontweight='bold')
        ax3.set_ylabel('Number of Sales')
        ax3.tick_params(axis='x', rotation=45)
        
        # Chart 4: Market Condition Indicators
        indicators = ['Absorption\nRate', 'Price\nGrowth', 'Buyer\nDemand', 'Inventory\nLevel']
        values = [7.2, 4.5, 8.1, 6.3]  # Out of 10
        bars = ax4.barh(indicators, values, color=self.colors[2])
        ax4.set_title('Market Strength Indicators', fontweight='bold')
        ax4.set_xlabel('Strength (1-10 scale)')
        ax4.set_xlim(0, 10)
        
        # Add value labels
        for bar, value in zip(bars, values):
            ax4.text(value + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{value}', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            return f"data:image/png;base64,{image_base64}"


class CMAPDFGenerator:
    """Generate professional PDF reports for CMA."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2E86AB'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2E86AB'),
            borderWidth=1,
            borderColor=colors.HexColor('#2E86AB'),
            borderRadius=3,
            backColor=colors.HexColor('#F0F8FF'),
            leftIndent=10,
            rightIndent=10,
            topPadding=8,
            bottomPadding=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=10,
            backColor=colors.HexColor('#E8F5E8'),
            borderWidth=1,
            borderColor=colors.HexColor('#4CAF50'),
            leftIndent=15,
            rightIndent=15,
            topPadding=10,
            bottomPadding=10,
            alignment=TA_CENTER
        ))
    
    def generate_cma_report(self, cma_data: Dict, output_path: str) -> str:
        """Generate a complete CMA PDF report."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Title Page
        story.extend(self._create_title_page(cma_data))
        
        # Executive Summary
        story.extend(self._create_executive_summary(cma_data))
        
        # Property Details
        story.extend(self._create_property_details(cma_data))
        
        # Market Analysis with Charts
        story.extend(self._create_market_analysis(cma_data))
        
        # Comparables Analysis
        story.extend(self._create_comparables_analysis(cma_data))
        
        # Methodology & Disclaimers
        story.extend(self._create_methodology_section())
        
        # Build the PDF
        doc.build(story)
        return output_path
    
    def _create_title_page(self, cma_data: Dict) -> List:
        """Create the title page content."""
        content = []
        
        # Main title
        content.append(Paragraph("COMPARATIVE MARKET ANALYSIS", self.styles['CustomTitle']))
        content.append(Spacer(1, 30))
        
        # Property address
        address = cma_data.get('property_address', '[Property Address]')
        content.append(Paragraph(f"<b>{address}</b>", self.styles['Heading2']))
        content.append(Spacer(1, 20))
        
        # Analysis details table
        analysis_data = [
            ['Prepared For:', cma_data.get('client_name', '[Client Name]')],
            ['Prepared By:', cma_data.get('agent_name', '[Agent Name]')],
            ['Brokerage:', cma_data.get('brokerage', '[Brokerage Name]')],
            ['Analysis Date:', cma_data.get('analysis_date', datetime.date.today().strftime('%B %d, %Y'))],
            ['Report Type:', 'Comparative Market Analysis']
        ]
        
        analysis_table = Table(analysis_data, colWidths=[2*inch, 3*inch])
        analysis_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
        ]))
        
        content.append(analysis_table)
        content.append(Spacer(1, 50))
        
        # Disclaimer
        disclaimer = """
        <i>This Comparative Market Analysis is based on information from the MLS and public records. 
        It is intended to assist in making real estate decisions and should not be considered as 
        a formal appraisal of the property.</i>
        """
        content.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return content
    
    def _create_executive_summary(self, cma_data: Dict) -> List:
        """Create executive summary section."""
        content = []
        content.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        # Value estimate highlight box
        value_estimate = cma_data.get('recommended_value', 485000)
        value_range = cma_data.get('value_range', {'low': 465000, 'high': 505000})
        
        summary_text = f"""
        <b>ESTIMATED MARKET VALUE: ${value_estimate:,}</b><br/>
        <b>Value Range: ${value_range['low']:,} - ${value_range['high']:,}</b>
        """
        content.append(Paragraph(summary_text, self.styles['HighlightBox']))
        content.append(Spacer(1, 20))
        
        # Market summary
        market_summary = cma_data.get('market_summary', 
            "Based on analysis of comparable properties and current market conditions, "
            "the subject property shows strong market positioning with competitive pricing "
            "relative to recent sales in the area.")
        
        content.append(Paragraph("<b>Market Analysis:</b>", self.styles['Heading3']))
        content.append(Paragraph(market_summary, self.styles['Normal']))
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_property_details(self, cma_data: Dict) -> List:
        """Create property details section."""
        content = []
        content.append(Paragraph("SUBJECT PROPERTY DETAILS", self.styles['SectionHeader']))
        
        # Property specs table
        property_data = [
            ['Address:', cma_data.get('property_address', '[Address]')],
            ['Property Type:', cma_data.get('property_type', 'Single Family')],
            ['Bedrooms:', str(cma_data.get('bedrooms', 0))],
            ['Bathrooms:', str(cma_data.get('bathrooms', 0))],
            ['Square Feet:', f"{cma_data.get('sqft', 0):,}"],
            ['Lot Size:', f"{cma_data.get('lot_size', 0)} acres"],
            ['Year Built:', str(cma_data.get('year_built', 0))],
            ['Garage:', 'Yes' if cma_data.get('garage', False) else 'No'],
            ['Pool:', 'Yes' if cma_data.get('pool', False) else 'No'],
        ]
        
        property_table = Table(property_data, colWidths=[2*inch, 3*inch])
        property_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        content.append(property_table)
        content.append(Spacer(1, 20))
        
        # Property Photos Section
        photos = cma_data.get('photos', [])
        if photos:
            content.append(Paragraph("Property Photos", self.styles['Heading3']))
            
            # Add photos in grid layout (2 per row)
            for i in range(0, len(photos), 2):
                photo_row = []
                
                for j in range(2):
                    if i + j < len(photos):
                        photo = photos[i + j]
                        try:
                            if os.path.exists(photo['path']):
                                img = Image(photo['path'], width=2.5*inch, height=2*inch)
                                photo_data = [
                                    [img],
                                    [Paragraph(f"<b>{photo['title']}</b>", self.styles['Normal'])]
                                ]
                                photo_table = Table(photo_data, colWidths=[2.5*inch])
                                photo_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                ]))
                                photo_row.append(photo_table)
                            else:
                                photo_row.append(Paragraph("Photo not found", self.styles['Normal']))
                        except Exception as e:
                            photo_row.append(Paragraph(f"Error loading photo: {str(e)}", self.styles['Normal']))
                    else:
                        photo_row.append("")  # Empty cell for odd number of photos
                
                if photo_row:
                    photos_table = Table([photo_row], colWidths=[3*inch, 3*inch])
                    photos_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                    ]))
                    content.append(photos_table)
            
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_market_analysis(self, cma_data: Dict) -> List:
        """Create market analysis section with charts."""
        content = []
        content.append(Paragraph("MARKET ANALYSIS", self.styles['SectionHeader']))
        
        # Generate and embed charts
        chart_gen = CMAChartGenerator()
        
        # Create temporary chart files
        trend_chart = chart_gen.create_price_trend_chart(
            cma_data.get('price_trends', []),
            '/tmp/trend_chart.png'
        )
        
        market_chart = chart_gen.create_market_analysis_chart(
            cma_data.get('market_data', {}),
            '/tmp/market_chart.png'
        )
        
        # Add charts to PDF
        if os.path.exists(trend_chart):
            content.append(Image(trend_chart, width=6*inch, height=3.6*inch))
            content.append(Spacer(1, 20))
        
        if os.path.exists(market_chart):
            content.append(Image(market_chart, width=6*inch, height=4.8*inch))
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_comparables_analysis(self, cma_data: Dict) -> List:
        """Create comparables analysis section."""
        content = []
        content.append(Paragraph("COMPARABLE PROPERTIES ANALYSIS", self.styles['SectionHeader']))
        
        # Comparables table
        comparables = cma_data.get('comparables', [])
        if not comparables:
            # Sample data
            comparables = [
                {'address': '123 Main St', 'price': 485000, 'sqft': 2100, 'beds': 4, 'baths': 2.5, 'sold_date': '2024-05-15'},
                {'address': '456 Oak Ave', 'price': 462000, 'sqft': 1950, 'beds': 3, 'baths': 2, 'sold_date': '2024-04-22'},
                {'address': '789 Pine Rd', 'price': 510000, 'sqft': 2200, 'beds': 4, 'baths': 3, 'sold_date': '2024-06-01'},
            ]
        
        # Create comparables table
        table_data = [['Address', 'Sale Price', 'Sq Ft', 'Beds/Baths', 'Sale Date', '$/Sq Ft']]
        
        for comp in comparables:
            price_per_sqft = comp['price'] / comp['sqft'] if comp['sqft'] > 0 else 0
            table_data.append([
                comp['address'][:25],
                f"${comp['price']:,}",
                f"{comp['sqft']:,}",
                f"{comp['beds']}/{comp['baths']}",
                comp['sold_date'],
                f"${price_per_sqft:.0f}"
            ])
        
        comp_table = Table(table_data, colWidths=[2*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
        ]))
        
        content.append(comp_table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_methodology_section(self) -> List:
        """Create methodology and disclaimers section."""
        content = []
        content.append(Paragraph("METHODOLOGY & DISCLAIMERS", self.styles['SectionHeader']))
        
        methodology_text = """
        <b>Methodology:</b><br/>
        This Comparative Market Analysis was prepared using the following methodology:
        <br/><br/>
        • Analysis of recently sold properties within 1 mile radius of subject property<br/>
        • Properties selected based on similarity in size, age, and features<br/>
        • Adjustments made for differences in square footage, lot size, and amenities<br/>
        • Current market conditions and trends considered<br/>
        • Data sourced from MLS, public records, and market reports<br/>
        <br/>
        <b>Important Disclaimers:</b><br/>
        • This analysis is not an appraisal and should not be used as such<br/>
        • Market conditions can change rapidly affecting property values<br/>
        • Individual property characteristics may significantly impact value<br/>
        • Consult with a licensed appraiser for official valuation<br/>
        • Agent and brokerage make no warranty as to accuracy of information<br/>
        """
        
        content.append(Paragraph(methodology_text, self.styles['Normal']))
        
        return content


def generate_sample_cma_data() -> Dict:
    """Generate sample CMA data for testing."""
    return {
        'property_address': '123 Sample Street, Anytown, ST 12345',
        'client_name': 'John & Jane Smith',
        'agent_name': 'Real Estate Agent',
        'brokerage': 'Premier Realty Group',
        'analysis_date': datetime.date.today().strftime('%B %d, %Y'),
        'property_type': 'Single Family',
        'bedrooms': 4,
        'bathrooms': 2.5,
        'sqft': 2050,
        'lot_size': 0.25,
        'year_built': 1995,
        'garage': True,
        'pool': False,
        'recommended_value': 485000,
        'value_range': {'low': 465000, 'high': 505000},
        'market_summary': 'The local market shows strong buyer activity with low inventory levels. Properties in this price range are selling within 30 days on average.',
        'comparables': [
            {'address': '456 Nearby Ave', 'price': 475000, 'sqft': 2000, 'beds': 4, 'baths': 2, 'sold_date': '2024-05-15'},
            {'address': '789 Close St', 'price': 495000, 'sqft': 2100, 'beds': 4, 'baths': 2.5, 'sold_date': '2024-04-22'},
            {'address': '321 Similar Rd', 'price': 462000, 'sqft': 1950, 'beds': 3, 'baths': 2, 'sold_date': '2024-06-01'},
        ]
    }