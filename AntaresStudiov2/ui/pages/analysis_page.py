"""
ANTARES 3D Studio - Analysis Page
Gelişmiş Bozulma Analizi Dashboard
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QTextEdit, QFileDialog,
    QGraphicsDropShadowEffect, QMessageBox, QSplitter,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from .base_page import BasePage
from ui.themes import get_current_theme, is_dark_mode
from ui.components import CircularProgress, QualityBar


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class AnalysisPage(BasePage):
    """
    Gelişmiş Bozulma Analizi Dashboard.
    
    Özellikler:
    - Görsel metrikler (CircularProgress)
    - ICP Kalite çubuğu
    - Side-by-side 3D viewer
    """
    
    def __init__(self, parent=None):
        self._analyzer = None
        self._result = None
        super().__init__(parent)
    
    def _get_analyzer(self):
        """Lazy load analyzer"""
        if self._analyzer is None:
            try:
                from analysis import DeteriorationAnalyzer, is_open3d_available
                if is_open3d_available():
                    self._analyzer = DeteriorationAnalyzer()
            except ImportError:
                pass
        return self._analyzer
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header
        header = self.create_header(
            "📊", "Bozulma Analizi",
            "İki farklı taramayı karşılaştırarak eserdeki değişimleri tespit edin."
        )
        self._main_layout.addLayout(header)
        
        # Model selection panel
        self._create_selection_panel()
        
        # Metrics dashboard (hidden initially)
        self._create_metrics_dashboard()
        
        # Side-by-side viewer
        self._create_sidebyside_viewer()
    
    def _create_selection_panel(self):
        theme = get_current_theme()
        
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(panel, blur=24, opacity=0.08, offset=6)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(32, 28, 32, 28)
        panel_layout.setSpacing(20)
        
        # Baseline row
        base_row = QHBoxLayout()
        base_row.setSpacing(16)
        
        base_lbl = QLabel("📌 Referans Model")
        base_lbl.setStyleSheet(f"color: {theme.text_secondary}; font-weight: 500; min-width: 140px;")
        base_row.addWidget(base_lbl)
        
        self.baseline_input = QLineEdit()
        self.baseline_input.setPlaceholderText("Önceki tarama dosyası (.ply, .obj, .stl)")
        base_row.addWidget(self.baseline_input, 1)
        
        btn_base = QPushButton("📂 Seç")
        btn_base.setStyleSheet(f"""
            QPushButton {{
                background: {theme.bg_input};
                color: {theme.text_secondary};
                padding: 12px 20px;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: {theme.bg_hover}; color: {theme.text_primary}; }}
        """)
        btn_base.clicked.connect(lambda: self._select_model(self.baseline_input))
        base_row.addWidget(btn_base)
        
        panel_layout.addLayout(base_row)
        
        # Current row
        curr_row = QHBoxLayout()
        curr_row.setSpacing(16)
        
        curr_lbl = QLabel("📍 Güncel Model")
        curr_lbl.setStyleSheet(f"color: {theme.text_secondary}; font-weight: 500; min-width: 140px;")
        curr_row.addWidget(curr_lbl)
        
        self.current_input = QLineEdit()
        self.current_input.setPlaceholderText("Yeni tarama dosyası (.ply, .obj, .stl)")
        curr_row.addWidget(self.current_input, 1)
        
        btn_curr = QPushButton("📂 Seç")
        btn_curr.setStyleSheet(f"""
            QPushButton {{
                background: {theme.bg_input};
                color: {theme.text_secondary};
                padding: 12px 20px;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: {theme.bg_hover}; color: {theme.text_primary}; }}
        """)
        btn_curr.clicked.connect(lambda: self._select_model(self.current_input))
        curr_row.addWidget(btn_curr)
        
        panel_layout.addLayout(curr_row)
        
        # Compare button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.btn_compare = QPushButton("🔬 Karşılaştırmayı Başlat")
        self.btn_compare.setFixedWidth(260)
        self.btn_compare.clicked.connect(self._on_compare)
        btn_row.addWidget(self.btn_compare)
        
        panel_layout.addLayout(btn_row)
        
        self._main_layout.addWidget(panel)
    
    def _create_metrics_dashboard(self):
        theme = get_current_theme()
        
        self.metrics_panel = QFrame()
        self.metrics_panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.metrics_panel, blur=24, opacity=0.08, offset=6)
        self.metrics_panel.setVisible(False)  # Hide initially
        
        metrics_layout = QVBoxLayout(self.metrics_panel)
        metrics_layout.setContentsMargins(32, 28, 32, 28)
        metrics_layout.setSpacing(24)
        
        # Title
        title = QLabel("📈 Analiz Sonuçları")
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {theme.text_primary};")
        metrics_layout.addWidget(title)
        
        # Circular progress row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(40)
        progress_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Overall change
        self.overall_progress = CircularProgress(
            value=0,
            max_value=100,
            title="Genel Değişim",
            suffix="%",
            size=120,
            color=theme.primary
        )
        progress_row.addWidget(self.overall_progress)
        
        # Volume change
        self.volume_progress = CircularProgress(
            value=0,
            max_value=100,
            title="Hacim Değişimi",
            suffix="%",
            size=120,
            color="#8b5cf6"
        )
        progress_row.addWidget(self.volume_progress)
        
        # Area change
        self.area_progress = CircularProgress(
            value=0,
            max_value=100,
            title="Yüzey Değişimi",
            suffix="%",
            size=120,
            color="#f97316"
        )
        progress_row.addWidget(self.area_progress)
        
        metrics_layout.addLayout(progress_row)
        
        # ICP Quality bar
        self.icp_bar = QualityBar(value=0, label="ICP Hizalama Kalitesi")
        metrics_layout.addWidget(self.icp_bar)
        
        # Deterioration level badge
        self.level_label = QLabel()
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setStyleSheet(f"font-size: 16px; font-weight: 600; padding: 12px;")
        metrics_layout.addWidget(self.level_label)
        
        # Warnings
        self.warnings_label = QLabel()
        self.warnings_label.setStyleSheet(f"font-size: 13px; color: {theme.warning};")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setVisible(False)
        metrics_layout.addWidget(self.warnings_label)
        
        self._main_layout.addWidget(self.metrics_panel)
    
    def _create_sidebyside_viewer(self):
        theme = get_current_theme()
        
        self.viewer_panel = QFrame()
        self.viewer_panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.viewer_panel, blur=24, opacity=0.08, offset=6)
        self.viewer_panel.setVisible(False)
        self.viewer_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        viewer_layout = QVBoxLayout(self.viewer_panel)
        viewer_layout.setContentsMargins(24, 20, 24, 20)
        viewer_layout.setSpacing(16)
        
        # Title row
        title_row = QHBoxLayout()
        title = QLabel("🔍 Model Karşılaştırması")
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {theme.text_primary};")
        title_row.addWidget(title)
        title_row.addStretch()
        viewer_layout.addLayout(title_row)
        
        # Splitter for side-by-side
        self.viewer_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left viewer placeholder
        left_frame = QFrame()
        left_frame.setStyleSheet(f"background: {theme.bg_input}; border-radius: 12px;")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_label = QLabel("📌 Referans Model")
        left_label.setStyleSheet(f"color: {theme.text_muted}; font-size: 14px;")
        left_layout.addWidget(left_label)
        self.left_viewer_container = left_frame
        self.viewer_splitter.addWidget(left_frame)
        
        # Right viewer placeholder
        right_frame = QFrame()
        right_frame.setStyleSheet(f"background: {theme.bg_input}; border-radius: 12px;")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_label = QLabel("📍 Güncel Model")
        right_label.setStyleSheet(f"color: {theme.text_muted}; font-size: 14px;")
        right_layout.addWidget(right_label)
        self.right_viewer_container = right_frame
        self.viewer_splitter.addWidget(right_frame)
        
        viewer_layout.addWidget(self.viewer_splitter, 1)
        
        self._main_layout.addWidget(self.viewer_panel)
    
    def _select_model(self, line_edit: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Model Seç", "",
            "3D Files (*.ply *.obj *.stl);;All Files (*)"
        )
        if path:
            line_edit.setText(path)
    
    def _on_compare(self):
        """Karşılaştırma başlat"""
        baseline = self.baseline_input.text().strip()
        current = self.current_input.text().strip()
        
        if not baseline or not current:
            self._show_styled_message("Uyarı", "Her iki model dosyasını da seçin!", QMessageBox.Icon.Warning)
            return
        
        analyzer = self._get_analyzer()
        if analyzer is None:
            self._show_styled_message(
                "Uyarı",
                "Open3D yüklü değil!\nKurulum: pip install open3d",
                QMessageBox.Icon.Warning
            )
            return
        
        self.btn_compare.setEnabled(False)
        self.btn_compare.setText("⏳ Analiz ediliyor...")
        
        try:
            result = analyzer.analyze(baseline, current)
            self._result = result
            
            # Show full-screen results dialog
            from .analysis_results_dialog import AnalysisResultsDialog
            dialog = AnalysisResultsDialog(result, self)
            dialog.exec()
            
        except Exception as e:
            self._show_styled_message("Hata", f"Analiz hatası: {str(e)}", QMessageBox.Icon.Critical)
        finally:
            self.btn_compare.setEnabled(True)
            self.btn_compare.setText("🔬 Karşılaştırmayı Başlat")
    
    def _show_styled_message(self, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information):
        """Tema uyumlu mesaj dialogu göster"""
        theme = get_current_theme()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {theme.bg_card};
            }}
            QMessageBox QLabel {{
                color: {theme.text_primary};
                font-size: 14px;
                min-width: 300px;
            }}
            QMessageBox QPushButton {{
                background-color: {theme.primary};
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {theme.primary_hover};
            }}
        """)
        msg_box.exec()
    
    def _display_results(self, result):
        """Sonuçları dashboard'da göster"""
        theme = get_current_theme()
        
        # Update circular progress bars
        self.overall_progress.set_value(abs(result.overall_change_percent))
        
        # Color based on severity
        if result.overall_change_percent > 10:
            self.overall_progress.set_color(theme.error)
        elif result.overall_change_percent > 5:
            self.overall_progress.set_color(theme.warning)
        else:
            self.overall_progress.set_color(theme.success)
        
        self.volume_progress.set_value(abs(result.volume_change_percent))
        self.area_progress.set_value(abs(result.area_change_percent))
        
        # Update ICP quality bar
        self.icp_bar.set_value(result.icp_fitness)
        
        # Update deterioration level
        level_colors = {
            "none": (theme.success, "✅ Değişim Yok"),
            "minimal": ("#90EE90", "📊 Minimal Değişim"),
            "moderate": (theme.warning, "⚠️ Orta Seviye Değişim"),
            "severe": ("#f97316", "🔶 Ciddi Değişim"),
            "critical": (theme.error, "🔴 Kritik Değişim"),
        }
        color, text = level_colors.get(result.deterioration_level, (theme.text_muted, "Bilinmiyor"))
        self.level_label.setText(text)
        self.level_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            padding: 16px 24px;
            background: {color}22;
            color: {color};
            border-radius: 12px;
        """)
        
        # Show warnings
        if result.warnings:
            self.warnings_label.setText("⚠️ " + " | ".join(result.warnings))
            self.warnings_label.setVisible(True)
        else:
            self.warnings_label.setVisible(False)
    
    def _load_comparison_models(self, baseline_path: str, current_path: str):
        """Side-by-side viewer'lara modelleri yükle"""
        try:
            from widgets import Embedded3DViewer
            
            # Clear existing viewers
            for i in reversed(range(self.left_viewer_container.layout().count())):
                self.left_viewer_container.layout().itemAt(i).widget().deleteLater()
            for i in reversed(range(self.right_viewer_container.layout().count())):
                self.right_viewer_container.layout().itemAt(i).widget().deleteLater()
            
            # Create and add viewers
            self.left_viewer = Embedded3DViewer()
            self.left_viewer.load_mesh(baseline_path)
            self.left_viewer_container.layout().addWidget(self.left_viewer)
            
            self.right_viewer = Embedded3DViewer()
            self.right_viewer.load_mesh(current_path)
            self.right_viewer_container.layout().addWidget(self.right_viewer)
            
        except ImportError:
            pass  # PyVista not available
        except Exception:
            pass  # Other errors
    
    def update_theme(self):
        theme = get_current_theme()
        opacity = 0.08 if is_dark_mode() else 0.04
        
        # Update all panels
        for panel in [self.metrics_panel, self.viewer_panel]:
            if panel:
                panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
                add_shadow(panel, blur=24, opacity=opacity, offset=6)
        
        # Update metric widgets
        if hasattr(self, 'overall_progress'):
            self.overall_progress.update_theme()
        if hasattr(self, 'volume_progress'):
            self.volume_progress.update_theme()
        if hasattr(self, 'area_progress'):
            self.area_progress.update_theme()
        if hasattr(self, 'icp_bar'):
            self.icp_bar.update_theme()
