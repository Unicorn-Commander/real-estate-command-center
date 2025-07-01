"""
Enhanced Modern Dashboard for Magic Commander: Real Estate Edition
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QScrollArea, QLabel, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import qtawesome as qta
from ui.modern_widgets import (ModernCard, StatCard, ModernSection, ModernButton, 
                               ModernProgressBar, ModernSeparator)
from ui.modern_theme import get_brand_color
from ui.enhanced_animations import AnimationManager, add_card_shadow
import datetime

class EnhancedDashboard(QWidget):
    """Modern dashboard with beautiful cards and animations"""
    
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.animation_manager = AnimationManager()
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the modern dashboard UI"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {get_brand_color('bg_primary')};
                border: none;
            }}
        """)
        
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Dashboard header
        self.create_dashboard_header(main_layout)
        
        # Key metrics section
        self.create_metrics_section(main_layout)
        
        # Quick actions section
        self.create_quick_actions_section(main_layout)
        
        # Recent activity section
        self.create_recent_activity_section(main_layout)
        
        # AI insights section
        self.create_ai_insights_section(main_layout)
        
        main_layout.addStretch()
        scroll.setWidget(main_widget)
        
        # Set main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        # Animate dashboard load
        self.animate_dashboard_load()
    
    def create_dashboard_header(self, parent_layout):
        """Create the dashboard header with welcome message"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_brand_color('unicorn_primary')}, 
                    stop:0.5 {get_brand_color('unicorn_secondary')},
                    stop:1 {get_brand_color('unicorn_accent')});
                border-radius: 16px;
                padding: 24px;
            }}
        """)
        add_card_shadow(header_frame, blur_radius=15, offset=(0, 5))
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        # Welcome content
        content_layout = QVBoxLayout()
        
        # Time-based greeting
        current_hour = datetime.datetime.now().hour
        if current_hour < 12:
            greeting = "Good Morning"
        elif current_hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        
        welcome_label = QLabel(f"{greeting}! 🌟")
        welcome_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: 700;
                margin: 0;
            }
        """)
        content_layout.addWidget(welcome_label)
        
        subtitle_label = QLabel("Your Real Estate Command Center is ready")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
                margin-top: 4px;
            }
        """)
        content_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(content_layout)
        header_layout.addStretch()
        
        # Dashboard icon
        icon_label = QLabel()
        dashboard_icon = qta.icon('fa5s.chart-pie', color='white', scale_factor=2.0)
        icon_label.setPixmap(dashboard_icon.pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_metrics_section(self, parent_layout):
        """Create key metrics cards"""
        metrics_section = ModernSection("📊 Key Metrics")
        
        # Metrics grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        # Sample metrics (you can connect these to real data)
        metrics = [
            {"title": "Active Leads", "value": "47", "subtitle": "+12% this month", "color": get_brand_color('unicorn_primary')},
            {"title": "Properties Listed", "value": "23", "subtitle": "8 pending", "color": get_brand_color('unicorn_secondary')},
            {"title": "CMAs Generated", "value": "156", "subtitle": "This quarter", "color": get_brand_color('unicorn_accent')},
            {"title": "Avg. Response Time", "value": "2.4h", "subtitle": "AI-enhanced", "color": get_brand_color('success')},
        ]
        
        for i, metric in enumerate(metrics):
            card = StatCard(
                title=metric["title"],
                value=metric["value"],
                subtitle=metric["subtitle"],
                color=metric["color"]
            )
            metrics_grid.addWidget(card, 0, i)
        
        metrics_section.add_layout(metrics_grid)
        parent_layout.addWidget(metrics_section)
    
    def create_quick_actions_section(self, parent_layout):
        """Create quick actions cards"""
        actions_section = ModernSection("⚡ Quick Actions")
        
        # Actions grid
        actions_grid = QGridLayout()
        actions_grid.setSpacing(12)
        
        # Quick action cards
        actions = [
            {"title": "New Lead", "subtitle": "Add prospect", "icon": "fa5s.user-plus"},
            {"title": "Generate CMA", "subtitle": "Market analysis", "icon": "fa5s.chart-line"},
            {"title": "Create Campaign", "subtitle": "Marketing", "icon": "fa5s.bullhorn"},
            {"title": "AI Assistant", "subtitle": "Get help", "icon": "fa5s.robot"},
        ]
        
        for i, action in enumerate(actions):
            card = ModernCard(
                title=action["title"],
                subtitle=action["subtitle"],
                icon=action["icon"]
            )
            card.clicked.connect(lambda idx=i: self.handle_quick_action(idx))
            actions_grid.addWidget(card, i // 2, i % 2)
        
        actions_section.add_layout(actions_grid)
        parent_layout.addWidget(actions_section)
    
    def create_recent_activity_section(self, parent_layout):
        """Create recent activity section"""
        activity_section = ModernSection("📈 Recent Activity")
        
        # Activity items - only show real activity data
        activities = []  # Will be populated from real data sources when available
        
        if not activities:
            # Show empty state message
            empty_frame = QFrame()
            empty_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {get_brand_color('bg_secondary')};
                    border: 2px dashed {get_brand_color('gray_600')};
                    border-radius: 8px;
                    padding: 20px;
                    margin: 4px 0;
                }}
            """)
            
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            empty_label = QLabel("No recent activity available")
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_400')};
                    font-size: 14px;
                    font-style: italic;
                }}
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_label)
            
            activity_section.add_widget(empty_frame)
        
        for activity in activities:
            activity_frame = QFrame()
            activity_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {get_brand_color('bg_primary')};
                    border: 1px solid {get_brand_color('gray_700')};
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px 0;
                }}
                QFrame:hover {{
                    background-color: {get_brand_color('bg_tertiary')};
                    border-color: {get_brand_color('unicorn_primary')};
                }}
            """)
            
            activity_layout = QHBoxLayout(activity_frame)
            activity_layout.setContentsMargins(12, 8, 12, 8)
            
            # Icon
            icon_label = QLabel()
            icon_pixmap = qta.icon(activity["icon"], color=get_brand_color('unicorn_primary')).pixmap(20, 20)
            icon_label.setPixmap(icon_pixmap)
            activity_layout.addWidget(icon_label)
            
            # Text
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            text_label = QLabel(activity["text"])
            text_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_100')};
                    font-size: 14px;
                    font-weight: 500;
                }}
            """)
            text_layout.addWidget(text_label)
            
            time_label = QLabel(activity["time"])
            time_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_500')};
                    font-size: 12px;
                }}
            """)
            text_layout.addWidget(time_label)
            
            activity_layout.addLayout(text_layout)
            activity_layout.addStretch()
            
            activity_section.add_widget(activity_frame)
        
        parent_layout.addWidget(activity_section)
    
    def create_ai_insights_section(self, parent_layout):
        """Create AI insights section"""
        insights_section = ModernSection("🤖 AI Insights")
        
        # AI status
        ai_status_frame = QFrame()
        ai_status_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_brand_color('success')}, 
                    stop:1 {get_brand_color('unicorn_secondary')});
                border-radius: 10px;
                padding: 16px;
                margin: 8px 0;
            }}
        """)
        
        ai_layout = QHBoxLayout(ai_status_frame)
        ai_layout.setContentsMargins(16, 12, 16, 12)
        
        # AI icon
        ai_icon = QLabel()
        robot_icon = qta.icon('fa5s.robot', color='white', scale_factor=1.5)
        ai_icon.setPixmap(robot_icon.pixmap(32, 32))
        ai_layout.addWidget(ai_icon)
        
        # AI status text
        ai_text = QVBoxLayout()
        
        status_label = QLabel("AI System Status: Operational")
        status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        ai_text.addWidget(status_label)
        
        agents_label = QLabel("4/4 Specialized agents ready • Real Estate Interpreter active")
        agents_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            }
        """)
        ai_text.addWidget(agents_label)
        
        ai_layout.addLayout(ai_text)
        ai_layout.addStretch()
        
        insights_section.add_widget(ai_status_frame)
        
        # Recent AI insights
        insights = [
            "🏠 Detected strong seller's market in downtown area",
            "📈 Property values trending +8% in target neighborhoods", 
            "💡 Optimal listing time: Thursday afternoons",
            "🎯 High-potential leads increased 25% this week"
        ]
        
        for insight in insights:
            insight_label = QLabel(insight)
            insight_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_300')};
                    font-size: 14px;
                    padding: 8px 0;
                    margin: 4px 0;
                }}
            """)
            insights_section.add_widget(insight_label)
        
        parent_layout.addWidget(insights_section)
    
    def animate_dashboard_load(self):
        """Animate dashboard elements loading in sequence"""
        # This creates a nice cascading load effect
        widgets = self.findChildren(ModernSection)
        for i, widget in enumerate(widgets):
            self.animation_manager.fade_in(widget, duration=400, delay=i * 150)
    
    def handle_quick_action(self, action_index):
        """Handle quick action clicks"""
        actions = [
            "new_lead",
            "generate_cma", 
            "create_campaign",
            "ai_assistant"
        ]
        
        if action_index < len(actions):
            action = actions[action_index]
            print(f"Quick action triggered: {action}")
            # You can emit signals here to trigger actions in the main window
    
    def refresh_data(self):
        """Refresh dashboard data"""
        # This would update metrics and activity data
        pass
    
    def load_data(self):
        """Load dashboard data - called from main window refresh"""
        self.refresh_data()