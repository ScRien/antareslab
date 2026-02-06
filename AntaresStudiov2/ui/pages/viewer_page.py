"""
ANTARES 3D Studio - Viewer Page
3D Görüntüleyici sayfası
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect
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


class ViewerPage(BasePage):
    """3D Görüntüleyici sayfası"""
    
    def __init__(self, parent=None):
        self._viewer = None
        self._pyvista_available = False
        super().__init__(parent)
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header
        header = self.create_header("🎨", "3D Görüntüleyici")
        self._main_layout.addLayout(header)
        
        # Check PyVista
        self._check_pyvista()
        
        if self._pyvista_available:
            self._setup_viewer()
        else:
            self._setup_fallback()
    
    def _check_pyvista(self):
        try:
            from widgets import is_pyvista_available
            self._pyvista_available = is_pyvista_available()
        except:
            self._pyvista_available = False
    
    def _setup_viewer(self):
        """PyVista viewer'ı ekle"""
        theme = get_current_theme()
        
        try:
            from widgets import Embedded3DViewer
            self._viewer = Embedded3DViewer()
            self._main_layout.addWidget(self._viewer)
        except Exception as e:
            self._setup_fallback()
    
    def _setup_fallback(self):
        """PyVista yoksa fallback görünüm"""
        theme = get_current_theme()
        
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(frame, blur=24, opacity=0.08, offset=6)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.setContentsMargins(60, 100, 60, 100)
        frame_layout.setSpacing(16)
        
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 56px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(icon)
        
        text = QLabel("PyVista Yüklü Değil")
        text.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {theme.warning};")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(text)
        
        cmd = QLabel("pip install pyvista pyvistaqt")
        cmd.setStyleSheet(f"font-size: 14px; color: {theme.text_muted}; font-family: monospace;")
        cmd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(cmd)
        
        self._main_layout.addWidget(frame)
    
    def load_mesh(self, filepath: str) -> bool:
        """3D model yükle"""
        if self._viewer:
            return self._viewer.load_mesh(filepath)
        return False
    
    def update_theme(self):
        # Viewer has its own theme handling
        pass
