"""
ANTARES 3D Studio - Projects Page
Projelerim sayfası - ProjectCard ile zengin görünüm
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QWidget,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .base_page import BasePage
from ui.themes import get_current_theme, is_dark_mode
from ui.components import ProjectCard


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class ProjectsPage(BasePage):
    """
    Projelerim sayfası.
    
    ProjectCard widget'ları ile zengin proje bilgisi gösterir.
    """
    
    new_project_requested = pyqtSignal()
    project_selected = pyqtSignal(str)  # project_id
    refresh_requested = pyqtSignal()
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header row
        header_row = QHBoxLayout()
        
        header = QLabel("📁 Projelerim")
        header.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {theme.text_primary};")
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        btn_refresh = QPushButton("🔄 Yenile")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.text_secondary};
                border: none;
                padding: 12px 20px;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: {theme.bg_hover}; color: {theme.text_primary}; }}
        """)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        header_row.addWidget(btn_refresh)
        
        btn_new = QPushButton("➕ Yeni Proje")
        btn_new.clicked.connect(self.new_project_requested.emit)
        header_row.addWidget(btn_new)
        
        self._main_layout.addLayout(header_row)
        
        # Projects scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setContentsMargins(0, 0, 16, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        self._main_layout.addWidget(self.scroll_area)
        
        # Cards list
        self.project_cards: List[ProjectCard] = []
        
        # Empty state
        self._create_empty_state()
    
    def _create_empty_state(self):
        theme = get_current_theme()
        
        self.empty_frame = QFrame()
        self.empty_frame.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.empty_frame, blur=24, opacity=0.08, offset=6)
        
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(60, 80, 60, 80)
        empty_layout.setSpacing(16)
        
        icon = QLabel("📭")
        icon.setStyleSheet("font-size: 56px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon)
        
        text = QLabel("Henüz proje yok")
        text.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {theme.text_primary};")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(text)
        
        desc = QLabel("İlk projenizi oluşturmak için butona tıklayın.")
        desc.setStyleSheet(f"font-size: 14px; color: {theme.text_muted};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(desc)
        
        btn = QPushButton("➕ Yeni Proje Oluştur")
        btn.clicked.connect(self.new_project_requested.emit)
        empty_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.empty_frame)
    
    def set_projects(self, projects: list):
        """Proje listesini güncelle"""
        theme = get_current_theme()
        
        # Clear existing cards
        for card in self.project_cards:
            card.deleteLater()
        self.project_cards.clear()
        
        if not projects:
            self.empty_frame.setVisible(True)
            return
        
        self.empty_frame.setVisible(False)
        
        # Create cards for each project
        for project in projects:
            card = ProjectCard(project)
            card.clicked.connect(self._on_card_clicked)
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)
            self.project_cards.append(card)
    
    def _on_card_clicked(self, project_id: str):
        self.project_selected.emit(project_id)
    
    def update_theme(self):
        theme = get_current_theme()
        
        self.empty_frame.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.empty_frame, blur=24, opacity=0.08 if is_dark_mode() else 0.04, offset=6)
        
        for card in self.project_cards:
            card.update_theme()
