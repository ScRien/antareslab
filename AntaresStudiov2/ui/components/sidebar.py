"""
ANTARES 3D Studio - Sidebar Components
SidebarButton widget'ı
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

from ui.themes import get_current_theme, get_sidebar_button_style


class SidebarButton(QPushButton):
    """Flat design sidebar butonu"""
    
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.label_text = text
        self.setText(f"  {icon}   {text}")
        self.setCheckable(True)
        self.setMinimumHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
    
    def _update_style(self):
        theme = get_current_theme()
        self.setStyleSheet(get_sidebar_button_style(theme))
    
    def update_theme(self):
        """Tema değiştiğinde güncelle"""
        self._update_style()
