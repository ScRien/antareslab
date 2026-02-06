"""
ANTARES 3D Studio - Embedded 3D Viewer Module
PyVista tabanlı gömülü 3D görüntüleyici

Özellikler:
- PLY, OBJ, STL dosyalarını görüntüleme
- Mouse ile döndürme, zoom, pan
- Ölçüm araçları
- Ekran görüntüsü alma
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QToolBar, QMessageBox, QFileDialog, QSlider,
    QColorDialog, QComboBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

# PyVista ve VTK import kontrolü
PYVISTA_AVAILABLE = False
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    import numpy as np
    PYVISTA_AVAILABLE = True
except ImportError:
    pv = None
    QtInteractor = None
    np = None


@dataclass
class MeshInfo:
    """3D model bilgisi"""
    filename: str
    n_vertices: int
    n_faces: int
    n_cells: int
    bounds: Tuple[float, ...]
    volume: float = 0.0
    surface_area: float = 0.0
    center: Tuple[float, float, float] = (0, 0, 0)


class Embedded3DViewer(QWidget):
    """
    PyVista tabanlı gömülü 3D görüntüleyici.
    
    Özellikler:
    - PLY, OBJ, STL dosyalarını görüntüleme
    - Mouse kontrolü (döndürme, zoom, pan)
    - Wireframe/solid görünüm
    - Arka plan rengi
    - Ölçüm araçları
    
    Kullanım:
        viewer = Embedded3DViewer()
        layout.addWidget(viewer)
        
        # Model yükle
        success = viewer.load_mesh("/path/to/model.ply")
        
        # Point cloud yükle
        viewer.load_point_cloud("/path/to/cloud.ply")
        
        # Ekran görüntüsü
        viewer.save_screenshot("/path/to/screenshot.png")
    """
    
    # Sinyaller
    model_loaded = pyqtSignal(str)  # filepath
    measurement_taken = pyqtSignal(float)  # distance
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.mesh = None
        self.point_cloud = None
        self.mesh_actor = None
        self.mesh_info: Optional[MeshInfo] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # 3D Viewer alanı
        if PYVISTA_AVAILABLE:
            self._setup_pyvista_viewer(layout)
        else:
            self._setup_fallback_viewer(layout)
        
        # Info panel
        self.info_panel = self._create_info_panel()
        layout.addWidget(self.info_panel)
    
    def _create_toolbar(self) -> QFrame:
        """Toolbar oluştur"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #1a2535;
                border-bottom: 1px solid #2c5364;
            }
            QPushButton {
                min-width: 35px;
                max-width: 35px;
                min-height: 30px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Reset camera
        self.btn_reset = QPushButton("🔄")
        self.btn_reset.setToolTip("Kamerayı Sıfırla")
        self.btn_reset.clicked.connect(self.reset_camera)
        layout.addWidget(self.btn_reset)
        
        # Görünüm modları
        self.btn_solid = QPushButton("🔲")
        self.btn_solid.setToolTip("Solid Görünüm")
        self.btn_solid.clicked.connect(lambda: self.set_display_mode("solid"))
        layout.addWidget(self.btn_solid)
        
        self.btn_wireframe = QPushButton("📐")
        self.btn_wireframe.setToolTip("Wireframe Görünüm")
        self.btn_wireframe.clicked.connect(lambda: self.set_display_mode("wireframe"))
        layout.addWidget(self.btn_wireframe)
        
        self.btn_points = QPushButton("⚫")
        self.btn_points.setToolTip("Nokta Görünüm")
        self.btn_points.clicked.connect(lambda: self.set_display_mode("points"))
        layout.addWidget(self.btn_points)
        
        layout.addWidget(self._create_separator())
        
        # Arka plan rengi
        self.btn_bg_color = QPushButton("🎨")
        self.btn_bg_color.setToolTip("Arka Plan Rengi")
        self.btn_bg_color.clicked.connect(self._change_background)
        layout.addWidget(self.btn_bg_color)
        
        # Işık ayarı
        self.btn_light = QPushButton("💡")
        self.btn_light.setToolTip("Işık Ayarları")
        self.btn_light.clicked.connect(self._toggle_lighting)
        layout.addWidget(self.btn_light)
        
        layout.addWidget(self._create_separator())
        
        # Ölçüm
        self.btn_measure = QPushButton("📏")
        self.btn_measure.setToolTip("Mesafe Ölç")
        self.btn_measure.setCheckable(True)
        self.btn_measure.clicked.connect(self._toggle_measurement_mode)
        layout.addWidget(self.btn_measure)
        
        layout.addWidget(self._create_separator())
        
        # Ekran görüntüsü
        self.btn_screenshot = QPushButton("📷")
        self.btn_screenshot.setToolTip("Ekran Görüntüsü")
        self.btn_screenshot.clicked.connect(self._take_screenshot)
        layout.addWidget(self.btn_screenshot)
        
        # Dosya aç
        self.btn_open = QPushButton("📂")
        self.btn_open.setToolTip("Dosya Aç")
        self.btn_open.clicked.connect(self._open_file_dialog)
        layout.addWidget(self.btn_open)
        
        layout.addStretch()
        
        # Zoom slider
        layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(100)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        layout.addWidget(self.zoom_slider)
        
        return toolbar
    
    def _create_separator(self) -> QFrame:
        """Ayırıcı çizgi oluştur"""
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #2c5364;")
        return sep
    
    def _create_info_panel(self) -> QFrame:
        """Bilgi paneli oluştur"""
        panel = QFrame()
        panel.setMaximumHeight(50)
        panel.setStyleSheet("""
            QFrame {
                background-color: #15192b;
                border-top: 1px solid #2c5364;
            }
            QLabel {
                font-size: 11px;
                color: #888;
            }
        """)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl_vertices = QLabel("Verteks: -")
        layout.addWidget(self.lbl_vertices)
        
        self.lbl_faces = QLabel("Yüz: -")
        layout.addWidget(self.lbl_faces)
        
        self.lbl_volume = QLabel("Hacim: -")
        layout.addWidget(self.lbl_volume)
        
        layout.addStretch()
        
        self.lbl_file = QLabel("Dosya: -")
        layout.addWidget(self.lbl_file)
        
        return panel
    
    def _setup_pyvista_viewer(self, layout: QVBoxLayout):
        """PyVista viewer'ı ayarla"""
        # PyVista plotter oluştur
        self.plotter = QtInteractor(self)
        self.plotter.set_background("#0f2027")
        self.plotter.add_axes()
        
        layout.addWidget(self.plotter.interactor, 1)
    
    def _setup_fallback_viewer(self, layout: QVBoxLayout):
        """PyVista yoksa fallback görünüm"""
        self.plotter = None
        
        fallback = QLabel(
            "⚠️ PyVista yüklü değil\n\n"
            "3D görüntüleyici için PyVista gereklidir.\n\n"
            "Kurulum:\n"
            "pip install pyvista pyvistaqt"
        )
        fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback.setStyleSheet("""
            background-color: #15192b;
            color: #ff8800;
            font-size: 14px;
            padding: 40px;
            border: 2px dashed #ff8800;
            border-radius: 10px;
            margin: 20px;
        """)
        
        layout.addWidget(fallback, 1)
    
    # ==================== MODEL YÜKLEME ====================
    
    def load_mesh(self, filepath: str) -> bool:
        """
        3D mesh dosyası yükle.
        
        Desteklenen formatlar: PLY, OBJ, STL
        
        Args:
            filepath: Dosya yolu
            
        Returns:
            Başarılı mı?
        """
        if not PYVISTA_AVAILABLE or self.plotter is None:
            self.error_occurred.emit("PyVista yüklü değil")
            return False
        
        if not os.path.exists(filepath):
            self.error_occurred.emit(f"Dosya bulunamadı: {filepath}")
            return False
        
        try:
            # Mevcut mesh'i temizle
            self.clear()
            
            # Mesh yükle
            self.mesh = pv.read(filepath)
            
            # Mesh bilgilerini al
            self.mesh_info = self._extract_mesh_info(filepath, self.mesh)
            
            # Görüntüle
            self.mesh_actor = self.plotter.add_mesh(
                self.mesh,
                color="white",
                show_edges=False,
                lighting=True,
                smooth_shading=True
            )
            
            # Kamerayı ayarla
            self.plotter.reset_camera()
            
            # Bilgi panelini güncelle
            self._update_info_panel()
            
            self.model_loaded.emit(filepath)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Yükleme hatası: {str(e)}")
            return False
    
    def load_point_cloud(self, filepath: str) -> bool:
        """
        Point cloud dosyası yükle.
        
        Args:
            filepath: PLY dosya yolu
            
        Returns:
            Başarılı mı?
        """
        if not PYVISTA_AVAILABLE or self.plotter is None:
            return False
        
        try:
            self.clear()
            
            self.point_cloud = pv.read(filepath)
            
            # Point cloud olarak görüntüle
            self.plotter.add_points(
                self.point_cloud,
                render_points_as_spheres=True,
                point_size=3,
                color="cyan"
            )
            
            self.plotter.reset_camera()
            
            self.mesh_info = MeshInfo(
                filename=Path(filepath).name,
                n_vertices=self.point_cloud.n_points,
                n_faces=0,
                n_cells=0,
                bounds=self.point_cloud.bounds
            )
            self._update_info_panel()
            
            self.model_loaded.emit(filepath)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Yükleme hatası: {str(e)}")
            return False
    
    def clear(self):
        """Görüntüleyiciyi temizle"""
        if self.plotter:
            self.plotter.clear()
            self.plotter.add_axes()
        
        self.mesh = None
        self.point_cloud = None
        self.mesh_actor = None
        self.mesh_info = None
    
    def _extract_mesh_info(self, filepath: str, mesh) -> MeshInfo:
        """Mesh bilgilerini çıkar"""
        info = MeshInfo(
            filename=Path(filepath).name,
            n_vertices=mesh.n_points,
            n_faces=mesh.n_faces if hasattr(mesh, 'n_faces') else 0,
            n_cells=mesh.n_cells,
            bounds=mesh.bounds,
            center=tuple(mesh.center)
        )
        
        # Hacim ve yüzey alanı hesapla (mesh için)
        try:
            if hasattr(mesh, 'volume'):
                info.volume = mesh.volume
            if hasattr(mesh, 'area'):
                info.surface_area = mesh.area
        except:
            pass
        
        return info
    
    def _update_info_panel(self):
        """Bilgi panelini güncelle"""
        if self.mesh_info:
            self.lbl_vertices.setText(f"Verteks: {self.mesh_info.n_vertices:,}")
            self.lbl_faces.setText(f"Yüz: {self.mesh_info.n_faces:,}")
            
            if self.mesh_info.volume > 0:
                vol_mm3 = self.mesh_info.volume
                self.lbl_volume.setText(f"Hacim: {vol_mm3:.2f}")
            else:
                self.lbl_volume.setText("Hacim: -")
            
            self.lbl_file.setText(f"Dosya: {self.mesh_info.filename}")
        else:
            self.lbl_vertices.setText("Verteks: -")
            self.lbl_faces.setText("Yüz: -")
            self.lbl_volume.setText("Hacim: -")
            self.lbl_file.setText("Dosya: -")
    
    # ==================== GÖRÜNÜM KONTROL ====================
    
    def reset_camera(self):
        """Kamerayı sıfırla"""
        if self.plotter:
            self.plotter.reset_camera()
            self.zoom_slider.setValue(100)
    
    def set_display_mode(self, mode: str):
        """
        Görüntüleme modunu ayarla.
        
        Args:
            mode: "solid", "wireframe", "points"
        """
        if not self.plotter or not self.mesh:
            return
        
        self.plotter.clear()
        self.plotter.add_axes()
        
        if mode == "wireframe":
            self.mesh_actor = self.plotter.add_mesh(
                self.mesh, 
                style="wireframe",
                color="cyan",
                line_width=1
            )
        elif mode == "points":
            self.mesh_actor = self.plotter.add_mesh(
                self.mesh,
                style="points",
                color="cyan",
                point_size=3,
                render_points_as_spheres=True
            )
        else:  # solid
            self.mesh_actor = self.plotter.add_mesh(
                self.mesh,
                color="white",
                show_edges=False,
                lighting=True
            )
    
    def _change_background(self):
        """Arka plan rengini değiştir"""
        if not self.plotter:
            return
        
        color = QColorDialog.getColor()
        if color.isValid():
            self.plotter.set_background(color.name())
    
    def _toggle_lighting(self):
        """Işığı aç/kapat"""
        if not self.plotter:
            return
        
        # TODO: Işık ayarları
        pass
    
    def _on_zoom_changed(self, value: int):
        """Zoom değiştiğinde"""
        if self.plotter:
            factor = value / 100.0
            self.plotter.camera.zoom(factor)
    
    # ==================== ÖLÇÜM ====================
    
    def _toggle_measurement_mode(self, checked: bool):
        """Ölçüm modunu aç/kapat"""
        if not self.plotter:
            return
        
        if checked:
            self.btn_measure.setStyleSheet("background-color: #00d2ff; color: black;")
            # TODO: Ölçüm modu etkinleştir
        else:
            self.btn_measure.setStyleSheet("")
    
    def measure_distance(self, point1: Tuple, point2: Tuple) -> float:
        """
        İki nokta arasındaki mesafeyi ölç.
        
        Args:
            point1: (x, y, z)
            point2: (x, y, z)
            
        Returns:
            Mesafe
        """
        if not PYVISTA_AVAILABLE:
            return 0.0
        
        p1 = np.array(point1)
        p2 = np.array(point2)
        distance = np.linalg.norm(p2 - p1)
        
        self.measurement_taken.emit(distance)
        return distance
    
    def get_volume(self) -> float:
        """Mesh hacmini döndür"""
        if self.mesh_info:
            return self.mesh_info.volume
        return 0.0
    
    def get_surface_area(self) -> float:
        """Mesh yüzey alanını döndür"""
        if self.mesh_info:
            return self.mesh_info.surface_area
        return 0.0
    
    # ==================== EXPORT ====================
    
    def _take_screenshot(self):
        """Ekran görüntüsü al"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Ekran Görüntüsü Kaydet",
            "",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        
        if filepath:
            self.save_screenshot(filepath)
    
    def save_screenshot(self, filepath: str) -> bool:
        """
        Ekran görüntüsü kaydet.
        
        Args:
            filepath: Çıktı dosya yolu
            
        Returns:
            Başarılı mı?
        """
        if not self.plotter:
            return False
        
        try:
            self.plotter.screenshot(filepath)
            return True
        except Exception:
            return False
    
    def _open_file_dialog(self):
        """Dosya aç diyaloğu"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "3D Model Aç",
            "",
            "3D Dosyaları (*.ply *.obj *.stl);;PLY (*.ply);;OBJ (*.obj);;STL (*.stl)"
        )
        
        if filepath:
            ext = Path(filepath).suffix.lower()
            if ext == '.ply' and 'point' in filepath.lower():
                self.load_point_cloud(filepath)
            else:
                self.load_mesh(filepath)
    
    # ==================== KARŞILAŞTIRMA ====================
    
    def load_comparison(self, mesh1_path: str, mesh2_path: str):
        """
        İki mesh'i karşılaştırma için yükle.
        Sol: Orijinal, Sağ: Güncel
        """
        if not PYVISTA_AVAILABLE or not self.plotter:
            return
        
        try:
            self.clear()
            
            mesh1 = pv.read(mesh1_path)
            mesh2 = pv.read(mesh2_path)
            
            # Yan yana görüntüle
            self.plotter.add_mesh(
                mesh1.translate((-mesh1.center[0] - 50, 0, 0)),
                color="gray",
                label="Önceki"
            )
            
            self.plotter.add_mesh(
                mesh2.translate((-mesh2.center[0] + 50, 0, 0)),
                color="cyan",
                label="Güncel"
            )
            
            self.plotter.add_legend()
            self.plotter.reset_camera()
            
        except Exception as e:
            self.error_occurred.emit(f"Karşılaştırma hatası: {str(e)}")


# Kolay kullanım için yardımcı fonksiyon
def is_pyvista_available() -> bool:
    """PyVista kullanılabilir mi?"""
    return PYVISTA_AVAILABLE
