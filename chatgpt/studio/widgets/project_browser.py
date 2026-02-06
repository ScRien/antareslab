"""
ANTARES 3D Studio - Project Browser Widget
Proje tarayıcı

Özellikler:
- Proje listesi (card view)
- Filtreleme ve arama
- Proje önizleme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QGridLayout,
    QMenu, QMessageBox, QDialog, QFormLayout, QTextEdit,
    QDateEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QPixmap, QCursor
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Local imports (proje yüklendiğinde kullanılacak)
import sys
import os

# Core modülünü import et
try:
    from core.project_manager import ProjectManager, AntaresProject, ProjectStatus, ArtifactType
except ImportError:
    # Fallback - doğrudan import
    ProjectManager = None
    AntaresProject = None


class ProjectCard(QFrame):
    """
    Proje kartı widget'ı.
    
    Görünüm:
    ┌─────────────────────────────────────────┐
    │ 🏺 Seramik Parçası #001                 │
    │ Efes Antik Kenti • 2024-01-15           │
    │ 📸 24 görüntü • ✅ Tamamlandı           │
    └─────────────────────────────────────────┘
    """
    
    clicked = pyqtSignal(str)  # project_id
    open_requested = pyqtSignal(str)  # project_id
    delete_requested = pyqtSignal(str)  # project_id
    
    ARTIFACT_ICONS = {
        "seramik": "🏺",
        "metal": "⚔️",
        "cam": "🔮",
        "taş": "🪨",
        "kemik": "🦴",
        "ahşap": "🪵",
        "tekstil": "🧵",
        "sikke": "🪙",
        "heykel": "🗿",
        "diğer": "📦"
    }
    
    STATUS_LABELS = {
        "created": ("🆕", "Yeni", "#888"),
        "downloading": ("📥", "İndiriliyor", "#00d2ff"),
        "downloaded": ("📸", "Hazır", "#ffff00"),
        "processing": ("⚙️", "İşleniyor", "#00d2ff"),
        "completed": ("✅", "Tamamlandı", "#00ff88"),
        "error": ("❌", "Hata", "#ff4444")
    }
    
    def __init__(self, project: 'AntaresProject', parent=None):
        super().__init__(parent)
        
        self.project = project
        self.project_id = project.id
        self._selected = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setFixedHeight(90)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Üst satır: İkon + İsim
        top_layout = QHBoxLayout()
        
        # Eser türü ikonu
        icon = self.ARTIFACT_ICONS.get(self.project.artifact_type, "📦")
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        top_layout.addWidget(icon_label)
        
        # Proje adı
        name_label = QLabel(self.project.name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d2ff;")
        top_layout.addWidget(name_label)
        
        top_layout.addStretch()
        
        # Durum badge
        status_info = self.STATUS_LABELS.get(self.project.status, ("❓", "Bilinmiyor", "#888"))
        status_icon, status_text, status_color = status_info
        
        status_label = QLabel(f"{status_icon} {status_text}")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        top_layout.addWidget(status_label)
        
        layout.addLayout(top_layout)
        
        # Orta satır: Konum + Tarih
        mid_layout = QHBoxLayout()
        
        location_text = self.project.excavation_site or "Konum belirtilmedi"
        date_text = self._format_date(self.project.created_at)
        
        info_label = QLabel(f"{location_text} • {date_text}")
        info_label.setStyleSheet("font-size: 11px; color: #888;")
        mid_layout.addWidget(info_label)
        mid_layout.addStretch()
        
        layout.addLayout(mid_layout)
        
        # Alt satır: Görüntü sayısı + Envanter no
        bottom_layout = QHBoxLayout()
        
        image_count = self.project.image_count
        count_label = QLabel(f"📸 {image_count} görüntü")
        count_label.setStyleSheet("font-size: 10px; color: #666;")
        bottom_layout.addWidget(count_label)
        
        if self.project.inventory_number:
            inv_label = QLabel(f"📋 {self.project.inventory_number}")
            inv_label.setStyleSheet("font-size: 10px; color: #666;")
            bottom_layout.addWidget(inv_label)
        
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
        
        # Stil
        self._update_style()
    
    def _format_date(self, date_str: str) -> str:
        """Tarihi formatla"""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d.%m.%Y")
        except:
            return "Tarih yok"
    
    def _update_style(self):
        """Stili güncelle"""
        if self._selected:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #1a3040;
                    border: 2px solid #00d2ff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #15192b;
                    border: 1px solid #2c5364;
                    border-radius: 8px;
                }
                ProjectCard:hover {
                    border: 1px solid #00d2ff;
                    background-color: #1a2535;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Seçim durumunu ayarla"""
        self._selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Tıklama"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_id)
    
    def mouseDoubleClickEvent(self, event):
        """Çift tıklama - projeyi aç"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.project_id)
    
    def contextMenuEvent(self, event):
        """Sağ tık menüsü"""
        menu = QMenu(self)
        
        action_open = menu.addAction("📂 Aç")
        action_info = menu.addAction("ℹ️ Detaylar")
        menu.addSeparator()
        action_export = menu.addAction("📤 Dışa Aktar")
        action_backup = menu.addAction("💾 Yedekle")
        menu.addSeparator()
        action_delete = menu.addAction("🗑️ Sil")
        
        action = menu.exec(event.globalPos())
        
        if action == action_open:
            self.open_requested.emit(self.project_id)
        elif action == action_delete:
            self.delete_requested.emit(self.project_id)


class ProjectBrowser(QWidget):
    """
    Proje tarayıcı widget'ı.
    
    Kullanım:
        browser = ProjectBrowser()
        browser.project_selected.connect(self.on_project_selected)
        browser.project_opened.connect(self.on_project_opened)
        browser.refresh()
    """
    
    # Sinyaller
    project_selected = pyqtSignal(str)  # project_id
    project_opened = pyqtSignal(str)  # project_id
    project_deleted = pyqtSignal(str)  # project_id
    new_project_requested = pyqtSignal()
    
    def __init__(self, project_manager: 'ProjectManager' = None, parent=None):
        super().__init__(parent)
        
        self.project_manager = project_manager
        self.project_cards: List[ProjectCard] = []
        self.selected_project_id: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Proje ara...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setMaximumWidth(250)
        toolbar.addWidget(self.search_input)
        
        # Filtreler
        self.filter_status = QComboBox()
        self.filter_status.addItem("Tüm Durumlar", None)
        self.filter_status.addItem("✅ Tamamlanan", "completed")
        self.filter_status.addItem("⚙️ İşleniyor", "processing")
        self.filter_status.addItem("📸 Hazır", "downloaded")
        self.filter_status.addItem("🆕 Yeni", "created")
        self.filter_status.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_status)
        
        self.filter_type = QComboBox()
        self.filter_type.addItem("Tüm Türler", None)
        self.filter_type.addItem("🏺 Seramik", "seramik")
        self.filter_type.addItem("⚔️ Metal", "metal")
        self.filter_type.addItem("🔮 Cam", "cam")
        self.filter_type.addItem("🪨 Taş", "taş")
        self.filter_type.addItem("🦴 Kemik", "kemik")
        self.filter_type.addItem("📦 Diğer", "diğer")
        self.filter_type.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_type)
        
        toolbar.addStretch()
        
        # Yenile butonu
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip("Listeyi Yenile")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_refresh.setMaximumWidth(40)
        toolbar.addWidget(self.btn_refresh)
        
        # Yeni proje butonu
        self.btn_new = QPushButton("➕ Yeni Proje")
        self.btn_new.clicked.connect(lambda: self.new_project_requested.emit())
        toolbar.addWidget(self.btn_new)
        
        layout.addLayout(toolbar)
        
        # Proje sayısı
        self.count_label = QLabel("0 proje")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.count_label)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)
        
        # Boş durum mesajı
        self.empty_label = QLabel("Henüz proje yok.\nYeni bir proje oluşturun.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
    
    def set_project_manager(self, manager: 'ProjectManager'):
        """Project manager'ı ayarla"""
        self.project_manager = manager
        self.refresh()
    
    def refresh(self):
        """Proje listesini yenile"""
        if self.project_manager is None:
            return
        
        # Mevcut kartları temizle
        for card in self.project_cards:
            card.setParent(None)
            card.deleteLater()
        self.project_cards.clear()
        
        # Filtreleri al
        status_filter = self.filter_status.currentData()
        type_filter = self.filter_type.currentData()
        search_text = self.search_input.text().strip()
        
        # Projeleri yükle
        projects = self.project_manager.list_projects(
            status=status_filter,
            artifact_type=type_filter,
            search=search_text if search_text else None
        )
        
        # Kartları oluştur
        for project in projects:
            card = ProjectCard(project)
            card.clicked.connect(self._on_card_clicked)
            card.open_requested.connect(self._on_card_opened)
            card.delete_requested.connect(self._on_card_delete_requested)
            
            self.project_cards.append(card)
            self.list_layout.addWidget(card)
        
        # Sayıyı güncelle
        self.count_label.setText(f"{len(projects)} proje")
        
        # Boş durum
        self.empty_label.setVisible(len(projects) == 0)
        self.scroll_area.setVisible(len(projects) > 0)
    
    def _on_search(self, text: str):
        """Arama değiştiğinde"""
        self.refresh()
    
    def _on_filter_changed(self):
        """Filtre değiştiğinde"""
        self.refresh()
    
    def _on_card_clicked(self, project_id: str):
        """Kart tıklandı"""
        # Seçimi güncelle
        self.selected_project_id = project_id
        
        for card in self.project_cards:
            card.set_selected(card.project_id == project_id)
        
        self.project_selected.emit(project_id)
    
    def _on_card_opened(self, project_id: str):
        """Kart açıldı"""
        self.project_opened.emit(project_id)
    
    def _on_card_delete_requested(self, project_id: str):
        """Silme istendi"""
        reply = QMessageBox.question(
            self,
            "Proje Sil",
            "Bu projeyi silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.project_manager:
                success = self.project_manager.delete_project(project_id, confirm=True)
                if success:
                    self.refresh()
                    self.project_deleted.emit(project_id)
    
    def get_selected_project(self) -> Optional[str]:
        """Seçili proje ID'sini al"""
        return self.selected_project_id


class NewProjectDialog(QDialog):
    """
    Yeni proje oluşturma diyaloğu.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Yeni Proje Oluştur")
        self.setMinimumWidth(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Proje adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Seramik_Parcasi_001")
        form.addRow("Proje Adı*:", self.name_input)
        
        # Eser türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("🏺 Seramik", "seramik")
        self.type_combo.addItem("⚔️ Metal", "metal")
        self.type_combo.addItem("🔮 Cam", "cam")
        self.type_combo.addItem("🪨 Taş", "taş")
        self.type_combo.addItem("🦴 Kemik", "kemik")
        self.type_combo.addItem("🪵 Ahşap", "ahşap")
        self.type_combo.addItem("🧵 Tekstil", "tekstil")
        self.type_combo.addItem("🪙 Sikke", "sikke")
        self.type_combo.addItem("🗿 Heykel", "heykel")
        self.type_combo.addItem("📦 Diğer", "diğer")
        form.addRow("Eser Türü:", self.type_combo)
        
        # Kazı alanı
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("Örn: Efes Antik Kenti")
        form.addRow("Kazı Alanı:", self.site_input)
        
        # Kazı tarihi
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form.addRow("Kazı Tarihi:", self.date_input)
        
        # Envanter numarası
        self.inventory_input = QLineEdit()
        self.inventory_input.setPlaceholderText("Örn: EFE-2024-001")
        form.addRow("Envanter No:", self.inventory_input)
        
        # Notlar
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Ek notlar...")
        form.addRow("Notlar:", self.notes_input)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_create = QPushButton("Oluştur")
        btn_create.clicked.connect(self._on_create)
        btn_create.setStyleSheet("background-color: #00d2ff; color: black;")
        btn_layout.addWidget(btn_create)
        
        layout.addLayout(btn_layout)
    
    def _on_create(self):
        """Oluştur butonu"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Hata", "Proje adı zorunludur!")
            return
        
        self.accept()
    
    def get_project_data(self) -> dict:
        """Proje verilerini al"""
        return {
            "name": self.name_input.text().strip(),
            "artifact_type": self.type_combo.currentData(),
            "excavation_site": self.site_input.text().strip(),
            "excavation_date": self.date_input.date().toString("yyyy-MM-dd"),
            "inventory_number": self.inventory_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip()
        }
