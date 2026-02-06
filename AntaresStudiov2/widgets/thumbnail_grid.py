"""
ANTARES 3D Studio - Thumbnail Grid Widget
Görüntü önizleme grid'i

Özellikler:
- Kalite göstergeli thumbnail'lar
- Seçim desteği
- Zoom/preview
"""

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QMenu, QDialog,
    QPushButton, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QImage, QCursor
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ThumbnailData:
    """Thumbnail verisi"""
    path: str
    filename: str
    quality_level: str = "acceptable"  # excellent, good, acceptable, poor, rejected
    quality_score: float = 0.0
    is_selected: bool = False
    metadata: Dict[str, Any] = None


class ThumbnailItem(QFrame):
    """
    Tek bir thumbnail öğesi.
    
    Kalite seviyesine göre renkli çerçeve gösterir.
    """
    
    clicked = pyqtSignal(str)  # path
    double_clicked = pyqtSignal(str)  # path
    
    QUALITY_COLORS = {
        "excellent": "#00ff88",
        "good": "#90EE90",
        "acceptable": "#ffff00",
        "poor": "#ffa500",
        "rejected": "#ff4444"
    }
    
    def __init__(self, data: ThumbnailData, size: int = 120, parent=None):
        super().__init__(parent)
        
        self.data = data
        self.thumb_size = size
        self._selected = False
        
        self._setup_ui()
        self._load_image()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setFixedSize(self.thumb_size + 10, self.thumb_size + 30)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Görüntü label'ı
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.thumb_size, self.thumb_size)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: #1a1a1a;
                border: 2px solid {self.QUALITY_COLORS.get(self.data.quality_level, '#555')};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.image_label)
        
        # Dosya adı
        name_label = QLabel(self.data.filename[:15] + "..." if len(self.data.filename) > 15 else self.data.filename)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 9px; color: #888;")
        layout.addWidget(name_label)
        
        # Kalite skoru badge
        if self.data.quality_score > 0:
            self._add_quality_badge()
    
    def _load_image(self):
        """Görüntüyü yükle"""
        try:
            pixmap = QPixmap(self.data.path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.thumb_size - 4, self.thumb_size - 4,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("🖼️")
        except Exception:
            self.image_label.setText("⚠️")
    
    def _add_quality_badge(self):
        """Kalite skoru badge'i ekle"""
        # Score badge'i image_label üzerine overlay olarak eklenebilir
        # Şimdilik basit tutalım - tooltip olarak göster
        tooltip = f"Kalite Skoru: {self.data.quality_score:.0f}/100\n"
        tooltip += f"Seviye: {self.data.quality_level}"
        self.setToolTip(tooltip)
    
    def set_selected(self, selected: bool):
        """Seçim durumunu ayarla"""
        self._selected = selected
        
        border_color = self.QUALITY_COLORS.get(self.data.quality_level, '#555')
        if selected:
            self.image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: #1a1a1a;
                    border: 3px solid #00d2ff;
                    border-radius: 4px;
                }}
            """)
        else:
            self.image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: #1a1a1a;
                    border: 2px solid {border_color};
                    border-radius: 4px;
                }}
            """)
    
    def mousePressEvent(self, event):
        """Tıklama olayı"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data.path)
    
    def mouseDoubleClickEvent(self, event):
        """Çift tıklama olayı"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.data.path)
    
    def contextMenuEvent(self, event):
        """Sağ tık menüsü"""
        menu = QMenu(self)
        
        action_preview = menu.addAction("👁️ Önizle")
        action_info = menu.addAction("ℹ️ Bilgi")
        menu.addSeparator()
        action_exclude = menu.addAction("❌ Hariç Tut")
        
        action = menu.exec(event.globalPos())
        
        if action == action_preview:
            self.double_clicked.emit(self.data.path)
        elif action == action_info:
            self._show_info_dialog()
    
    def _show_info_dialog(self):
        """Görüntü bilgi diyaloğu"""
        # TODO: Detaylı görüntü bilgisi diyaloğu
        pass


class ThumbnailGrid(QWidget):
    """
    Thumbnail grid widget'ı.
    
    Özellikler:
    - Otomatik grid düzeni
    - Kalite filtresi
    - Çoklu seçim
    - Zoom kontrolü
    
    Kullanım:
        grid = ThumbnailGrid()
        
        # Görüntü ekle
        grid.add_image("/path/to/image.jpg", quality_info)
        
        # Toplu ekleme
        grid.set_images([
            ThumbnailData(path="/path1.jpg", quality_level="good", quality_score=85),
            ThumbnailData(path="/path2.jpg", quality_level="poor", quality_score=45),
        ])
        
        # Seçilen görüntüleri al
        selected = grid.get_selected()
    """
    
    # Sinyaller
    image_selected = pyqtSignal(str)  # path
    image_double_clicked = pyqtSignal(str)  # path
    selection_changed = pyqtSignal(list)  # [paths]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.thumbnails: List[ThumbnailItem] = []
        self.thumbnail_size = 120
        self.multi_select = True
        self.selected_paths: set = set()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Boyut slider'ı
        size_label = QLabel("Boyut:")
        toolbar.addWidget(size_label)
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(80)
        self.size_slider.setMaximum(200)
        self.size_slider.setValue(self.thumbnail_size)
        self.size_slider.setMaximumWidth(100)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        toolbar.addWidget(self.size_slider)
        
        toolbar.addStretch()
        
        # Seçim bilgisi
        self.selection_label = QLabel("0 seçili")
        toolbar.addWidget(self.selection_label)
        
        # Tümünü seç/kaldır
        self.btn_select_all = QPushButton("Tümünü Seç")
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_select_all.setMaximumWidth(100)
        toolbar.addWidget(self.btn_select_all)
        
        main_layout.addLayout(toolbar)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(5)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)
        
        # Stil
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #2c5364;
                background-color: #0f2027;
            }
        """)
    
    def set_images(self, images: List[ThumbnailData]):
        """Görüntüleri ayarla"""
        self.clear()
        
        for data in images:
            self._add_thumbnail(data)
        
        self._reflow_grid()
    
    def add_image(self, path: str, quality_level: str = "acceptable", 
                  quality_score: float = 0.0, metadata: Dict = None):
        """Tek görüntü ekle"""
        data = ThumbnailData(
            path=path,
            filename=Path(path).name,
            quality_level=quality_level,
            quality_score=quality_score,
            metadata=metadata
        )
        self._add_thumbnail(data)
        self._reflow_grid()
    
    def _add_thumbnail(self, data: ThumbnailData):
        """Thumbnail öğesi ekle"""
        item = ThumbnailItem(data, self.thumbnail_size)
        item.clicked.connect(self._on_item_clicked)
        item.double_clicked.connect(self._on_item_double_clicked)
        self.thumbnails.append(item)
    
    def clear(self):
        """Tüm thumbnail'ları temizle"""
        for thumb in self.thumbnails:
            thumb.setParent(None)
            thumb.deleteLater()
        
        self.thumbnails.clear()
        self.selected_paths.clear()
        self._update_selection_label()
    
    def _reflow_grid(self):
        """Grid düzenini yeniden hesapla"""
        # Mevcut widget'ları kaldır
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        if not self.thumbnails:
            return
        
        # Grid genişliğine göre sütun sayısı hesapla
        available_width = self.scroll_area.viewport().width() - 20
        item_width = self.thumbnail_size + 20
        columns = max(1, available_width // item_width)
        
        # Thumbnail'ları yerleştir
        for i, thumb in enumerate(self.thumbnails):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(thumb, row, col)
    
    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde grid'i yeniden düzenle"""
        super().resizeEvent(event)
        self._reflow_grid()
    
    def _on_size_changed(self, value: int):
        """Thumbnail boyutu değişti"""
        self.thumbnail_size = value
        
        # Tüm thumbnail'ları yeniden oluştur
        current_data = [t.data for t in self.thumbnails]
        self.clear()
        
        for data in current_data:
            self._add_thumbnail(data)
        
        self._reflow_grid()
    
    def _on_item_clicked(self, path: str):
        """Thumbnail'a tıklandı"""
        if self.multi_select:
            # Toggle seçim
            if path in self.selected_paths:
                self.selected_paths.remove(path)
            else:
                self.selected_paths.add(path)
        else:
            # Tek seçim
            self.selected_paths = {path}
        
        # UI güncelle
        for thumb in self.thumbnails:
            thumb.set_selected(thumb.data.path in self.selected_paths)
        
        self._update_selection_label()
        self.image_selected.emit(path)
        self.selection_changed.emit(list(self.selected_paths))
    
    def _on_item_double_clicked(self, path: str):
        """Thumbnail'a çift tıklandı"""
        self.image_double_clicked.emit(path)
        self._show_preview(path)
    
    def _show_preview(self, path: str):
        """Görüntü önizleme diyaloğu"""
        dialog = QDialog(self)
        dialog.setWindowTitle(Path(path).name)
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel()
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                800, 600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec()
    
    def _update_selection_label(self):
        """Seçim etiketini güncelle"""
        count = len(self.selected_paths)
        self.selection_label.setText(f"{count} seçili")
    
    def select_all(self):
        """Tümünü seç"""
        if len(self.selected_paths) == len(self.thumbnails):
            # Tümü seçiliyse, seçimi kaldır
            self.selected_paths.clear()
            self.btn_select_all.setText("Tümünü Seç")
        else:
            # Tümünü seç
            self.selected_paths = {t.data.path for t in self.thumbnails}
            self.btn_select_all.setText("Seçimi Kaldır")
        
        for thumb in self.thumbnails:
            thumb.set_selected(thumb.data.path in self.selected_paths)
        
        self._update_selection_label()
        self.selection_changed.emit(list(self.selected_paths))
    
    def get_selected(self) -> List[str]:
        """Seçilen görüntü yollarını al"""
        return list(self.selected_paths)
    
    def get_all_paths(self) -> List[str]:
        """Tüm görüntü yollarını al"""
        return [t.data.path for t in self.thumbnails]
    
    def filter_by_quality(self, min_level: str):
        """Kalite seviyesine göre filtrele"""
        levels = ["rejected", "poor", "acceptable", "good", "excellent"]
        min_index = levels.index(min_level) if min_level in levels else 0
        
        for thumb in self.thumbnails:
            level_index = levels.index(thumb.data.quality_level) if thumb.data.quality_level in levels else 0
            thumb.setVisible(level_index >= min_index)
    
    def show_all(self):
        """Tüm thumbnail'ları göster"""
        for thumb in self.thumbnails:
            thumb.setVisible(True)
    
    def get_quality_summary(self) -> Dict[str, int]:
        """Kalite özeti"""
        summary = {
            "excellent": 0,
            "good": 0,
            "acceptable": 0,
            "poor": 0,
            "rejected": 0
        }
        
        for thumb in self.thumbnails:
            level = thumb.data.quality_level
            if level in summary:
                summary[level] += 1
        
        return summary
