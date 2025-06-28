"""
Professional property photo management widget with drag-and-drop upload.
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QGroupBox, QLineEdit, QTextEdit, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QMimeData, QUrl
from PySide6.QtGui import QPixmap, QFont, QDragEnterEvent, QDropEvent, QPainter, QColor
from PIL import Image, ImageDraw, ImageFont


class PhotoThumbnailWidget(QLabel):
    """Individual photo thumbnail widget with controls."""
    
    photo_deleted = Signal(str)  # Emits file path when photo is deleted
    
    def __init__(self, image_path: str, title: str = "", parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.title = title
        self.setFixedSize(200, 180)
        self.setFrameStyle(QFrame.Box)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 5px;
            }
            QLabel:hover {
                border-color: #2E86AB;
                background-color: #f0f8ff;
            }
        """)
        
        self.load_thumbnail()
        self.setup_context_menu()
    
    def load_thumbnail(self):
        """Load and display thumbnail image."""
        try:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale pixmap to fit widget while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    180, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                
                # Add title text overlay if provided
                if self.title:
                    self.add_title_overlay(scaled_pixmap)
            else:
                self.setText("Invalid\nImage")
                
        except Exception as e:
            self.setText(f"Error\nLoading\n{str(e)[:20]}")
    
    def add_title_overlay(self, pixmap: QPixmap):
        """Add title text overlay to the image."""
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent background for text
        painter.fillRect(0, pixmap.height() - 25, pixmap.width(), 25, 
                        QColor(0, 0, 0, 180))
        
        # White text
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(5, pixmap.height() - 8, self.title[:25])
        painter.end()
        
        self.setPixmap(pixmap)
    
    def setup_context_menu(self):
        """Setup right-click context menu."""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Show context menu for photo operations."""
        menu = QMenu(self)
        
        view_action = menu.addAction(qta.icon('fa5s.eye'), "View Full Size")
        edit_action = menu.addAction(qta.icon('fa5s.edit'), "Edit Title")
        delete_action = menu.addAction(qta.icon('fa5s.trash'), "Delete Photo")
        
        action = menu.exec(self.mapToGlobal(position))
        
        if action == view_action:
            self.view_full_size()
        elif action == edit_action:
            self.edit_title()
        elif action == delete_action:
            self.delete_photo()
    
    def view_full_size(self):
        """Open full-size image in system default viewer."""
        try:
            os.startfile(self.image_path)  # Windows
        except AttributeError:
            os.system(f'xdg-open "{self.image_path}"')  # Linux
    
    def edit_title(self):
        """Edit photo title."""
        from PySide6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(
            self, "Edit Photo Title", "Enter new title:", text=self.title
        )
        if ok and new_title != self.title:
            self.title = new_title
            self.load_thumbnail()  # Reload with new title
    
    def delete_photo(self):
        """Delete photo with confirmation."""
        reply = QMessageBox.question(
            self, "Delete Photo", 
            f"Are you sure you want to delete this photo?\n{os.path.basename(self.image_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.image_path)
                self.photo_deleted.emit(self.image_path)
                self.hide()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete photo: {str(e)}")


class PhotoUploadWidget(QWidget):
    """Drag-and-drop photo upload area."""
    
    photos_uploaded = Signal(list)  # Emits list of uploaded file paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            PhotoUploadWidget {
                border: 3px dashed #2E86AB;
                border-radius: 10px;
                background-color: #f0f8ff;
            }
            PhotoUploadWidget:hover {
                background-color: #e6f3ff;
                border-color: #1a5490;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize upload area UI."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Upload icon
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.cloud-upload-alt', color='#2E86AB').pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Main text
        main_text = QLabel("Drag & Drop Photos Here")
        main_text.setAlignment(Qt.AlignCenter)
        main_text.setFont(QFont("Arial", 14, QFont.Bold))
        main_text.setStyleSheet("color: #2E86AB; margin: 10px;")
        layout.addWidget(main_text)
        
        # Subtitle
        subtitle = QLabel("or click to browse files")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Browse button
        self.browse_btn = QPushButton(qta.icon('fa5s.folder-open'), "Browse Files")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a5490;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_files)
        layout.addWidget(self.browse_btn)
        
        # Supported formats
        formats_text = QLabel("Supported: JPG, PNG, TIFF, BMP")
        formats_text.setAlignment(Qt.AlignCenter)
        formats_text.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(formats_text)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if any URLs are image files
            for url in event.mimeData().urls():
                if self.is_image_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop event."""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self.is_image_file(file_path):
                files.append(file_path)
        
        if files:
            self.process_uploaded_files(files)
        event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        """Handle click to browse files."""
        if event.button() == Qt.LeftButton:
            self.browse_files()
    
    def browse_files(self):
        """Open file browser for photo selection."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Property Photos",
            "",
            "Image Files (*.jpg *.jpeg *.png *.tiff *.bmp);;All Files (*)"
        )
        
        if files:
            self.process_uploaded_files(files)
    
    def is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format."""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    def process_uploaded_files(self, files: List[str]):
        """Process and emit uploaded files."""
        valid_files = [f for f in files if self.is_image_file(f)]
        if valid_files:
            self.photos_uploaded.emit(valid_files)


class PhotoManagerWidget(QWidget):
    """Complete photo management system for property CMAs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.photos_dir = Path("cma_photos")
        self.photos_dir.mkdir(exist_ok=True)
        self.photo_widgets = []
        
        self.init_ui()
        self.setup_signals()
    
    def init_ui(self):
        """Initialize the photo manager UI."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Property Photos")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        self.btn_add_photos = QPushButton(qta.icon('fa5s.plus'), "Add Photos")
        self.btn_clear_all = QPushButton(qta.icon('fa5s.trash'), "Clear All")
        
        header_layout.addWidget(self.btn_add_photos)
        header_layout.addWidget(self.btn_clear_all)
        
        layout.addLayout(header_layout)
        
        # Upload area
        self.upload_widget = PhotoUploadWidget()
        layout.addWidget(self.upload_widget)
        
        # Photos grid container
        photos_container = QGroupBox("Uploaded Photos")
        photos_container.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Scrollable area for photos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        self.photos_widget = QWidget()
        self.photos_layout = QGridLayout()
        self.photos_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.photos_widget.setLayout(self.photos_layout)
        
        scroll_area.setWidget(self.photos_widget)
        
        photos_container_layout = QVBoxLayout()
        photos_container_layout.addWidget(scroll_area)
        photos_container.setLayout(photos_container_layout)
        
        layout.addWidget(photos_container)
        
        # Photo count and stats
        self.stats_label = QLabel("0 photos uploaded")
        self.stats_label.setStyleSheet("color: #666; margin-top: 10px;")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
    
    def setup_signals(self):
        """Connect signals and slots."""
        self.upload_widget.photos_uploaded.connect(self.add_photos)
        self.btn_add_photos.clicked.connect(self.upload_widget.browse_files)
        self.btn_clear_all.clicked.connect(self.clear_all_photos)
    
    def add_photos(self, file_paths: List[str]):
        """Add photos to the manager."""
        for file_path in file_paths:
            try:
                # Copy file to photos directory
                filename = Path(file_path).name
                dest_path = self.photos_dir / filename
                
                # Handle duplicate names
                counter = 1
                while dest_path.exists():
                    name_parts = Path(filename).stem, Path(filename).suffix
                    dest_path = self.photos_dir / f"{name_parts[0]}_{counter}{name_parts[1]}"
                    counter += 1
                
                shutil.copy2(file_path, dest_path)
                
                # Create thumbnail widget
                self.add_photo_widget(str(dest_path))
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add photo {filename}: {str(e)}")
        
        self.update_stats()
    
    def add_photo_widget(self, image_path: str, title: str = ""):
        """Add a photo widget to the grid."""
        if not title:
            title = Path(image_path).stem.replace('_', ' ').title()
        
        photo_widget = PhotoThumbnailWidget(image_path, title)
        photo_widget.photo_deleted.connect(self.remove_photo_widget)
        
        # Add to grid layout
        row = len(self.photo_widgets) // 4
        col = len(self.photo_widgets) % 4
        self.photos_layout.addWidget(photo_widget, row, col)
        
        self.photo_widgets.append(photo_widget)
    
    def remove_photo_widget(self, image_path: str):
        """Remove a photo widget when photo is deleted."""
        for widget in self.photo_widgets:
            if widget.image_path == image_path:
                self.photos_layout.removeWidget(widget)
                widget.deleteLater()
                self.photo_widgets.remove(widget)
                break
        
        self.reorganize_grid()
        self.update_stats()
    
    def reorganize_grid(self):
        """Reorganize the photo grid after deletion."""
        # Remove all widgets from layout
        for widget in self.photo_widgets:
            self.photos_layout.removeWidget(widget)
        
        # Re-add in grid formation
        for i, widget in enumerate(self.photo_widgets):
            row = i // 4
            col = i % 4
            self.photos_layout.addWidget(widget, row, col)
    
    def clear_all_photos(self):
        """Clear all photos with confirmation."""
        if not self.photo_widgets:
            return
        
        reply = QMessageBox.question(
            self, "Clear All Photos",
            f"Are you sure you want to remove all {len(self.photo_widgets)} photos?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove all widgets
            for widget in self.photo_widgets:
                try:
                    os.remove(widget.image_path)
                except:
                    pass  # File might already be deleted
                widget.deleteLater()
            
            self.photo_widgets.clear()
            self.update_stats()
    
    def update_stats(self):
        """Update photo count and statistics."""
        count = len(self.photo_widgets)
        if count == 0:
            self.stats_label.setText("No photos uploaded")
        elif count == 1:
            self.stats_label.setText("1 photo uploaded")
        else:
            self.stats_label.setText(f"{count} photos uploaded")
    
    def get_photo_paths(self) -> List[str]:
        """Get list of all photo file paths."""
        return [widget.image_path for widget in self.photo_widgets]
    
    def get_photos_for_report(self) -> List[dict]:
        """Get photo data formatted for report inclusion."""
        return [
            {
                'path': widget.image_path,
                'title': widget.title,
                'filename': Path(widget.image_path).name
            }
            for widget in self.photo_widgets
        ]