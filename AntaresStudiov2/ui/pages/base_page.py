"""
ANTARES 3D Studio - Base Page
Tüm sayfalar için temel sınıf
"""

from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal

from ui.themes import get_current_theme

if TYPE_CHECKING:
    from core import AntaresProject


class BasePage(QWidget):
    """
    Tüm sayfalar için temel sınıf.
    
    Her sayfa bu sınıftan türetilmeli ve şu metodları implement etmelidir:
    - _setup_ui(): UI elemanlarını oluştur
    - update_theme(): Tema değiştiğinde güncelle
    """
    
    # Sinyaller
    navigate_to = pyqtSignal(int)       # Başka sayfaya git
    project_changed = pyqtSignal()       # Proje değişti
    status_message = pyqtSignal(str)     # Status bar mesajı
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Optional['AntaresProject'] = None
        self._setup_base_layout()
        self._setup_ui()
    
    def _setup_base_layout(self):
        """Temel layout"""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(24)
    
    @property
    def project(self) -> Optional['AntaresProject']:
        """Aktif proje"""
        return self._project
    
    @project.setter
    def project(self, value: Optional['AntaresProject']):
        """Proje ayarla ve UI'ı güncelle"""
        self._project = value
        self.on_project_changed()
    
    def _setup_ui(self):
        """UI elemanlarını oluştur - subclass'lar override etmeli"""
        pass
    
    def update_theme(self):
        """Tema değiştiğinde UI'ı güncelle - subclass'lar override etmeli"""
        pass
    
    def on_project_changed(self):
        """Proje değiştiğinde çağrılır - override edilebilir"""
        pass
    
    def create_header(self, icon: str, title: str, description: str = "") -> QVBoxLayout:
        """Standart sayfa başlığı oluştur"""
        theme = get_current_theme()
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Title
        title_lbl = QLabel(f"{icon} {title}")
        title_lbl.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {theme.text_primary};")
        title_lbl.setObjectName("page_title")
        layout.addWidget(title_lbl)
        
        # Description
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(f"font-size: 15px; color: {theme.text_muted};")
            desc_lbl.setObjectName("page_description")
            layout.addWidget(desc_lbl)
        
        return layout
