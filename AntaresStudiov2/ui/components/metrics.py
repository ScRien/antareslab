"""
ANTARES 3D Studio - Metric Components
CircularProgress, SensorGauge, QualityBar widget'ları
"""

import math
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush

from ui.themes import get_current_theme, is_dark_mode


class CircularProgress(QFrame):
    """
    Dairesel progress bar widget'ı.
    
    Analiz sonuçlarını görsel olarak göstermek için kullanılır.
    Örn: overall_change_percent, volume_change_percent
    """
    
    def __init__(
        self, 
        value: float = 0.0,
        max_value: float = 100.0,
        title: str = "",
        suffix: str = "%",
        size: int = 120,
        color: str = "#14a3a8",
        parent=None
    ):
        super().__init__(parent)
        self._value = value
        self.max_value = max_value
        self.title = title
        self.suffix = suffix
        self.size = size
        self.color = color
        
        self.setFixedSize(size + 40, size + 60)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none;")
        self._setup_labels()
    
    @property
    def value(self):
        return self._value
    
    def _setup_labels(self):
        """Create overlay labels for value and title"""
        theme = get_current_theme()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Spacer for top
        layout.addSpacing(self.size // 2 - 15)
        
        # Value label
        self.value_label = QLabel(f"{self._value:.1f}{self.suffix}")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {theme.text_primary};
            background: transparent;
        """)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
        
        # Title label
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 500;
                color: {theme.text_muted};
                background: transparent;
            """)
            layout.addWidget(self.title_label)
        
        layout.addSpacing(8)
    
    def set_value(self, value: float):
        """Değeri güncelle"""
        self._value = min(value, self.max_value)
        self.value_label.setText(f"{self._value:.1f}{self.suffix}")
        self.update()
    
    def set_color(self, color: str):
        """Rengi güncelle"""
        self.color = color
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        theme = get_current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center calculations
        center_x = self.width() // 2
        center_y = self.size // 2 + 5
        radius = self.size // 2 - 12
        
        # Background circle
        bg_pen = QPen(QColor(theme.divider))
        bg_pen.setWidth(12)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        
        rect = QRectF(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2
        )
        painter.drawArc(rect, 0, 360 * 16)
        
        # Progress arc
        if self.max_value > 0:
            progress = self._value / self.max_value
        else:
            progress = 0
        
        progress_pen = QPen(QColor(self.color))
        progress_pen.setWidth(12)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        
        # Start from top (90 degrees), go clockwise
        start_angle = 90 * 16
        span_angle = -int(progress * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)
        
        painter.end()
    
    def update_theme(self):
        """Tema değiştiğinde güncelle"""
        theme = get_current_theme()
        self.value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {theme.text_primary};
            background: transparent;
        """)
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 500;
                color: {theme.text_muted};
                background: transparent;
            """)
        self.update()


class SensorGauge(QFrame):
    """
    Sensör değeri göstergesi.
    
    Sıcaklık ve nem değerlerini görselleştirmek için.
    """
    
    def __init__(
        self,
        value: float = 0.0,
        unit: str = "°C",
        label: str = "Sıcaklık",
        icon: str = "🌡️",
        min_value: float = 0.0,
        max_value: float = 50.0,
        warning_threshold: float = 35.0,
        parent=None
    ):
        super().__init__(parent)
        self.value = value
        self.unit = unit
        self.label = label
        self.icon = icon
        self.min_value = min_value
        self.max_value = max_value
        self.warning_threshold = warning_threshold
        
        self._setup_ui()
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            SensorGauge {{
                background-color: {theme.bg_card};
                border: none;
                border-radius: 16px;
            }}
        """)
        
        self.setFixedSize(140, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon + Label
        header = QHBoxLayout()
        header.setSpacing(6)
        
        icon_lbl = QLabel(self.icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_lbl)
        
        label_lbl = QLabel(self.label)
        label_lbl.setStyleSheet(f"font-size: 12px; color: {theme.text_muted};")
        header.addWidget(label_lbl)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_lbl = QLabel(f"{self.value:.1f}{self.unit}")
        color = theme.warning if self.value > self.warning_threshold else theme.text_primary
        self.value_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {color};")
        layout.addWidget(self.value_lbl)
    
    def set_value(self, value: float):
        """Değeri güncelle"""
        self.value = value
        theme = get_current_theme()
        color = theme.warning if self.value > self.warning_threshold else theme.text_primary
        self.value_lbl.setText(f"{self.value:.1f}{self.unit}")
        self.value_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {color};")


class QualityBar(QFrame):
    """
    Kalite göstergesi çubuğu.
    
    ICP fitness değerini görselleştirmek için.
    0.0 = Kötü (Kırmızı), 1.0 = Mükemmel (Yeşil)
    """
    
    def __init__(
        self,
        value: float = 0.0,
        label: str = "ICP Kalitesi",
        parent=None
    ):
        super().__init__(parent)
        self._value = min(max(value, 0.0), 1.0)
        self.label = label
        
        self._setup_ui()
    
    @property
    def value(self):
        return self._value
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QualityBar {{
                background-color: {theme.bg_elevated};
                border: none;
                border-radius: 12px;
            }}
        """)
        
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)
        
        # Header row
        header = QHBoxLayout()
        
        self.label_lbl = QLabel(self.label)
        self.label_lbl.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {theme.text_secondary};")
        header.addWidget(self.label_lbl)
        
        header.addStretch()
        
        self.value_lbl = QLabel(f"{self._value:.2f}")
        self.value_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {theme.text_primary};")
        header.addWidget(self.value_lbl)
        
        layout.addLayout(header)
        
        # Bar container
        self.bar_container = QFrame()
        self.bar_container.setFixedHeight(12)
        self.bar_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_input};
                border-radius: 6px;
            }}
        """)
        
        # Use a single layout for the bar
        bar_layout = QHBoxLayout(self.bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        self.bar_fill = QFrame()
        self.bar_fill.setFixedHeight(12)
        bar_layout.addWidget(self.bar_fill)
        bar_layout.addStretch(1)
        
        layout.addWidget(self.bar_container)
        
        self._update_bar_color()
    
    def _get_color_for_value(self, value: float) -> str:
        """0-1 arası değer için renk hesapla"""
        if value < 0.33:
            return "#ef4444"  # Red
        elif value < 0.66:
            return "#f59e0b"  # Yellow/Orange
        else:
            return "#10b981"  # Green
    
    def _update_bar_color(self):
        """Çubuk rengini güncelle"""
        color = self._get_color_for_value(self._value)
        self.bar_fill.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update bar width based on container width
        container_width = self.bar_container.width()
        if container_width > 0:
            bar_width = int(container_width * self._value)
            self.bar_fill.setFixedWidth(max(bar_width, 6))
    
    def showEvent(self, event):
        super().showEvent(event)
        # Delay width calculation to after widget is shown
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._delayed_resize)
    
    def _delayed_resize(self):
        """Widget gösterildikten sonra boyut hesapla"""
        container_width = self.bar_container.width()
        if container_width > 0:
            bar_width = int(container_width * self._value)
            self.bar_fill.setFixedWidth(max(bar_width, 6))
    
    def set_value(self, value: float):
        """Değeri güncelle"""
        self._value = min(max(value, 0.0), 1.0)
        self.value_lbl.setText(f"{self._value:.2f}")
        self._update_bar_color()
        self._delayed_resize()
    
    def update_theme(self):
        """Tema değiştiğinde güncelle"""
        theme = get_current_theme()
        self.setStyleSheet(f"""
            QualityBar {{
                background-color: {theme.bg_elevated};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.label_lbl.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {theme.text_secondary};")
        self.value_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {theme.text_primary};")
        self.bar_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_input};
                border-radius: 6px;
            }}
        """)
        self._update_bar_color()
