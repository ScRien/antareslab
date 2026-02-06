"""
ANTARES KAPSÜL 3D STUDIO v2.0
Refactored - Modular Page Architecture
Flat Design - Border-free, Shadow-based UI

Tasarım Prensipleri:
- Kenarlık yerine gölge ve negatif alan
- WCAG AA uyumlu kontrast
- İnce, modern progress bar
- Ferah ve içerik odaklı
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QFileDialog,
    QGraphicsDropShadowEffect, QFrame, QStatusBar, QMenuBar, QMenu,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from ui.themes import (
    ThemeMode, DARK_THEME, LIGHT_THEME,
    get_stylesheet, get_sidebar_style, get_sidebar_button_style,
    get_current_theme, set_theme, is_dark_mode
)
from ui.components import SidebarButton
from ui.pages import (
    HomePage, WizardPage, ImagesPage, ViewerPage, AnalysisPage, ProjectsPage
)


# ==============================================================================
# AYARLAR
# ==============================================================================

APP_NAME = "ANTARES KAPSÜL 3D STUDIO"
APP_VERSION = "2.0.0"
DEFAULT_ESP32_IP = "192.168.4.1"

HOME_DIR = Path.home()
PROJECTS_DIR = HOME_DIR / "ANTARES_Projects"
BACKUPS_DIR = HOME_DIR / "ANTARES_Backups"
CONFIG_FILE = Path(__file__).parent / "config.json"


# ==============================================================================
# LAZY LOADERS
# ==============================================================================

_project_manager = None
_backup_manager = None


def get_project_manager():
    global _project_manager
    if _project_manager is None:
        from core import ProjectManager
        _project_manager = ProjectManager(PROJECTS_DIR)
    return _project_manager


def get_backup_manager():
    global _backup_manager
    if _backup_manager is None:
        from core import BackupManager
        _backup_manager = BackupManager(BACKUPS_DIR)
    return _backup_manager


# ==============================================================================
# UI HELPERS
# ==============================================================================

def add_shadow(widget: QWidget, blur: int = 20, opacity: float = 0.15, offset: int = 4):
    """Widget'a gölge ekle"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(shadow)


# ==============================================================================
# ANA UYGULAMA
# ==============================================================================

class AntaresStudioApp(QMainWindow):
    """ANTARES 3D Studio - Modular Page Architecture"""
    
    theme_changed = pyqtSignal()
    project_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.current_project = None
        self.esp32_ip = DEFAULT_ESP32_IP
        
        # Thread references
        self.download_thread = None
        self.analysis_thread = None
        self.reconstruction_thread = None
        
        self._setup_ui()
        self._setup_menubar()
        self._setup_statusbar()
        self._connect_signals()
        self._apply_theme()
        self._load_config()
        self._refresh_data()
    
    def _apply_theme(self):
        """Temayı uygula"""
        theme = get_current_theme()
        self.setStyleSheet(get_stylesheet(theme))
        
        if hasattr(self, 'sidebar'):
            self.sidebar.setStyleSheet(get_sidebar_style(theme))
        
        if hasattr(self, 'sidebar_buttons'):
            for btn in self.sidebar_buttons:
                btn.update_theme()
        
        # Tema buton metnini güncelle
        if hasattr(self, 'theme_btn'):
            if is_dark_mode():
                self.theme_btn.setText("☀️  Açık Tema")
            else:
                self.theme_btn.setText("🌙  Koyu Tema")
        
        # Sayfa temalarını güncelle
        for page in self.pages.values():
            page.update_theme()
    
    def toggle_theme(self):
        """Tema değiştir"""
        if is_dark_mode():
            set_theme(ThemeMode.LIGHT)
        else:
            set_theme(ThemeMode.DARK)
        
        self._apply_theme()
        self._save_config()
        self.theme_changed.emit()
    
    def _setup_ui(self):
        """Ana UI"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1320, 850)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==================== SIDEBAR ====================
        self._setup_sidebar(main_layout)
        
        # ==================== ANA İÇERİK ====================
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(24)
        
        self.stack = QStackedWidget()
        
        # Sayfa sınıflarını oluştur
        self.pages = {
            'home': HomePage(),
            'wizard': WizardPage(),
            'images': ImagesPage(),
            'viewer': ViewerPage(),
            'analysis': AnalysisPage(),
            'projects': ProjectsPage(),
        }
        
        # Stack'e ekle
        for name, page in self.pages.items():
            self.stack.addWidget(page)
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content, 1)
    
    def _setup_sidebar(self, main_layout):
        """Sidebar oluştur"""
        theme = get_current_theme()
        
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(100)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(28, 28, 28, 12)
        
        logo = QLabel("🏛️ ANTARES")
        logo.setStyleSheet("font-size: 24px; font-weight: 700; color: #14a3a8;")
        logo_layout.addWidget(logo)
        
        tagline = QLabel("3D Dijital İkiz Stüdyosu")
        tagline.setStyleSheet("font-size: 12px; color: #6b7280;")
        logo_layout.addWidget(tagline)
        
        sidebar_layout.addWidget(logo_frame)
        
        # Menü butonları
        self.sidebar_buttons: List[SidebarButton] = []
        menu_items = [
            ("🏠", "Ana Sayfa", 0),
            ("📚", "Eğitim Sihirbazı", 1),
            ("🖼️", "Görüntüler", 2),
            ("🎨", "3D Görüntüleyici", 3),
            ("📊", "Bozulma Analizi", 4),
            ("📁", "Projelerim", 5),
        ]
        
        for icon, text, idx in menu_items:
            btn = SidebarButton(icon, text)
            btn.clicked.connect(lambda checked, i=idx: self._on_sidebar_click(i))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
        
        self.sidebar_buttons[0].setChecked(True)
        
        sidebar_layout.addStretch()
        
        # Tema butonu
        theme_frame = QFrame()
        theme_layout = QVBoxLayout(theme_frame)
        theme_layout.setContentsMargins(16, 12, 16, 12)
        
        self.theme_btn = QPushButton("☀️  Açık Tema")
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6b7280;
                border: none;
                padding: 14px 20px;
                border-radius: 10px;
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover { background: rgba(255,255,255,0.04); color: #a0a0a0; }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_btn)
        
        sidebar_layout.addWidget(theme_frame)
        
        # Proje bilgisi
        project_frame = QFrame()
        project_frame.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.05);")
        project_layout = QVBoxLayout(project_frame)
        project_layout.setContentsMargins(20, 20, 20, 20)
        project_layout.setSpacing(12)
        
        project_header = QLabel("AKTİF PROJE")
        project_header.setStyleSheet("font-size: 10px; font-weight: 600; color: #6b7280; letter-spacing: 1px;")
        project_layout.addWidget(project_header)
        
        self.project_label = QLabel("Seçilmedi")
        self.project_label.setStyleSheet("font-size: 14px; color: #a0a0a0;")
        self.project_label.setWordWrap(True)
        project_layout.addWidget(self.project_label)
        
        btn_new = QPushButton("➕  Yeni Proje")
        btn_new.clicked.connect(self._on_new_project)
        project_layout.addWidget(btn_new)
        
        sidebar_layout.addWidget(project_frame)
        main_layout.addWidget(self.sidebar)
    
    def _connect_signals(self):
        """Sayfa sinyallerini bağla"""
        # Home page
        self.pages['home'].navigate_to.connect(self._on_sidebar_click)
        self.pages['home'].new_project_requested.connect(self._on_new_project)
        self.pages['home'].project_selected.connect(self._on_project_selected)
        
        # Wizard page
        self.pages['wizard'].new_project_requested.connect(self._on_new_project)
        self.pages['wizard'].download_requested.connect(self._on_download_start)
        
        # Projects page
        self.pages['projects'].new_project_requested.connect(self._on_new_project)
        self.pages['projects'].project_selected.connect(self._on_project_selected)
        self.pages['projects'].refresh_requested.connect(self._refresh_projects)
    
    def _on_sidebar_click(self, index: int):
        """Sidebar butonu tıklandığında"""
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)
    
    def _on_new_project(self):
        """Yeni proje oluştur"""
        name, ok = QInputDialog.getText(
            self, "Yeni Proje", "Proje adını girin:",
            text="Yeni Proje"
        )
        
        if ok and name:
            try:
                pm = get_project_manager()
                project = pm.create_project(name)
                self.current_project = project
                self.project_label.setText(project.name)
                
                # Sayfalara projeyi bildir
                for page in self.pages.values():
                    page.project = project
                
                self._refresh_data()
                self.statusBar().showMessage(f"Proje oluşturuldu: {name}", 3000)
                self.project_changed.emit()
                
            except Exception as e:
                self._show_warning("Hata", f"Proje oluşturulamadı: {e}")
    
    def _on_project_selected(self, project_id: str):
        """Proje seçildi"""
        try:
            pm = get_project_manager()
            project = pm.load_project(project_id)
            
            if project:
                self.current_project = project
                self.project_label.setText(project.name)
                
                # Sayfalara projeyi bildir
                for page in self.pages.values():
                    page.project = project
                
                self.statusBar().showMessage(f"Proje yüklendi: {project.name}", 3000)
                self.project_changed.emit()
                
        except Exception as e:
            self._show_warning("Hata", f"Proje yüklenemedi: {e}")
    
    def _on_download_start(self, ip: str, output_dir: str):
        """İndirme başlat"""
        # TODO: DownloadThread entegrasyonu
        self.statusBar().showMessage(f"İndirme başlatılıyor: {ip} -> {output_dir}")
    
    def _refresh_data(self):
        """Verileri yenile"""
        self._refresh_projects()
        self._refresh_recent_projects()
    
    def _refresh_projects(self):
        """Proje listesini yenile"""
        try:
            pm = get_project_manager()
            projects = pm.list_projects()
            self.pages['projects'].set_projects(projects)
        except Exception:
            pass
    
    def _refresh_recent_projects(self):
        """Son projeleri yenile"""
        try:
            pm = get_project_manager()
            projects = pm.list_projects(sort_by='modified', limit=5)
            self.pages['home'].set_recent_projects(projects)
        except Exception:
            pass
    
    def _setup_menubar(self):
        """Menü çubuğu"""
        menubar = self.menuBar()
        
        # Dosya
        file_menu = menubar.addMenu("Dosya")
        
        new_action = QAction("Yeni Proje", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Görünüm
        view_menu = menubar.addMenu("Görünüm")
        
        theme_action = QAction("Tema Değiştir", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Yardım
        help_menu = menubar.addMenu("Yardım")
        
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self):
        """Status bar"""
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Hazır")
    
    def _show_about(self):
        """Hakkında dialog"""
        QMessageBox.about(
            self,
            "Hakkında",
            f"{APP_NAME}\nVersiyon: {APP_VERSION}\n\n"
            "Arkeolojik eserlerin 3D dijital ikizlerini oluşturmak için\n"
            "geliştirilmiş profesyonel bir stüdyo uygulaması."
        )
    
    def _load_config(self):
        """Ayarları yükle"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    
                if config.get('theme') == 'light':
                    set_theme(ThemeMode.LIGHT)
                    self._apply_theme()
        except Exception:
            pass
    
    def _save_config(self):
        """Ayarları kaydet"""
        try:
            config = {
                'theme': 'light' if not is_dark_mode() else 'dark'
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass
    
    def _show_warning(self, title: str, message: str):
        """Tema uyumlu uyarı dialogu göster"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        self._style_message_box(msg_box)
        msg_box.exec()
    
    def _show_info(self, title: str, message: str):
        """Tema uyumlu bilgi dialogu göster"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        self._style_message_box(msg_box)
        msg_box.exec()
    
    def _style_message_box(self, msg_box: QMessageBox):
        """QMessageBox'a tema stili uygula"""
        theme = get_current_theme()
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


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = AntaresStudioApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
