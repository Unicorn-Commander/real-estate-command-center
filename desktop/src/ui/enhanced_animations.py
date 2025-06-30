"""
Enhanced Animations and Visual Effects for Magic Commander: Real Estate Edition
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QWidget
from PySide6.QtGui import QColor
from ui.modern_theme import get_brand_color

class AnimationManager:
    """Manages animations and visual effects throughout the application"""
    
    def __init__(self):
        self.animations = []
    
    def fade_in(self, widget, duration=300, delay=0):
        """Fade in animation for widgets"""
        if delay > 0:
            QTimer.singleShot(delay, lambda: self._perform_fade_in(widget, duration))
        else:
            self._perform_fade_in(widget, duration)
    
    def _perform_fade_in(self, widget, duration):
        """Perform the actual fade in"""
        self.opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
        self.animations.append(self.animation)
    
    def slide_in_from_right(self, widget, duration=400):
        """Slide widget in from the right"""
        start_pos = widget.pos()
        widget.move(start_pos.x() + 300, start_pos.y())
        
        self.animation = QPropertyAnimation(widget, b"pos")
        self.animation.setDuration(duration)
        self.animation.setStartValue(widget.pos())
        self.animation.setEndValue(start_pos)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
        self.animations.append(self.animation)
    
    def pulse_effect(self, widget, duration=1000):
        """Create a subtle pulse effect"""
        self.opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.7)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.finished.connect(lambda: self._pulse_reverse(widget, duration))
        self.animation.start()
        self.animations.append(self.animation)
    
    def _pulse_reverse(self, widget, duration):
        """Reverse pulse animation"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.7)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.finished.connect(lambda: self.pulse_effect(widget, duration))
        self.animation.start()

def add_card_shadow(widget, color=None, blur_radius=15, offset=(0, 2)):
    """Add modern card-style shadow to any widget"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(color or get_brand_color('gray_900')))
    shadow.setOffset(offset[0], offset[1])
    widget.setGraphicsEffect(shadow)
    return shadow

def add_glow_effect(widget, color=None, blur_radius=20):
    """Add a subtle glow effect"""
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(blur_radius)
    glow.setColor(QColor(color or get_brand_color('unicorn_primary')))
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)
    return glow

class HoverEffectMixin:
    """Mixin to add hover effects to any widget"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_stylesheet = ""
        self._hover_stylesheet = ""
    
    def set_hover_style(self, hover_stylesheet):
        """Set the stylesheet to apply on hover"""
        self._original_stylesheet = self.styleSheet()
        self._hover_stylesheet = hover_stylesheet
    
    def enterEvent(self, event):
        """Apply hover style on mouse enter"""
        if self._hover_stylesheet:
            self.setStyleSheet(self._hover_stylesheet)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Restore original style on mouse leave"""
        if self._original_stylesheet is not None:
            self.setStyleSheet(self._original_stylesheet)
        super().leaveEvent(event)

def create_modern_card_style(base_color=None, hover_color=None):
    """Create modern card-style CSS"""
    base_color = base_color or get_brand_color('bg_secondary')
    hover_color = hover_color or get_brand_color('bg_tertiary')
    
    return f"""
        QWidget {{
            background-color: {base_color};
            border: 1px solid {get_brand_color('gray_700')};
            border-radius: 12px;
            padding: 16px;
            margin: 8px;
        }}
        QWidget:hover {{
            background-color: {hover_color};
            border-color: {get_brand_color('unicorn_primary')};
        }}
    """

def create_modern_button_style(primary=False):
    """Create modern button styling"""
    if primary:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {get_brand_color('unicorn_primary')}, 
                    stop:1 {get_brand_color('unicorn_secondary')});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {get_brand_color('unicorn_secondary')}, 
                    stop:1 {get_brand_color('unicorn_accent')});
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                transform: translateY(1px);
            }}
        """
    else:
        return f"""
            QPushButton {{
                background: {get_brand_color('bg_tertiary')};
                color: {get_brand_color('gray_100')};
                border: 2px solid {get_brand_color('gray_600')};
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {get_brand_color('bg_accent')};
                border-color: {get_brand_color('unicorn_primary')};
                color: white;
            }}
            QPushButton:pressed {{
                background: {get_brand_color('unicorn_primary')};
            }}
        """