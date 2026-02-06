"""
ANTARES 3D Studio - Wizard Page
Eğitim Sihirbazı - Preflight entegrasyonlu
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QProgressBar, QListWidget,
    QListWidgetItem, QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .base_page import BasePage
from ui.themes import get_current_theme, get_alert_style, is_dark_mode


def add_shadow(widget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


class WizardPage(BasePage):
    """
    Eğitim Sihirbazı sayfası.
    
    PreFlightChecker ile entegre:
    - Adım 1: Bağlantı kontrolü
    - Adım 2: İndirme
    """
    
    new_project_requested = pyqtSignal()
    download_requested = pyqtSignal(str, str)  # ip, output_dir
    
    def __init__(self, parent=None):
        self.esp32_ip = "192.168.4.1"
        self._preflight_checker = None
        super().__init__(parent)
    
    def _get_preflight_checker(self):
        """Lazy load preflight checker"""
        if self._preflight_checker is None:
            try:
                from core import PreFlightChecker
                self._preflight_checker = PreFlightChecker()
            except ImportError:
                pass
        return self._preflight_checker
    
    def _setup_ui(self):
        theme = get_current_theme()
        
        # Header
        header_layout = self.create_header(
            "📚", "Eğitim Sihirbazı",
            "Adım adım 3D model oluşturma rehberi"
        )
        self._main_layout.addLayout(header_layout)
        
        # Warning (project required)
        self._create_warning_card()
        
        # Main panel
        self._create_main_panel()
    
    def _create_warning_card(self):
        theme = get_current_theme()
        
        self.warning_card = QFrame()
        self.warning_card.setStyleSheet(get_alert_style(theme, "warning"))
        
        warn_layout = QHBoxLayout(self.warning_card)
        warn_layout.setContentsMargins(20, 18, 20, 18)
        
        warn_icon = QLabel("💡")
        warn_icon.setStyleSheet("font-size: 18px;")
        warn_layout.addWidget(warn_icon)
        
        warn_text = QLabel("Başlamadan önce bir proje oluşturun veya mevcut bir projeyi seçin.")
        warn_text.setStyleSheet(f"font-size: 14px; color: {theme.warning};")
        warn_layout.addWidget(warn_text, 1)
        
        btn_create = QPushButton("Proje Oluştur")
        btn_create.setStyleSheet(f"""
            QPushButton {{
                background: {theme.warning};
                color: #1a1a1a;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
            }}
        """)
        btn_create.clicked.connect(self.new_project_requested.emit)
        warn_layout.addWidget(btn_create)
        
        self._main_layout.addWidget(self.warning_card)
    
    def _create_main_panel(self):
        theme = get_current_theme()
        
        self.panel = QFrame()
        self.panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.panel, blur=30, opacity=0.1, offset=8)
        
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(36, 36, 36, 36)
        panel_layout.setSpacing(32)
        
        # Step 1: Connection
        self._create_step1(panel_layout)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {theme.divider};")
        panel_layout.addWidget(divider)
        
        # Step 2: Download
        self._create_step2(panel_layout)
        
        panel_layout.addStretch()
        self._main_layout.addWidget(self.panel)
    
    def _create_step1(self, parent_layout: QVBoxLayout):
        theme = get_current_theme()
        
        # Step header
        step_frame = self._create_step_header("1", "ESP32 Kapsüle Bağlanın",
                                               "ANTARES Kapsülün WiFi ağına bağlanın ve IP adresini girin.",
                                               theme.primary)
        parent_layout.addWidget(step_frame)
        
        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(52, 16, 0, 0)
        content_layout.setSpacing(16)
        
        # IP input row
        ip_row = QHBoxLayout()
        ip_row.setSpacing(12)
        
        ip_label = QLabel("IP Adresi")
        ip_label.setStyleSheet(f"color: {theme.text_secondary}; font-weight: 500;")
        ip_row.addWidget(ip_label)
        
        self.ip_input = QLineEdit(self.esp32_ip)
        self.ip_input.setFixedWidth(200)
        ip_row.addWidget(self.ip_input)
        
        self.btn_connect = QPushButton("🔌 Bağlantıyı Test Et")
        self.btn_connect.clicked.connect(self._on_connect_click)
        ip_row.addWidget(self.btn_connect)
        ip_row.addStretch()
        
        content_layout.addLayout(ip_row)
        
        # Preflight results list
        self.preflight_list = QListWidget()
        self.preflight_list.setMaximumHeight(120)
        self.preflight_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.bg_input};
                border: none;
                border-radius: 12px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
            }}
        """)
        content_layout.addWidget(self.preflight_list)
        
        # Status
        self.conn_status = QLabel("Bağlantı bekleniyor...")
        self.conn_status.setStyleSheet(f"color: {theme.text_muted};")
        content_layout.addWidget(self.conn_status)
        
        parent_layout.addWidget(content)
    
    def _create_step2(self, parent_layout: QVBoxLayout):
        theme = get_current_theme()
        
        step_frame = self._create_step_header("2", "Görüntüleri İndirin",
                                               "Kapsüldeki fotoğrafları bilgisayarınıza aktarın.",
                                               "#8b5cf6")
        parent_layout.addWidget(step_frame)
        
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(52, 16, 0, 0)
        content_layout.setSpacing(16)
        
        self.btn_download = QPushButton("📥 İndirmeyi Başlat")
        self.btn_download.setFixedWidth(200)
        self.btn_download.setEnabled(False)  # Preflight geçene kadar disabled
        self.btn_download.clicked.connect(self._on_download_click)
        content_layout.addWidget(self.btn_download)
        
        self.download_progress = QProgressBar()
        content_layout.addWidget(self.download_progress)
        
        self.download_status = QLabel("Hazır")
        self.download_status.setStyleSheet(f"color: {theme.text_muted}; font-size: 13px;")
        content_layout.addWidget(self.download_status)
        
        parent_layout.addWidget(content)
    
    def _create_step_header(self, num: str, title: str, desc: str, color: str) -> QFrame:
        theme = get_current_theme()
        
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        header.setSpacing(16)
        
        # Badge
        badge = QLabel(num)
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            background: {color};
            color: white;
            font-size: 15px;
            font-weight: 700;
            border-radius: 18px;
        """)
        header.addWidget(badge)
        
        # Title & desc
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {theme.text_primary};")
        text_layout.addWidget(title_lbl)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 13px; color: {theme.text_muted};")
        text_layout.addWidget(desc_lbl)
        
        header.addLayout(text_layout, 1)
        layout.addLayout(header)
        
        return frame
    
    def _on_connect_click(self):
        """Bağlantı test butonu tıklandı"""
        theme = get_current_theme()
        self.esp32_ip = self.ip_input.text().strip()
        
        self.preflight_list.clear()
        self.conn_status.setText("⏳ Kontroller yapılıyor...")
        self.conn_status.setStyleSheet(f"color: {theme.warning};")
        
        checker = self._get_preflight_checker()
        if checker is None:
            self.conn_status.setText("❌ PreFlightChecker yüklenemedi")
            self.conn_status.setStyleSheet(f"color: {theme.error};")
            return
        
        # Run preflight
        try:
            report = checker.run_connection_preflight(self.esp32_ip)
            
            # Show results in list
            for check in report.checks:
                item = QListWidgetItem(f"{check.icon}  {check.name}: {check.message}")
                
                if check.status.value == "passed":
                    item.setForeground(QColor(theme.success))
                elif check.status.value == "warning":
                    item.setForeground(QColor(theme.warning))
                else:
                    item.setForeground(QColor(theme.error))
                
                self.preflight_list.addItem(item)
                
                if check.suggestion:
                    hint = QListWidgetItem(f"    💡 {check.suggestion}")
                    hint.setForeground(QColor(theme.text_muted))
                    self.preflight_list.addItem(hint)
            
            # Update status and button
            if report.can_proceed:
                self.conn_status.setText("✅ Tüm kontroller başarılı!")
                self.conn_status.setStyleSheet(f"color: {theme.success};")
                self.btn_download.setEnabled(True)
            else:
                self.conn_status.setText(f"❌ {report.summary}")
                self.conn_status.setStyleSheet(f"color: {theme.error};")
                self.btn_download.setEnabled(False)
                
        except Exception as e:
            self.conn_status.setText(f"❌ Hata: {str(e)}")
            self.conn_status.setStyleSheet(f"color: {theme.error};")
            self.btn_download.setEnabled(False)
    
    def _on_download_click(self):
        """İndirme butonu tıklandı"""
        if not self._project:
            self._show_styled_warning("Uyarı", "Önce bir proje seçin!")
            return
        
        output_dir = str(self._project.get_images_path())
        self.download_requested.emit(self.esp32_ip, output_dir)
        self.btn_download.setEnabled(False)
    
    def _show_styled_warning(self, title: str, message: str):
        """Tema uyumlu uyarı dialogu göster"""
        theme = get_current_theme()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
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
    
    def set_download_progress(self, value: int):
        """Download progress güncelle"""
        self.download_progress.setValue(value)
    
    def set_download_status(self, text: str, success: bool = False):
        """Download status güncelle"""
        theme = get_current_theme()
        color = theme.success if success else theme.text_muted
        self.download_status.setText(text)
        self.download_status.setStyleSheet(f"color: {color}; font-size: 13px;")
    
    def on_download_complete(self):
        """İndirme tamamlandığında"""
        theme = get_current_theme()
        self.download_status.setText("✅ Tamamlandı!")
        self.download_status.setStyleSheet(f"color: {theme.success}; font-size: 13px;")
        self.btn_download.setEnabled(True)
    
    def on_project_changed(self):
        """Proje değiştiğinde warning'i güncelle"""
        has_project = self._project is not None
        self.warning_card.setVisible(not has_project)
    
    def update_theme(self):
        theme = get_current_theme()
        
        self.warning_card.setStyleSheet(get_alert_style(theme, "warning"))
        self.panel.setStyleSheet(f"background-color: {theme.bg_card}; border: none; border-radius: 20px;")
        add_shadow(self.panel, blur=30, opacity=0.1 if is_dark_mode() else 0.05, offset=8)
        
        self.preflight_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.bg_input};
                border: none;
                border-radius: 12px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
            }}
        """)
