"""
ANTARES 3D Studio - Analysis Results Dialog
Analiz sonuçlarını gösteren full-screen dialog
"""

from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QScrollArea, QWidget,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QFont

from ui.themes import get_current_theme, is_dark_mode

if TYPE_CHECKING:
    from analysis import DeteriorationResult


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class MetricCard(QFrame):
    """Tek bir metrik gösteren kart"""
    
    def __init__(
        self, 
        value: float, 
        label: str, 
        icon_text: str = "DEĞ",
        suffix: str = "%",
        color: str = "#14a3a8",
        parent=None
    ):
        super().__init__(parent)
        self.value = value
        self.label = label
        self.icon_text = icon_text
        self.suffix = suffix
        self.color = color
        self._setup_ui()
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: {theme.bg_elevated};
                border: none;
                border-radius: 16px;
            }}
        """)
        self.setMinimumSize(180, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon badge
        icon_badge = QLabel(self.icon_text)
        icon_badge.setFixedSize(44, 44)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(f"""
            background-color: {self.color}33;
            color: {self.color};
            border-radius: 22px;
            font-size: 12px;
            font-weight: 700;
        """)
        layout.addWidget(icon_badge, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Value
        value_lbl = QLabel(f"{self.value:.1f}{self.suffix}")
        value_lbl.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 800;
            color: {self.color};
        """)
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_lbl)
        
        # Label
        label_lbl = QLabel(self.label)
        label_lbl.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {theme.text_muted};
        """)
        label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_lbl)


class QualityBarWidget(QFrame):
    """ICP Kalite çubuğu widget'ı"""
    
    def __init__(self, value: float, label: str = "ICP Hizalama Kalitesi", parent=None):
        super().__init__(parent)
        self.value = min(max(value, 0.0), 1.0)
        self.label = label
        self._setup_ui()
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QualityBarWidget {{
                background-color: {theme.bg_elevated};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        label_lbl = QLabel(self.label)
        label_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {theme.text_secondary};")
        header.addWidget(label_lbl)
        
        header.addStretch()
        
        # Value with quality text
        quality_text = self._get_quality_text()
        color = self._get_color()
        value_lbl = QLabel(f"{self.value:.2f} - {quality_text}")
        value_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {color};")
        header.addWidget(value_lbl)
        
        layout.addLayout(header)
        
        # Bar
        bar_container = QFrame()
        bar_container.setFixedHeight(12)
        bar_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_input};
                border-radius: 6px;
            }}
        """)
        
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        self.bar_fill = QFrame()
        self.bar_fill.setFixedHeight(12)
        self.bar_fill.setFixedWidth(int(500 * self.value))  # Approximate width
        self.bar_fill.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_color()};
                border-radius: 6px;
            }}
        """)
        bar_layout.addWidget(self.bar_fill)
        bar_layout.addStretch()
        
        layout.addWidget(bar_container)
    
    def _get_quality_text(self) -> str:
        if self.value >= 0.8:
            return "Mükemmel"
        elif self.value >= 0.6:
            return "İyi"
        elif self.value >= 0.4:
            return "Orta"
        elif self.value >= 0.2:
            return "Zayıf"
        else:
            return "Çok Zayıf"
    
    def _get_color(self) -> str:
        if self.value >= 0.7:
            return "#10b981"
        elif self.value >= 0.4:
            return "#f59e0b"
        else:
            return "#ef4444"


class AnalysisResultsDialog(QDialog):
    """Analiz sonuçlarını gösteren full-screen dialog."""
    
    def __init__(self, result: 'DeteriorationResult', parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        self.setWindowTitle("Bozulma Analizi Sonuçları")
        self.setMinimumSize(900, 650)
        self.resize(1000, 750)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.bg_primary};
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(48, 40, 48, 40)
        main_layout.setSpacing(28)
        
        # Header
        self._create_header(main_layout)
        
        # Deterioration Level Banner
        self._create_level_banner(main_layout)
        
        # Metrics Grid
        self._create_metrics_grid(main_layout)
        
        # ICP Quality Bar
        self._create_quality_bar(main_layout)
        
        # Warnings
        if self.result.warnings:
            self._create_warnings(main_layout)
        
        main_layout.addStretch()
        
        # Close button
        self._create_close_button(main_layout)
    
    def _create_header(self, parent_layout):
        theme = get_current_theme()
        
        header = QHBoxLayout()
        
        title = QLabel("Bozulma Analizi Sonuçları")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 800;
            color: {theme.text_primary};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        parent_layout.addLayout(header)
    
    def _create_level_banner(self, parent_layout):
        theme = get_current_theme()
        
        level_config = {
            "none": ("#10b981", "Değişim Tespit Edilmedi", "Eser stabil durumda"),
            "minimal": ("#22c55e", "Minimal Değişim", "İzleme önerilir"),
            "moderate": ("#f59e0b", "Orta Seviye Değişim", "Koruma önlemi alınmalı"),
            "severe": ("#f97316", "Ciddi Değişim", "Acil müdahale gerekli"),
            "critical": ("#ef4444", "Kritik Değişim", "Derhal uzman müdahalesi şart"),
        }
        
        color, title, subtitle = level_config.get(
            self.result.deterioration_level, 
            (theme.text_muted, "Bilinmiyor", "")
        )
        
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: {color}22;
                border: 2px solid {color};
                border-radius: 16px;
            }}
        """)
        banner.setFixedHeight(100)
        
        banner_layout = QVBoxLayout(banner)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.setSpacing(6)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
        """)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(title_lbl)
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"""
            font-size: 14px;
            color: {theme.text_secondary};
        """)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(sub_lbl)
        
        parent_layout.addWidget(banner)
    
    def _create_metrics_grid(self, parent_layout):
        theme = get_current_theme()
        
        # Section title
        section_title = QLabel("Değişim Metrikleri")
        section_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {theme.text_primary};")
        parent_layout.addWidget(section_title)
        
        # Grid
        grid_frame = QFrame()
        grid_layout = QHBoxLayout(grid_frame)
        grid_layout.setSpacing(16)
        
        def get_metric_color(value):
            if value > 10:
                return "#ef4444"
            elif value > 5:
                return "#f59e0b"
            else:
                return "#10b981"
        
        # Overall change
        overall = abs(self.result.overall_change_percent)
        card1 = MetricCard(
            value=overall,
            label="Genel Değişim",
            icon_text="GEN",
            color=get_metric_color(overall)
        )
        add_shadow(card1, blur=12, opacity=0.04)
        grid_layout.addWidget(card1)
        
        # Volume change
        volume = abs(self.result.volume_change_percent)
        card2 = MetricCard(
            value=volume,
            label="Hacim Değişimi",
            icon_text="HCM",
            color=get_metric_color(volume)
        )
        add_shadow(card2, blur=12, opacity=0.04)
        grid_layout.addWidget(card2)
        
        # Area change
        area = abs(self.result.area_change_percent)
        card3 = MetricCard(
            value=area,
            label="Yüzey Değişimi",
            icon_text="YÜZ",
            color=get_metric_color(area)
        )
        add_shadow(card3, blur=12, opacity=0.04)
        grid_layout.addWidget(card3)
        
        # Point count change
        points = abs(self.result.point_count_change_percent) if hasattr(self.result, 'point_count_change_percent') else 0
        card4 = MetricCard(
            value=points,
            label="Nokta Değişimi",
            icon_text="NKT",
            color=get_metric_color(points)
        )
        add_shadow(card4, blur=12, opacity=0.04)
        grid_layout.addWidget(card4)
        
        parent_layout.addWidget(grid_frame)
    
    def _create_quality_bar(self, parent_layout):
        quality_bar = QualityBarWidget(
            value=self.result.icp_fitness,
            label="ICP Hizalama Kalitesi"
        )
        add_shadow(quality_bar, blur=10, opacity=0.03)
        parent_layout.addWidget(quality_bar)
    
    def _create_warnings(self, parent_layout):
        theme = get_current_theme()
        
        warnings_frame = QFrame()
        warnings_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.warning}18;
                border: 1px solid {theme.warning}44;
                border-radius: 10px;
            }}
        """)
        
        warnings_layout = QVBoxLayout(warnings_frame)
        warnings_layout.setContentsMargins(20, 14, 20, 14)
        warnings_layout.setSpacing(6)
        
        title = QLabel("Uyarılar")
        title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {theme.warning};")
        warnings_layout.addWidget(title)
        
        for warning in self.result.warnings:
            warn_lbl = QLabel(f"• {warning}")
            warn_lbl.setStyleSheet(f"font-size: 13px; color: {theme.text_secondary};")
            warn_lbl.setWordWrap(True)
            warnings_layout.addWidget(warn_lbl)
        
        parent_layout.addWidget(warnings_frame)
    
    def _create_close_button(self, parent_layout):
        theme = get_current_theme()
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        close_btn = QPushButton("Tamam")
        close_btn.setFixedWidth(180)
        close_btn.setFixedHeight(48)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.primary};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.primary_hover};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        
        btn_row.addStretch()
        parent_layout.addLayout(btn_row)
