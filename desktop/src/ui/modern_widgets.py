"""
Modern Widget Components for Magic Commander: Real Estate Edition
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import qtawesome as qta
from ui.modern_theme import get_brand_color
from ui.enhanced_animations import add_card_shadow, AnimationManager

class ModernCard(QFrame):
    """Modern card widget with shadow and hover effects"""
    
    clicked = Signal()
    
    def __init__(self, title="", subtitle="", icon=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setMinimumWidth(200)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set up card styling
        self.setStyleSheet(f"""
            ModernCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {get_brand_color('bg_secondary')}, 
                    stop:1 {get_brand_color('bg_tertiary')});
                border: 1px solid {get_brand_color('gray_700')};
                border-radius: 12px;
                padding: 16px;
            }}
            ModernCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {get_brand_color('bg_tertiary')}, 
                    stop:1 {get_brand_color('bg_accent')});
                border-color: {get_brand_color('unicorn_primary')};
            }}
        """)
        
        # Add shadow effect
        add_card_shadow(self, blur_radius=10, offset=(0, 4))
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon (if provided)
        if icon:
            icon_label = QLabel()
            if isinstance(icon, str):
                # FontAwesome icon
                icon_pixmap = qta.icon(icon, color=get_brand_color('unicorn_primary')).pixmap(32, 32)
                icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('gray_100')};
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }}
        """)
        text_layout.addWidget(title_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_400')};
                    font-size: 13px;
                    margin: 0;
                }}
            """)
            text_layout.addWidget(subtitle_label)
        
        text_layout.addStretch()
        layout.addLayout(text_layout)
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """Handle click events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class StatCard(QFrame):
    """Statistical display card with large numbers"""
    
    def __init__(self, title="", value="", subtitle="", color=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(140)
        self.setMinimumWidth(180)
        
        # Default color
        accent_color = color or get_brand_color('unicorn_primary')
        
        # Card styling
        self.setStyleSheet(f"""
            StatCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {get_brand_color('bg_secondary')}, 
                    stop:1 {get_brand_color('bg_primary')});
                border: 1px solid {get_brand_color('gray_700')};
                border-left: 4px solid {accent_color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        # Add shadow
        add_card_shadow(self, blur_radius=8, offset=(0, 2))
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {get_brand_color('gray_400')};
                font-size: 12px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)
        layout.addWidget(title_label)
        
        # Value (large number)
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 28px;
                font-weight: 700;
                margin: 4px 0;
            }}
        """)
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {get_brand_color('gray_500')};
                    font-size: 11px;
                }}
            """)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()

class ModernSeparator(QFrame):
    """Modern separator line"""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(1)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, 
                    stop:0.5 {get_brand_color('gray_700')}, 
                    stop:1 transparent);
                border: none;
            }}
        """)

class ModernSection(QFrame):
    """Modern section container with title"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        # Section styling
        self.setStyleSheet(f"""
            ModernSection {{
                background-color: {get_brand_color('bg_secondary')};
                border: 1px solid {get_brand_color('gray_700')};
                border-radius: 12px;
                margin: 8px 0;
            }}
        """)
        
        # Add subtle shadow
        add_card_shadow(self, blur_radius=5, offset=(0, 1))
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        if title:
            header = QFrame()
            header.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {get_brand_color('unicorn_primary')}, 
                        stop:1 {get_brand_color('unicorn_secondary')});
                    border-radius: 12px 12px 0 0;
                    padding: 12px 20px;
                }}
            """)
            
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(20, 12, 20, 12)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            
            self.main_layout.addWidget(header)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 16, 20, 20)
        self.main_layout.addWidget(self.content_widget)
    
    def add_widget(self, widget):
        """Add widget to content area"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to content area"""
        self.content_layout.addLayout(layout)

class ModernButton(QPushButton):
    """Enhanced button with modern styling and animations"""
    
    def __init__(self, text="", icon=None, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.animation_manager = AnimationManager()
        
        # Set icon if provided
        if icon:
            if isinstance(icon, str):
                self.setIcon(qta.icon(icon, color='white' if primary else get_brand_color('gray_300')))
        
        # Apply styling
        self._apply_style()
        
        # Set up hover animations
        self.setCursor(Qt.PointingHandCursor)
    
    def _apply_style(self):
        """Apply button styling"""
        if self.primary:
            style = f"""
                ModernButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {get_brand_color('unicorn_primary')}, 
                        stop:1 {get_brand_color('unicorn_secondary')});
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                    min-height: 20px;
                }}
                ModernButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {get_brand_color('unicorn_secondary')}, 
                        stop:1 {get_brand_color('unicorn_accent')});
                }}
                ModernButton:pressed {{
                    background: {get_brand_color('unicorn_accent')};
                }}
            """
        else:
            style = f"""
                ModernButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {get_brand_color('bg_tertiary')}, 
                        stop:1 {get_brand_color('bg_secondary')});
                    color: {get_brand_color('gray_100')};
                    border: 2px solid {get_brand_color('gray_600')};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 20px;
                }}
                ModernButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {get_brand_color('bg_accent')}, 
                        stop:1 {get_brand_color('bg_tertiary')});
                    border-color: {get_brand_color('unicorn_primary')};
                    color: white;
                }}
                ModernButton:pressed {{
                    background: {get_brand_color('unicorn_primary')};
                    border-color: {get_brand_color('unicorn_primary')};
                }}
            """
        
        self.setStyleSheet(style)

class ModernProgressBar(QFrame):
    """Modern progress bar with gradient"""
    
    def __init__(self, value=0, maximum=100, parent=None):
        super().__init__(parent)
        self.value = value
        self.maximum = maximum
        self.setFixedHeight(8)
        
        # Container styling
        self.setStyleSheet(f"""
            ModernProgressBar {{
                background-color: {get_brand_color('gray_700')};
                border-radius: 4px;
            }}
        """)
        
        # Progress fill
        self.progress_fill = QFrame(self)
        self.progress_fill.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_brand_color('unicorn_primary')}, 
                    stop:1 {get_brand_color('unicorn_secondary')});
                border-radius: 4px;
            }}
        """)
        
        self.update_progress()
    
    def setValue(self, value):
        """Update progress value"""
        self.value = max(0, min(value, self.maximum))
        self.update_progress()
    
    def update_progress(self):
        """Update visual progress"""
        if self.maximum > 0:
            progress_width = int((self.value / self.maximum) * self.width())
            self.progress_fill.setGeometry(0, 0, progress_width, self.height())
    
    def resizeEvent(self, event):
        """Handle resize to update progress bar"""
        super().resizeEvent(event)
        self.update_progress()

class ModernLoadingSpinner(QLabel):
    """Modern loading spinner with animation"""
    
    def __init__(self, size=32, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        # Set up spinner icon
        self.setPixmap(qta.icon('fa5s.spinner', color=get_brand_color('unicorn_primary')).pixmap(size, size))
        
        # Set up rotation animation
        self.animation_manager = AnimationManager()
        self.start_spinning()
    
    def start_spinning(self):
        """Start the spinning animation"""
        # Note: This would need a proper rotation animation
        # For now, we'll use a simple opacity pulse
        self.animation_manager.pulse_effect(self, 800)