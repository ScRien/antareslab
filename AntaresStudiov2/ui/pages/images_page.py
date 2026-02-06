"""
ANTARES 3D Studio - Images Page
Görüntüler sayfası
"""

from typing import List
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from .base_page import BasePage
from ui.themes import get_current_theme, is_dark_mode


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class ImagesPage(BasePage):
    """Görüntüler sayfası - İndirilen fotoğrafları gösterir"""
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header
        header = self.create_header("🖼️", "Görüntüler")
        self._main_layout.addLayout(header)
        
        # Empty state
        self.empty_frame = QFrame()
        self.empty_frame.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.empty_frame, blur=24, opacity=0.08, offset=6)
        
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(60, 100, 60, 100)
        empty_layout.setSpacing(16)
        
        icon = QLabel("📷")
        icon.setStyleSheet("font-size: 56px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon)
        
        text = QLabel("Henüz görüntü yok")
        text.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {theme.text_primary};")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(text)
        
        desc = QLabel("Eğitim Sihirbazı'ndan görüntüleri indirdikten sonra\nburada görüntülenecek.")
        desc.setStyleSheet(f"font-size: 14px; color: {theme.text_muted};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(desc)
        
        self._main_layout.addWidget(self.empty_frame)
    
    def set_images(self, image_paths: List[str]):
        """Görüntüleri ayarla (gelecekte grid view olacak)"""
        # TODO: Implement image grid view
        pass
    
    def update_theme(self):
        theme = get_current_theme()
        self.empty_frame.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.empty_frame, blur=24, opacity=0.08 if is_dark_mode() else 0.04, offset=6)
