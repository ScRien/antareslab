"""
ANTARES 3D Studio - Card Components
ModernCard ve ProjectCard widget'ları
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.themes import get_current_theme, is_dark_mode


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    """Widget'a gölge ekle"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class ModernCard(QFrame):
    """Border-free, shadow-based modern kart"""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon: str, title: str, desc: str, accent: str = "#14a3a8", parent=None):
        super().__init__(parent)
        self.accent = accent
        self._setup_ui(icon, title, desc)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_ui(self, icon: str, title: str, desc: str):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: {theme.bg_card};
                border: none;
                border-radius: 20px;
            }}
            ModernCard:hover {{
                background-color: {theme.bg_elevated};
            }}
        """)
        
        add_shadow(self, blur=24, opacity=0.12 if is_dark_mode() else 0.06, offset=6)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Accent indicator
        accent_line = QFrame()
        accent_line.setFixedSize(40, 4)
        accent_line.setStyleSheet(f"background: {self.accent}; border-radius: 2px;")
        layout.addWidget(accent_line)
        
        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 36px;")
        layout.addWidget(icon_lbl)
        
        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {theme.text_primary};")
        layout.addWidget(self.title_lbl)
        
        # Description
        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setStyleSheet(f"font-size: 13px; color: {theme.text_muted}; line-height: 1.4;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_theme(self):
        """Tema değiştiğinde güncelle"""
        theme = get_current_theme()
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: {theme.bg_card};
                border: none;
                border-radius: 20px;
            }}
            ModernCard:hover {{
                background-color: {theme.bg_elevated};
            }}
        """)
        self.title_lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {theme.text_primary};")
        self.desc_lbl.setStyleSheet(f"font-size: 13px; color: {theme.text_muted}; line-height: 1.4;")
        add_shadow(self, blur=24, opacity=0.12 if is_dark_mode() else 0.06, offset=6)


class ProjectCard(QFrame):
    """
    Zengin proje bilgisi gösteren kart.
    
    Gösterir:
    - Proje adı
    - Status badge (created/completed/error)
    - Poligon sayısı (model_vertices)
    - Deterioration level (varsa)
    - Sensör verileri (sıcaklık/nem)
    """
    
    clicked = pyqtSignal(str)  # project_id
    
    STATUS_COLORS = {
        "created": ("#6b7280", "Oluşturuldu"),
        "downloading": ("#3b82f6", "İndiriliyor"),
        "downloaded": ("#8b5cf6", "İndirildi"),
        "processing": ("#f59e0b", "İşleniyor"),
        "completed": ("#10b981", "Tamamlandı"),
        "error": ("#ef4444", "Hata"),
    }
    
    DETERIORATION_ICONS = {
        "none": ("✅", "#10b981"),
        "minimal": ("📊", "#6b7280"),
        "moderate": ("⚠️", "#f59e0b"),
        "severe": ("🔶", "#f97316"),
        "critical": ("🔴", "#ef4444"),
    }
    
    def __init__(self, project, parent=None):
        """
        Args:
            project: AntaresProject instance
        """
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            ProjectCard {{
                background-color: {theme.bg_card};
                border: none;
                border-radius: 16px;
            }}
            ProjectCard:hover {{
                background-color: {theme.bg_elevated};
            }}
        """)
        
        add_shadow(self, blur=20, opacity=0.1 if is_dark_mode() else 0.05, offset=4)
        
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Sol: İkon ve temel bilgi
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        # Header row (isim + badge)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        
        icon = QLabel("📁")
        icon.setStyleSheet("font-size: 28px;")
        header_row.addWidget(icon)
        
        name = QLabel(self.project.name)
        name.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {theme.text_primary};")
        header_row.addWidget(name)
        
        # Status badge
        status_color, status_text = self.STATUS_COLORS.get(
            self.project.status, ("#6b7280", "Bilinmiyor")
        )
        badge = QLabel(status_text)
        badge.setStyleSheet(f"""
            background: {status_color}22;
            color: {status_color};
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_row.addWidget(badge)
        header_row.addStretch()
        
        left_layout.addLayout(header_row)
        
        # Alt bilgiler
        info_row = QHBoxLayout()
        info_row.setSpacing(20)
        
        # Görüntü sayısı
        if self.project.image_count > 0:
            img_info = QLabel(f"🖼️ {self.project.image_count} görüntü")
            img_info.setStyleSheet(f"font-size: 12px; color: {theme.text_muted};")
            info_row.addWidget(img_info)
        
        # Poligon sayısı
        if self.project.model_vertices > 0:
            vertices = self.project.model_vertices
            if vertices >= 1000000:
                v_text = f"{vertices/1000000:.1f}M"
            elif vertices >= 1000:
                v_text = f"{vertices/1000:.1f}K"
            else:
                v_text = str(vertices)
            poly_info = QLabel(f"🔺 {v_text} poligon")
            poly_info.setStyleSheet(f"font-size: 12px; color: {theme.text_muted};")
            info_row.addWidget(poly_info)
        
        # Eser türü
        type_info = QLabel(f"📋 {self.project.artifact_type}")
        type_info.setStyleSheet(f"font-size: 12px; color: {theme.text_muted};")
        info_row.addWidget(type_info)
        
        info_row.addStretch()
        left_layout.addLayout(info_row)
        
        layout.addLayout(left_layout, 1)
        
        # Sağ: Sensör verileri (varsa)
        if self.project.capsule_temperature > 0 or self.project.capsule_humidity > 0:
            right_layout = QVBoxLayout()
            right_layout.setSpacing(4)
            right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            if self.project.capsule_temperature > 0:
                temp = QLabel(f"🌡️ {self.project.capsule_temperature:.1f}°C")
                temp.setStyleSheet(f"font-size: 12px; color: {theme.text_secondary};")
                right_layout.addWidget(temp)
            
            if self.project.capsule_humidity > 0:
                hum = QLabel(f"💧 {self.project.capsule_humidity:.0f}%")
                hum.setStyleSheet(f"font-size: 12px; color: {theme.text_secondary};")
                right_layout.addWidget(hum)
            
            layout.addLayout(right_layout)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.project.id)
        super().mousePressEvent(event)
    
    def update_theme(self):
        """Tema değiştiğinde yeniden oluştur"""
        # Clear and rebuild
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        
        self._setup_ui()
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
