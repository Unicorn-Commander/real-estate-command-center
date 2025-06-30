"""
Modern Theme System for Magic Commander: Real Estate Edition
Professional SaaS-style design with gaming/tech inspiration
"""

# Brand Colors - Magic Unicorn Tech / Unicorn Commander Theme
BRAND_COLORS = {
    # Primary Brand Colors (Magic Commander theme)
    'unicorn_primary': '#8B5CF6',      # Purple (vibrant)
    'unicorn_secondary': '#06B6D4',    # Cyan (tech)
    'unicorn_accent': '#EC4899',       # Pink/Magenta (modern)
    
    # Neutral Grays (modern)
    'gray_50': '#F9FAFB',
    'gray_100': '#F3F4F6',
    'gray_200': '#E5E7EB',
    'gray_300': '#D1D5DB',
    'gray_400': '#9CA3AF',
    'gray_500': '#6B7280',
    'gray_600': '#4B5563',
    'gray_700': '#374151',
    'gray_800': '#1F2937',
    'gray_900': '#111827',
    
    # Status Colors
    'success': '#10B981',
    'warning': '#F97316',      # Orange (warmer than amber)
    'error': '#EF4444',
    'info': '#3B82F6',
    
    # Background Variants
    'bg_primary': '#0F172A',      # Slate 900
    'bg_secondary': '#1E293B',    # Slate 800
    'bg_tertiary': '#334155',     # Slate 700
    'bg_accent': '#475569',       # Slate 600
}

# Typography
FONTS = {
    'primary': 'Segoe UI, system-ui, -apple-system, sans-serif',
    'heading': '"Inter", "Segoe UI", system-ui, sans-serif',
    'mono': '"JetBrains Mono", "Fira Code", "Consolas", monospace',
}

# Modern Qt Stylesheet for Magic Commander: Real Estate Edition
MODERN_STYLESHEET = f"""
/* Global Application Styling */
QApplication {{
    font-family: {FONTS['primary']};
    font-size: 13px;
    background-color: {BRAND_COLORS['bg_primary']};
    color: {BRAND_COLORS['gray_100']};
}}

/* Main Window */
QMainWindow {{
    background-color: {BRAND_COLORS['bg_primary']};
    border: none;
}}

QMainWindow::separator {{
    background-color: {BRAND_COLORS['gray_700']};
    width: 2px;
    height: 2px;
}}

/* Menu Bar - Modern flat design */
QMenuBar {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: none;
    padding: 4px;
    font-weight: 500;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px;
}}

QMenuBar::item:selected {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QMenuBar::item:pressed {{
    background-color: {BRAND_COLORS['unicorn_secondary']};
}}

/* Menu Dropdown */
QMenu {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: 1px solid {BRAND_COLORS['gray_700']};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
    margin: 1px;
}}

QMenu::item:selected {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background-color: {BRAND_COLORS['gray_700']};
    margin: 4px;
}}

/* Toolbar - Modern flat with subtle shadows */
QToolBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_secondary']}, 
        stop:1 {BRAND_COLORS['bg_primary']});
    border: none;
    border-bottom: 1px solid {BRAND_COLORS['gray_700']};
    spacing: 4px;
    padding: 8px;
}}

QToolBar QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px;
    margin: 2px;
    color: {BRAND_COLORS['gray_300']};
    font-weight: 500;
}}

QToolBar QToolButton:hover {{
    background-color: {BRAND_COLORS['bg_tertiary']};
    color: {BRAND_COLORS['unicorn_primary']};
}}

QToolBar QToolButton:pressed {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QToolBar QToolButton:checked {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QToolBar::separator {{
    background-color: {BRAND_COLORS['gray_700']};
    width: 1px;
    margin: 4px 8px;
}}

/* Status Bar - Sleek bottom bar */
QStatusBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_primary']}, 
        stop:1 {BRAND_COLORS['bg_secondary']});
    color: {BRAND_COLORS['gray_300']};
    border-top: 1px solid {BRAND_COLORS['gray_700']};
    padding: 4px 8px;
    font-size: 12px;
}}

/* Tab Widget - Modern card-style tabs */
QTabWidget {{
    background-color: {BRAND_COLORS['bg_primary']};
}}

QTabWidget::pane {{
    background-color: {BRAND_COLORS['bg_secondary']};
    border: 1px solid {BRAND_COLORS['gray_700']};
    border-radius: 8px;
    margin-top: -1px;
}}

QTabBar::tab {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_tertiary']}, 
        stop:1 {BRAND_COLORS['bg_secondary']});
    color: {BRAND_COLORS['gray_300']};
    border: 1px solid {BRAND_COLORS['gray_700']};
    border-bottom: none;
    padding: 12px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['unicorn_primary']}, 
        stop:1 {BRAND_COLORS['unicorn_secondary']});
    color: white;
    border-color: {BRAND_COLORS['unicorn_primary']};
}}

QTabBar::tab:hover:!selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_accent']}, 
        stop:1 {BRAND_COLORS['bg_tertiary']});
    color: {BRAND_COLORS['gray_100']};
}}

/* Dock Widgets - Modern panel styling */
QDockWidget {{
    background-color: {BRAND_COLORS['bg_secondary']};
    border: 1px solid {BRAND_COLORS['gray_700']};
    border-radius: 8px;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['unicorn_primary']}, 
        stop:1 {BRAND_COLORS['unicorn_secondary']});
    color: white;
    font-weight: bold;
    padding: 8px;
    border-radius: 8px 8px 0 0;
}}

/* Buttons - Modern with hover effects */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_tertiary']}, 
        stop:1 {BRAND_COLORS['bg_secondary']});
    color: {BRAND_COLORS['gray_100']};
    border: 1px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['unicorn_primary']}, 
        stop:1 {BRAND_COLORS['unicorn_secondary']});
    border-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QPushButton:pressed {{
    background: {BRAND_COLORS['unicorn_secondary']};
    border-color: {BRAND_COLORS['unicorn_secondary']};
}}

QPushButton:disabled {{
    background-color: {BRAND_COLORS['gray_700']};
    color: {BRAND_COLORS['gray_500']};
    border-color: {BRAND_COLORS['gray_700']};
}}

/* Primary Action Button */
QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['unicorn_primary']}, 
        stop:1 {BRAND_COLORS['unicorn_secondary']});
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['unicorn_secondary']}, 
        stop:1 {BRAND_COLORS['unicorn_primary']});
}}

/* Input Fields - Modern with focus states */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BRAND_COLORS['bg_primary']};
    color: {BRAND_COLORS['gray_100']};
    border: 2px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {BRAND_COLORS['unicorn_primary']};
    background-color: {BRAND_COLORS['bg_secondary']};
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {BRAND_COLORS['gray_500']};
}}

/* ComboBox - Modern dropdown */
QComboBox {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: 2px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {BRAND_COLORS['gray_500']};
}}

QComboBox:focus {{
    border-color: {BRAND_COLORS['unicorn_primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {BRAND_COLORS['gray_400']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: 1px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    selection-background-color: {BRAND_COLORS['unicorn_primary']};
    outline: none;
}}

/* Table/List Views - Modern data display */
QTableWidget, QListWidget, QTreeWidget {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: 1px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    selection-background-color: {BRAND_COLORS['unicorn_primary']};
    alternate-background-color: {BRAND_COLORS['bg_primary']};
    gridline-color: {BRAND_COLORS['gray_700']};
}}

QTableWidget::item, QListWidget::item, QTreeWidget::item {{
    padding: 8px;
    border: none;
}}

QTableWidget::item:selected, QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    color: white;
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRAND_COLORS['bg_tertiary']}, 
        stop:1 {BRAND_COLORS['bg_secondary']});
    color: {BRAND_COLORS['gray_100']};
    border: none;
    border-right: 1px solid {BRAND_COLORS['gray_700']};
    border-bottom: 1px solid {BRAND_COLORS['gray_700']};
    padding: 8px;
    font-weight: 600;
}}

/* Scrollbars - Minimal modern design */
QScrollBar:vertical {{
    background-color: {BRAND_COLORS['bg_primary']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {BRAND_COLORS['gray_500']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {BRAND_COLORS['bg_primary']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {BRAND_COLORS['gray_500']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* CheckBox and RadioButton - Modern styling */
QCheckBox, QRadioButton {{
    color: {BRAND_COLORS['gray_100']};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {BRAND_COLORS['gray_600']};
    border-radius: 3px;
    background-color: {BRAND_COLORS['bg_primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    border-color: {BRAND_COLORS['unicorn_primary']};
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QRadioButton::indicator:checked {{
    background-color: {BRAND_COLORS['unicorn_primary']};
    border-color: {BRAND_COLORS['unicorn_primary']};
}}

/* Spin Box */
QSpinBox, QDoubleSpinBox {{
    background-color: {BRAND_COLORS['bg_primary']};
    color: {BRAND_COLORS['gray_100']};
    border: 2px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    padding: 6px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {BRAND_COLORS['unicorn_primary']};
}}

/* Group Box - Modern card-style */
QGroupBox {{
    color: {BRAND_COLORS['gray_100']};
    border: 2px solid {BRAND_COLORS['gray_600']};
    border-radius: 8px;
    margin-top: 12px;
    font-weight: 600;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['unicorn_primary']};
}}

/* Progress Bar - Modern design */
QProgressBar {{
    background-color: {BRAND_COLORS['bg_primary']};
    border: 1px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    text-align: center;
    color: {BRAND_COLORS['gray_100']};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {BRAND_COLORS['unicorn_primary']}, 
        stop:1 {BRAND_COLORS['unicorn_secondary']});
    border-radius: 5px;
}}

/* Tooltips - Modern with subtle shadow */
QToolTip {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
    border: 1px solid {BRAND_COLORS['gray_600']};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}}

/* Message Boxes - Consistent styling */
QMessageBox {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 12px;
}}

/* Dialog styling */
QDialog {{
    background-color: {BRAND_COLORS['bg_secondary']};
    color: {BRAND_COLORS['gray_100']};
}}

/* Frame styling for containers */
QFrame {{
    background-color: transparent;
    border: none;
}}

QFrame[frameShape="1"] {{ /* Box frame */
    border: 1px solid {BRAND_COLORS['gray_700']};
    border-radius: 6px;
}}

QFrame[frameShape="4"] {{ /* HLine */
    border: none;
    background-color: {BRAND_COLORS['gray_700']};
    max-height: 1px;
}}

QFrame[frameShape="5"] {{ /* VLine */
    border: none;
    background-color: {BRAND_COLORS['gray_700']};
    max-width: 1px;
}}
"""

def apply_modern_theme(app):
    """Apply the modern theme to the application"""
    app.setStyleSheet(MODERN_STYLESHEET)

def get_brand_color(color_name: str) -> str:
    """Get a brand color by name"""
    return BRAND_COLORS.get(color_name, BRAND_COLORS['gray_500'])

def get_font_family(font_type: str = 'primary') -> str:
    """Get font family by type"""
    return FONTS.get(font_type, FONTS['primary'])