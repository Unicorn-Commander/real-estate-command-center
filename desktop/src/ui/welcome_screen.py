"""
Modern Welcome Screen for Magic Commander: Real Estate Edition
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient
import qtawesome as qta

class WelcomeScreen(QDialog):
    """Modern animated welcome screen with branding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Magic Commander: Real Estate Edition")
        self.setModal(True)
        self.setFixedSize(600, 400)
        
        # Remove window frame for modern look
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        self.setup_animations()
        
        # Auto-close timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.accept)
        self.timer.setSingleShot(True)
        self.timer.start(3000)  # 3 seconds
    
    def setup_ui(self):
        """Setup the welcome screen UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container with rounded corners and shadow
        self.main_frame = QFrame()
        self.main_frame.setObjectName("welcomeFrame")
        self.main_frame.setStyleSheet("""
            QFrame#welcomeFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0F172A, stop:0.5 #1E293B, stop:1 #334155);
                border-radius: 20px;
                border: 2px solid #8B5CF6;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(139, 92, 246, 100))  # Purple shadow
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        layout.addWidget(self.main_frame)
        
        # Content layout
        content_layout = QVBoxLayout(self.main_frame)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo area (placeholder for now)
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        # Magic/Unicorn icon
        self.logo_icon = QLabel()
        icon = qta.icon('fa5s.magic', color='#8B5CF6', scale_factor=3.0)
        pixmap = icon.pixmap(64, 64)
        self.logo_icon.setPixmap(pixmap)
        self.logo_icon.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.logo_icon)
        
        # Unicorn Commander text logo (placeholder)
        self.logo_text = QLabel("🦄")
        self.logo_text.setAlignment(Qt.AlignCenter)
        self.logo_text.setStyleSheet("font-size: 48px;")
        logo_layout.addWidget(self.logo_text)
        
        logo_layout.addStretch()
        content_layout.addLayout(logo_layout)
        
        # Main title
        self.title_label = QLabel("Magic Commander")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #F9FAFB;
                font-size: 32px;
                font-weight: bold;
                font-family: "Inter", "Segoe UI", sans-serif;
                margin: 0;
            }
        """)
        content_layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Real Estate Edition")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #8B5CF6;
                font-size: 18px;
                font-weight: 500;
                font-family: "Inter", "Segoe UI", sans-serif;
                margin: 0;
            }
        """)
        content_layout.addWidget(self.subtitle_label)
        
        # Description
        self.desc_label = QLabel("AI-Powered Professional Real Estate Management")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-weight: 400;
                margin: 10px 0;
            }
        """)
        content_layout.addWidget(self.desc_label)
        
        # Powered by section
        powered_layout = QHBoxLayout()
        powered_layout.addStretch()
        
        powered_label = QLabel("Powered by")
        powered_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 12px;
            }
        """)
        powered_layout.addWidget(powered_label)
        
        unicorn_commander_label = QLabel("Unicorn Commander")
        unicorn_commander_label.setStyleSheet("""
            QLabel {
                color: #06B6D4;
                font-size: 12px;
                font-weight: 600;
                margin-left: 4px;
            }
        """)
        powered_layout.addWidget(unicorn_commander_label)
        
        magic_unicorn_label = QLabel("• Magic Unicorn Tech")
        magic_unicorn_label.setStyleSheet("""
            QLabel {
                color: #EC4899;
                font-size: 12px;
                font-weight: 600;
                margin-left: 8px;
            }
        """)
        powered_layout.addWidget(magic_unicorn_label)
        
        powered_layout.addStretch()
        content_layout.addLayout(powered_layout)
        
        content_layout.addStretch()
        
        # Loading indicator
        self.loading_label = QLabel("Loading AI systems...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #8B5CF6;
                font-size: 12px;
                font-style: italic;
            }
        """)
        content_layout.addWidget(self.loading_label)
        
        # Progress dots
        dots_layout = QHBoxLayout()
        dots_layout.addStretch()
        
        self.dots = []
        for i in range(4):
            dot = QLabel("●")
            dot.setStyleSheet("""
                QLabel {
                    color: #374151;
                    font-size: 16px;
                }
            """)
            dot.setAlignment(Qt.AlignCenter)
            dots_layout.addWidget(dot)
            self.dots.append(dot)
        
        dots_layout.addStretch()
        content_layout.addLayout(dots_layout)
        
        # Close button (hidden initially)
        self.close_button = QPushButton("Continue")
        self.close_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B5CF6, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #06B6D4, stop:1 #8B5CF6);
            }
        """)
        self.close_button.clicked.connect(self.accept)
        self.close_button.hide()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)
    
    def setup_animations(self):
        """Setup loading animations"""
        self.dot_animations = []
        
        for i, dot in enumerate(self.dots):
            # Create animation for each dot
            timer = QTimer()
            timer.timeout.connect(lambda d=dot: self.animate_dot(d))
            timer.start(200 + i * 150)  # Staggered animation
            self.dot_animations.append(timer)
        
        # Animation to show continue button
        continue_timer = QTimer()
        continue_timer.timeout.connect(self.show_continue_button)
        continue_timer.setSingleShot(True)
        continue_timer.start(2500)
    
    def animate_dot(self, dot):
        """Animate a loading dot"""
        current_color = dot.styleSheet()
        if "#8B5CF6" in current_color:
            # Purple to gray
            dot.setStyleSheet("""
                QLabel {
                    color: #374151;
                    font-size: 16px;
                }
            """)
        else:
            # Gray to purple
            dot.setStyleSheet("""
                QLabel {
                    color: #8B5CF6;
                    font-size: 16px;
                }
            """)
    
    def show_continue_button(self):
        """Show the continue button"""
        self.loading_label.setText("Ready to launch! ✨")
        self.close_button.show()
        
        # Stop dot animations
        for timer in self.dot_animations:
            timer.stop()
        
        # Set all dots to active color
        for dot in self.dots:
            dot.setStyleSheet("""
                QLabel {
                    color: #10B981;
                    font-size: 16px;
                }
            """)
    
    def mousePressEvent(self, event):
        """Allow clicking anywhere to close"""
        if hasattr(self, 'close_button') and self.close_button.isVisible():
            self.accept()
        super().mousePressEvent(event)