"""
Property Photo Widget - Display MLS property photos with navigation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QUrl
from PySide6.QtGui import QPixmap, QPalette, QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import qtawesome as qta
import logging

logger = logging.getLogger(__name__)

class PhotoThumbnail(QFrame):
    """Clickable photo thumbnail"""
    
    clicked = Signal(int)  # Emits photo index when clicked
    
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFrameStyle(QFrame.Box)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(QSize(120, 90))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setScaledContents(True)
        self.photo_label.setStyleSheet("background-color: #f0f0f0;")
        
        layout.addWidget(self.photo_label)
        self.setLayout(layout)
        
    def set_photo(self, pixmap: QPixmap):
        """Set the thumbnail photo"""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(116, 86, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(scaled)
        else:
            self.photo_label.setText("No Image")
            
    def set_selected(self, selected: bool):
        """Update appearance when selected"""
        if selected:
            self.setFrameStyle(QFrame.Box)
            self.setStyleSheet("QFrame { border: 3px solid #4CAF50; }")
        else:
            self.setFrameStyle(QFrame.Box)
            self.setStyleSheet("")
            
    def mousePressEvent(self, event):
        """Handle click events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)

class PropertyPhotoWidget(QWidget):
    """Widget for displaying property photos from MLS"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.photos = []
        self.current_index = 0
        self.network_manager = QNetworkAccessManager()
        self.photo_cache = {}  # Cache loaded photos
        self.thumbnails = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Property Photos")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.count_label = QLabel("0 photos")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Main photo display
        self.main_photo_label = QLabel()
        self.main_photo_label.setAlignment(Qt.AlignCenter)
        self.main_photo_label.setMinimumHeight(400)
        self.main_photo_label.setStyleSheet("""
            QLabel {
                background-color: #000;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        self.main_photo_label.setScaledContents(False)
        layout.addWidget(self.main_photo_label, 1)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton(qta.icon('fa5s.chevron-left'), "Previous")
        self.prev_button.clicked.connect(self.show_previous)
        nav_layout.addWidget(self.prev_button)
        
        nav_layout.addStretch()
        
        self.photo_index_label = QLabel("0 / 0")
        self.photo_index_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.photo_index_label)
        
        nav_layout.addStretch()
        
        self.next_button = QPushButton(qta.icon('fa5s.chevron-right'), "Next")
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # Thumbnail strip
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumbnail_scroll.setMaximumHeight(110)
        self.thumbnail_scroll.setWidgetResizable(True)
        
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QHBoxLayout()
        self.thumbnail_layout.setSpacing(5)
        self.thumbnail_widget.setLayout(self.thumbnail_layout)
        self.thumbnail_scroll.setWidget(self.thumbnail_widget)
        
        layout.addWidget(self.thumbnail_scroll)
        
        self.setLayout(layout)
        self.update_controls()
        
    def load_photos(self, photo_urls: list):
        """Load photos from URLs"""
        self.photos = photo_urls
        self.current_index = 0
        self.photo_cache.clear()
        
        # Clear existing thumbnails
        for thumb in self.thumbnails:
            thumb.deleteLater()
        self.thumbnails.clear()
        
        # Create new thumbnails
        for i, photo_url in enumerate(photo_urls):
            thumb = PhotoThumbnail(i)
            thumb.clicked.connect(self.show_photo)
            self.thumbnail_layout.addWidget(thumb)
            self.thumbnails.append(thumb)
            
            # Load thumbnail
            self.load_photo_async(photo_url, i, is_thumbnail=True)
            
        # Add stretch at the end
        self.thumbnail_layout.addStretch()
        
        # Update UI
        self.count_label.setText(f"{len(photo_urls)} photos")
        self.update_controls()
        
        # Load first photo
        if photo_urls:
            self.show_photo(0)
            
    def load_photo_async(self, url: str, index: int, is_thumbnail: bool = False):
        """Load a photo asynchronously"""
        if not url:
            return
            
        # Check cache first
        cache_key = f"{url}_{is_thumbnail}"
        if cache_key in self.photo_cache:
            if is_thumbnail and index < len(self.thumbnails):
                self.thumbnails[index].set_photo(self.photo_cache[cache_key])
            elif not is_thumbnail and index == self.current_index:
                self.display_main_photo(self.photo_cache[cache_key])
            return
            
        # Load from network
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        
        # Store metadata in reply
        reply.setProperty("photo_index", index)
        reply.setProperty("is_thumbnail", is_thumbnail)
        reply.setProperty("url", url)
        
        reply.finished.connect(lambda: self.on_photo_loaded(reply))
        
    def on_photo_loaded(self, reply: QNetworkReply):
        """Handle loaded photo"""
        try:
            if reply.error() == QNetworkReply.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                
                if not pixmap.isNull():
                    index = reply.property("photo_index")
                    is_thumbnail = reply.property("is_thumbnail")
                    url = reply.property("url")
                    
                    # Cache the photo
                    cache_key = f"{url}_{is_thumbnail}"
                    self.photo_cache[cache_key] = pixmap
                    
                    # Display the photo
                    if is_thumbnail and index < len(self.thumbnails):
                        self.thumbnails[index].set_photo(pixmap)
                    elif not is_thumbnail and index == self.current_index:
                        self.display_main_photo(pixmap)
            else:
                logger.error(f"Failed to load photo: {reply.errorString()}")
                
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
        finally:
            reply.deleteLater()
            
    def display_main_photo(self, pixmap: QPixmap):
        """Display photo in main viewer"""
        if pixmap and not pixmap.isNull():
            # Scale to fit while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.main_photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.main_photo_label.setPixmap(scaled)
        else:
            self.main_photo_label.setText("Loading...")
            
    def show_photo(self, index: int):
        """Show a specific photo"""
        if 0 <= index < len(self.photos):
            self.current_index = index
            
            # Update thumbnail selection
            for i, thumb in enumerate(self.thumbnails):
                thumb.set_selected(i == index)
                
            # Load main photo
            self.load_photo_async(self.photos[index], index, is_thumbnail=False)
            
            # Update controls
            self.update_controls()
            
            # Scroll thumbnail into view
            if index < len(self.thumbnails):
                self.thumbnail_scroll.ensureWidgetVisible(self.thumbnails[index])
                
    def show_previous(self):
        """Show previous photo"""
        if self.current_index > 0:
            self.show_photo(self.current_index - 1)
            
    def show_next(self):
        """Show next photo"""
        if self.current_index < len(self.photos) - 1:
            self.show_photo(self.current_index + 1)
            
    def update_controls(self):
        """Update navigation controls"""
        has_photos = len(self.photos) > 0
        
        self.prev_button.setEnabled(has_photos and self.current_index > 0)
        self.next_button.setEnabled(has_photos and self.current_index < len(self.photos) - 1)
        
        if has_photos:
            self.photo_index_label.setText(f"{self.current_index + 1} / {len(self.photos)}")
        else:
            self.photo_index_label.setText("0 / 0")
            self.main_photo_label.setText("No photos available")
            
    def clear_photos(self):
        """Clear all photos"""
        self.photos = []
        self.current_index = 0
        self.photo_cache.clear()
        
        for thumb in self.thumbnails:
            thumb.deleteLater()
        self.thumbnails.clear()
        
        self.main_photo_label.clear()
        self.main_photo_label.setText("No photos available")
        self.count_label.setText("0 photos")
        self.update_controls()