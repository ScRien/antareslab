"""
ANTARES 3D Studio - Home Page
Ana sayfa
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .base_page import BasePage
from ui.themes import get_current_theme, is_dark_mode
from ui.components import ModernCard


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class HomePage(BasePage):
    """Ana sayfa - Hoş geldiniz ve hızlı erişim kartları"""
    
    new_project_requested = pyqtSignal()
    project_selected = pyqtSignal(str)  # project_id
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header
        self.header = QLabel("Hoş Geldiniz 👋")
        self.header.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {theme.text_primary};")
        self._main_layout.addWidget(self.header)
        
        self.sub = QLabel("ANTARES Kapsül ile arkeolojik eserlerin 3D dijital ikizlerini oluşturun.")
        self.sub.setStyleSheet(f"font-size: 16px; color: {theme.text_muted}; margin-bottom: 8px;")
        self._main_layout.addWidget(self.sub)
        
        # Onboarding card
        self._create_onboarding_card()
        
        # Quick access cards
        self._create_quick_access_cards()
        
        # Recent projects
        self._create_recent_projects()
        
        self._main_layout.addStretch()
    
    def _create_onboarding_card(self):
        theme = get_current_theme()
        
        self.onboarding = QFrame()
        self.onboarding.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme.primary_subtle}, stop:1 transparent);
                border: none;
                border-left: 4px solid {theme.primary};
                border-radius: 16px;
            }}
        """)
        add_shadow(self.onboarding, blur=30, opacity=0.1, offset=8)
        
        onboard_layout = QHBoxLayout(self.onboarding)
        onboard_layout.setContentsMargins(32, 32, 32, 32)
        onboard_layout.setSpacing(24)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet(f"background: {theme.primary}; border-radius: 20px;")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel("🚀")
        icon.setStyleSheet("font-size: 36px;")
        icon_layout.addWidget(icon)
        onboard_layout.addWidget(icon_container)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title = QLabel("Başlamaya Hazır mısınız?")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {theme.text_primary};")
        text_layout.addWidget(title)
        
        desc = QLabel("İlk adım olarak bir proje oluşturun, ardından Eğitim Sihirbazı ile 3D model oluşturmaya başlayın.")
        desc.setStyleSheet(f"font-size: 14px; color: {theme.text_secondary}; line-height: 1.5;")
        text_layout.addWidget(desc)
        
        onboard_layout.addLayout(text_layout, 1)
        
        # Button
        btn_start = QPushButton("Başla →")
        btn_start.setFixedWidth(140)
        btn_start.clicked.connect(self.new_project_requested.emit)
        onboard_layout.addWidget(btn_start)
        
        self._main_layout.addWidget(self.onboarding)
    
    def _create_quick_access_cards(self):
        theme = get_current_theme()
        
        section_label = QLabel("Hızlı Erişim")
        section_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {theme.text_muted}; margin-top: 8px;")
        self._main_layout.addWidget(section_label)
        
        self.cards_container = QFrame()
        cards_layout = QHBoxLayout(self.cards_container)
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cards: List[ModernCard] = []
        cards_data = [
            ("📚", "Eğitim Sihirbazı", "Adım adım rehber ile\n3D model oluşturun", 1, "#14a3a8"),
            ("🖼️", "Görüntüler", "Çekilen fotoğrafları\ninceleyin ve düzenleyin", 2, "#8b5cf6"),
            ("🎨", "3D Görüntüleyici", "Modelleri 3 boyutlu\nolarak görüntüleyin", 3, "#f97316"),
            ("📊", "Bozulma Analizi", "Zaman içindeki\ndeğişimleri analiz edin", 4, "#10b981"),
        ]
        
        for icon, title, desc, page_idx, accent in cards_data:
            card = ModernCard(icon, title, desc, accent)
            card.clicked.connect(lambda idx=page_idx: self.navigate_to.emit(idx))
            cards_layout.addWidget(card)
            self.cards.append(card)
        
        self._main_layout.addWidget(self.cards_container)
    
    def _create_recent_projects(self):
        theme = get_current_theme()
        
        section_label = QLabel("Son Projeler")
        section_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {theme.text_muted};")
        self._main_layout.addWidget(section_label)
        
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(180)
        add_shadow(self.recent_list, blur=20, opacity=0.08, offset=4)
        self.recent_list.itemDoubleClicked.connect(self._on_project_select)
        self._main_layout.addWidget(self.recent_list)
    
    def _on_project_select(self, item: QListWidgetItem):
        project_id = item.data(Qt.ItemDataRole.UserRole)
        if project_id:
            self.project_selected.emit(project_id)
    
    def set_recent_projects(self, projects: list):
        """Son projeleri güncelle"""
        theme = get_current_theme()
        self.recent_list.clear()
        
        if not projects:
            item = QListWidgetItem("📭  Henüz proje yok")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.recent_list.addItem(item)
        else:
            for p in projects[:5]:
                item = QListWidgetItem(f"📁  {p.name}")
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.recent_list.addItem(item)
    
    def set_onboarding_visible(self, visible: bool):
        """Onboarding kartını göster/gizle"""
        self.onboarding.setVisible(visible)
    
    def update_theme(self):
        theme = get_current_theme()
        
        self.header.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {theme.text_primary};")
        self.sub.setStyleSheet(f"font-size: 16px; color: {theme.text_muted}; margin-bottom: 8px;")
        
        self.onboarding.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme.primary_subtle}, stop:1 transparent);
                border: none;
                border-left: 4px solid {theme.primary};
                border-radius: 16px;
            }}
        """)
        add_shadow(self.onboarding, blur=30, opacity=0.1 if is_dark_mode() else 0.05, offset=8)
        
        for card in self.cards:
            card.update_theme()
