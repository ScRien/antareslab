"""
ANTARES 3D Studio - Deterioration Analyzer Module
Bozulma/değişim analizi

Özellikler:
- İki 3D model karşılaştırması
- ICP hizalama
- Referans nesne ile ölçeklendirme
- Değişim haritası oluşturma
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# 3D kütüphaneleri
OPEN3D_AVAILABLE = False
try:
    import open3d as o3d
    import numpy as np
    OPEN3D_AVAILABLE = True
except ImportError:
    o3d = None
    np = None


class DeteriorationLevel(Enum):
    """Bozulma seviyesi"""
    NONE = "none"           # Değişim yok
    MINIMAL = "minimal"     # Minimal değişim
    MODERATE = "moderate"   # Orta seviye
    SEVERE = "severe"       # Ciddi bozulma
    CRITICAL = "critical"   # Kritik


@dataclass
class ReferenceObject:
    """
    Referans nesne bilgisi (ölçeklendirme için).
    
    Arkeolojik taramada sabit boyutlu bir referans nesne
    (örn: 1 cm küp) kullanılarak otomatik ölçeklendirme yapılır.
    """
    expected_size_mm: float = 10.0  # Beklenen boyut (mm)
    detected_size_mm: float = 0.0   # Tespit edilen boyut
    scale_factor: float = 1.0       # Hesaplanan ölçek faktörü
    detected: bool = False          # Tespit edildi mi?
    position: Tuple[float, float, float] = (0, 0, 0)  # Tespit edilen konum


@dataclass
class DeteriorationResult:
    """Bozulma analizi sonucu"""
    
    # Temel bilgiler
    baseline_path: str              # Referans model
    current_path: str               # Güncel model
    analysis_date: str = ""
    
    # Genel sonuç
    deterioration_level: str = "none"
    overall_change_percent: float = 0.0
    
    # Metrikler
    mean_distance: float = 0.0      # Ortalama mesafe (mm)
    max_distance: float = 0.0       # Maksimum mesafe
    rmse: float = 0.0               # Root Mean Square Error
    hausdorff_distance: float = 0.0 # Hausdorff mesafesi
    
    # Hacim karşılaştırması
    baseline_volume: float = 0.0
    current_volume: float = 0.0
    volume_change_percent: float = 0.0
    
    # Yüzey alanı karşılaştırması
    baseline_area: float = 0.0
    current_area: float = 0.0
    area_change_percent: float = 0.0
    
    # Bölgesel analiz
    high_change_regions: List[Tuple[float, float, float]] = field(default_factory=list)
    
    # Referans nesne bilgisi
    reference_used: bool = False
    scale_factor: float = 1.0
    
    # ICP hizalama bilgisi
    icp_fitness: float = 0.0        # Hizalama kalitesi (0-1)
    icp_rmse: float = 0.0
    
    # Uyarılar
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON serileştirme için dict"""
        return {
            'baseline_path': self.baseline_path,
            'current_path': self.current_path,
            'analysis_date': self.analysis_date,
            'deterioration_level': self.deterioration_level,
            'overall_change_percent': self.overall_change_percent,
            'mean_distance': self.mean_distance,
            'max_distance': self.max_distance,
            'rmse': self.rmse,
            'hausdorff_distance': self.hausdorff_distance,
            'baseline_volume': self.baseline_volume,
            'current_volume': self.current_volume,
            'volume_change_percent': self.volume_change_percent,
            'baseline_area': self.baseline_area,
            'current_area': self.current_area,
            'area_change_percent': self.area_change_percent,
            'reference_used': self.reference_used,
            'scale_factor': self.scale_factor,
            'icp_fitness': self.icp_fitness,
            'icp_rmse': self.icp_rmse,
            'warnings': self.warnings
        }
    
    def to_html(self) -> str:
        """HTML formatında rapor"""
        level_colors = {
            "none": "#00ff88",
            "minimal": "#90EE90",
            "moderate": "#ffff00",
            "severe": "#ffa500",
            "critical": "#ff4444"
        }
        
        level_labels = {
            "none": "Değişim Yok",
            "minimal": "Minimal",
            "moderate": "Orta",
            "severe": "Ciddi",
            "critical": "Kritik"
        }
        
        color = level_colors.get(self.deterioration_level, "#888")
        label = level_labels.get(self.deterioration_level, "Bilinmiyor")
        
        html = f"""
        <h3>📊 Bozulma Analizi Raporu</h3>
        <p><b>Tarih:</b> {self.analysis_date}</p>
        
        <h4 style='color:{color};'>Değerlendirme: {label}</h4>
        <p>Genel Değişim: <b>{self.overall_change_percent:.2f}%</b></p>
        
        <table style='width:100%; border-collapse: collapse;'>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>Ortalama Mesafe</td>
                <td style='padding:8px;'><b>{self.mean_distance:.4f} mm</b></td>
            </tr>
            <tr>
                <td style='padding:8px;'>Maksimum Mesafe</td>
                <td style='padding:8px;'>{self.max_distance:.4f} mm</td>
            </tr>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>RMSE</td>
                <td style='padding:8px;'>{self.rmse:.4f}</td>
            </tr>
            <tr>
                <td style='padding:8px;'>Hausdorff Mesafesi</td>
                <td style='padding:8px;'>{self.hausdorff_distance:.4f} mm</td>
            </tr>
        </table>
        
        <h4>📐 Hacim Karşılaştırması</h4>
        <ul>
            <li>Referans: {self.baseline_volume:.2f} mm³</li>
            <li>Güncel: {self.current_volume:.2f} mm³</li>
            <li>Değişim: <b style='color:{color};'>{self.volume_change_percent:+.2f}%</b></li>
        </ul>
        
        <h4>📏 Yüzey Alanı Karşılaştırması</h4>
        <ul>
            <li>Referans: {self.baseline_area:.2f} mm²</li>
            <li>Güncel: {self.current_area:.2f} mm²</li>
            <li>Değişim: <b style='color:{color};'>{self.area_change_percent:+.2f}%</b></li>
        </ul>
        
        <h4>🔧 ICP Hizalama Kalitesi</h4>
        <p>Fitness: {self.icp_fitness:.4f} (1.0 = mükemmel)</p>
        """
        
        if self.reference_used:
            html += f"""
            <h4>📏 Referans Nesne</h4>
            <p>Ölçek Faktörü: {self.scale_factor:.6f}</p>
            """
        
        if self.warnings:
            html += "<h4>⚠️ Uyarılar</h4><ul>"
            for w in self.warnings:
                html += f"<li>{w}</li>"
            html += "</ul>"
        
        return html


class DeteriorationAnalyzer:
    """
    3D model bozulma/değişim analizi.
    
    İki 3D model arasındaki değişimleri tespit eder.
    Arkeolojik eserlerin zaman içindeki değişimini takip etmek için kullanılır.
    
    Özellikler:
    - ICP tabanlı otomatik hizalama
    - Referans nesne ile ölçeklendirme
    - Hacim ve yüzey alanı karşılaştırması
    - Değişim haritası oluşturma
    
    Kullanım:
        analyzer = DeteriorationAnalyzer()
        
        # Basit karşılaştırma
        result = analyzer.analyze(
            baseline_path="model_2023.ply",
            current_path="model_2024.ply"
        )
        print(f"Bozulma: {result.deterioration_level}")
        
        # Referans nesne ile (daha doğru)
        result = analyzer.analyze_with_reference(
            baseline_path="model_2023.ply",
            current_path="model_2024.ply",
            reference_size_mm=10.0  # 1 cm küp
        )
    """
    
    # Bozulma eşik değerleri (mm)
    THRESHOLD_MINIMAL = 0.1    # < 0.1 mm
    THRESHOLD_MODERATE = 0.5   # < 0.5 mm
    THRESHOLD_SEVERE = 2.0     # < 2.0 mm
    # > 2.0 mm = CRITICAL
    
    def __init__(self):
        if not OPEN3D_AVAILABLE:
            raise ImportError(
                "Open3D yüklü değil. Kurulum: pip install open3d"
            )
    
    def analyze(
        self,
        baseline_path: str,
        current_path: str,
        icp_threshold: float = 0.02,
        progress_callback=None
    ) -> DeteriorationResult:
        """
        İki model arasındaki değişimi analiz et.
        
        Args:
            baseline_path: Referans/eski model yolu
            current_path: Güncel model yolu
            icp_threshold: ICP eşik değeri
            progress_callback: İlerleme callback (step, total)
            
        Returns:
            DeteriorationResult
        """
        result = DeteriorationResult(
            baseline_path=baseline_path,
            current_path=current_path,
            analysis_date=datetime.now().isoformat()
        )
        
        # 1. Modelleri yükle
        if progress_callback:
            progress_callback(1, 6)
        
        baseline, current = self._load_meshes(baseline_path, current_path)
        
        if baseline is None or current is None:
            result.warnings.append("Model yüklenemedi")
            return result
        
        # 2. Point cloud'a çevir
        if progress_callback:
            progress_callback(2, 6)
        
        baseline_pc = baseline.sample_points_uniformly(number_of_points=50000)
        current_pc = current.sample_points_uniformly(number_of_points=50000)
        
        # 3. ICP hizalama
        if progress_callback:
            progress_callback(3, 6)
        
        transform, icp_result = self._icp_alignment(
            baseline_pc, current_pc, threshold=icp_threshold
        )
        
        result.icp_fitness = icp_result.fitness
        result.icp_rmse = icp_result.inlier_rmse
        
        if result.icp_fitness < 0.5:
            result.warnings.append(
                f"Düşük hizalama kalitesi ({result.icp_fitness:.2f}). "
                "Modeller çok farklı olabilir."
            )
        
        # Hizalanmış modeli uygula
        current_pc.transform(transform)
        
        # 4. Mesafe hesaplama
        if progress_callback:
            progress_callback(4, 6)
        
        distances = self._compute_distances(baseline_pc, current_pc)
        
        result.mean_distance = float(np.mean(distances))
        result.max_distance = float(np.max(distances))
        result.rmse = float(np.sqrt(np.mean(distances ** 2)))
        
        # Hausdorff mesafesi
        result.hausdorff_distance = self._compute_hausdorff(baseline_pc, current_pc)
        
        # 5. Hacim ve alan karşılaştırması
        if progress_callback:
            progress_callback(5, 6)
        
        try:
            result.baseline_volume = baseline.get_volume()
            result.current_volume = current.get_volume()
            
            if result.baseline_volume > 0:
                result.volume_change_percent = (
                    (result.current_volume - result.baseline_volume) / 
                    result.baseline_volume * 100
                )
        except:
            result.warnings.append("Hacim hesaplanamadı")
        
        try:
            result.baseline_area = baseline.get_surface_area()
            result.current_area = current.get_surface_area()
            
            if result.baseline_area > 0:
                result.area_change_percent = (
                    (result.current_area - result.baseline_area) / 
                    result.baseline_area * 100
                )
        except:
            result.warnings.append("Yüzey alanı hesaplanamadı")
        
        # 6. Bozulma seviyesi belirleme
        if progress_callback:
            progress_callback(6, 6)
        
        result.deterioration_level = self._determine_level(result)
        result.overall_change_percent = (
            abs(result.volume_change_percent) + 
            abs(result.area_change_percent) + 
            result.mean_distance * 10
        ) / 3
        
        return result
    
    def analyze_with_reference(
        self,
        baseline_path: str,
        current_path: str,
        reference_size_mm: float = 10.0,
        auto_detect_reference: bool = True,
        progress_callback=None
    ) -> DeteriorationResult:
        """
        Referans nesne kullanarak analiz.
        
        Referans nesne (örn: 1 cm küp) kullanılarak modeller
        önce ölçeklendirilir, sonra karşılaştırılır.
        
        Args:
            baseline_path: Referans model
            current_path: Güncel model
            reference_size_mm: Referans nesne boyutu (mm)
            auto_detect_reference: Otomatik tespit
            
        Returns:
            DeteriorationResult
        """
        if not auto_detect_reference:
            # Referans nesne tespiti kapalıysa normal analiz yap
            return self.analyze(baseline_path, current_path, 
                              progress_callback=progress_callback)
        
        # Referans nesne tespit et ve ölçeklendir
        baseline_mesh = o3d.io.read_triangle_mesh(baseline_path)
        current_mesh = o3d.io.read_triangle_mesh(current_path)
        
        # Referans nesne tespiti
        baseline_ref = self._detect_reference_object(baseline_mesh, reference_size_mm)
        current_ref = self._detect_reference_object(current_mesh, reference_size_mm)
        
        result = DeteriorationResult(
            baseline_path=baseline_path,
            current_path=current_path,
            analysis_date=datetime.now().isoformat()
        )
        
        if baseline_ref.detected and current_ref.detected:
            result.reference_used = True
            result.scale_factor = baseline_ref.scale_factor / current_ref.scale_factor
            
            # Modelleri ölçeklendir
            current_mesh.scale(result.scale_factor, center=current_mesh.get_center())
        else:
            result.warnings.append(
                "Referans nesne tespit edilemedi. "
                "Ölçeklendirme yapılmadan analiz edildi."
            )
        
        # Geçici dosyalara kaydet ve analiz et
        temp_baseline = str(Path(baseline_path).parent / "_temp_baseline.ply")
        temp_current = str(Path(current_path).parent / "_temp_current.ply")
        
        try:
            o3d.io.write_triangle_mesh(temp_baseline, baseline_mesh)
            o3d.io.write_triangle_mesh(temp_current, current_mesh)
            
            analysis_result = self.analyze(
                temp_baseline, temp_current,
                progress_callback=progress_callback
            )
            
            # Sonuçları birleştir
            result.deterioration_level = analysis_result.deterioration_level
            result.overall_change_percent = analysis_result.overall_change_percent
            result.mean_distance = analysis_result.mean_distance
            result.max_distance = analysis_result.max_distance
            result.rmse = analysis_result.rmse
            result.hausdorff_distance = analysis_result.hausdorff_distance
            result.baseline_volume = analysis_result.baseline_volume
            result.current_volume = analysis_result.current_volume
            result.volume_change_percent = analysis_result.volume_change_percent
            result.baseline_area = analysis_result.baseline_area
            result.current_area = analysis_result.current_area
            result.area_change_percent = analysis_result.area_change_percent
            result.icp_fitness = analysis_result.icp_fitness
            result.icp_rmse = analysis_result.icp_rmse
            result.warnings.extend(analysis_result.warnings)
            
        finally:
            # Geçici dosyaları temizle
            for temp in [temp_baseline, temp_current]:
                if os.path.exists(temp):
                    os.remove(temp)
        
        return result
    
    # ==================== YÜKLE & HİZALA ====================
    
    def _load_meshes(self, path1: str, path2: str) -> Tuple:
        """Mesh dosyalarını yükle"""
        try:
            mesh1 = o3d.io.read_triangle_mesh(path1)
            mesh2 = o3d.io.read_triangle_mesh(path2)
            
            # Normalleri hesapla
            mesh1.compute_vertex_normals()
            mesh2.compute_vertex_normals()
            
            return mesh1, mesh2
            
        except Exception as e:
            return None, None
    
    def _icp_alignment(
        self, 
        source: 'o3d.geometry.PointCloud', 
        target: 'o3d.geometry.PointCloud',
        threshold: float = 0.02
    ) -> Tuple[np.ndarray, Any]:
        """
        ICP ile hizalama.
        
        Returns:
            (transform matrix, icp result)
        """
        # Başlangıç tahmini (identity)
        trans_init = np.eye(4)
        
        # Global registration (kabaca hizala)
        source_down = source.voxel_down_sample(0.05)
        target_down = target.voxel_down_sample(0.05)
        
        source_down.estimate_normals()
        target_down.estimate_normals()
        
        # FPFH feature'ları hesapla
        source_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            source_down,
            o3d.geometry.KDTreeSearchParamHybrid(radius=0.25, max_nn=100)
        )
        target_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            target_down,
            o3d.geometry.KDTreeSearchParamHybrid(radius=0.25, max_nn=100)
        )
        
        # RANSAC global registration
        result_ransac = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
            source_down, target_down, source_fpfh, target_fpfh, True,
            threshold * 2,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
            3, [
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(threshold * 2)
            ], o3d.pipelines.registration.RANSACConvergenceCriteria(100000, 0.999)
        )
        
        trans_init = result_ransac.transformation
        
        # Fine ICP
        result_icp = o3d.pipelines.registration.registration_icp(
            source, target, threshold, trans_init,
            o3d.pipelines.registration.TransformationEstimationPointToPlane()
        )
        
        return result_icp.transformation, result_icp
    
    # ==================== MESAFE HESAPLAMA ====================
    
    def _compute_distances(
        self, 
        source: 'o3d.geometry.PointCloud', 
        target: 'o3d.geometry.PointCloud'
    ) -> np.ndarray:
        """
        İki point cloud arasındaki en yakın nokta mesafelerini hesapla.
        """
        distances = source.compute_point_cloud_distance(target)
        return np.asarray(distances)
    
    def _compute_hausdorff(
        self, 
        source: 'o3d.geometry.PointCloud', 
        target: 'o3d.geometry.PointCloud'
    ) -> float:
        """
        Hausdorff mesafesi hesapla.
        (İki küme arasındaki maksimum minimum mesafe)
        """
        dist1 = np.asarray(source.compute_point_cloud_distance(target))
        dist2 = np.asarray(target.compute_point_cloud_distance(source))
        
        return max(np.max(dist1), np.max(dist2))
    
    # ==================== REFERANS NESNE ====================
    
    def _detect_reference_object(
        self, 
        mesh: 'o3d.geometry.TriangleMesh',
        expected_size_mm: float
    ) -> ReferenceObject:
        """
        Referans nesneyi (örn: 1 cm küp) tespit et.
        
        Basit yaklaşım: Mesh'in en küçük bounding box boyutunu
        referans nesne boyutu olarak kabul et.
        
        Daha gelişmiş yaklaşımlar:
        - Küp şekli tanıma
        - Renk bazlı segmentasyon
        - ArUco marker tanıma (2D projeksiyon)
        """
        ref = ReferenceObject(expected_size_mm=expected_size_mm)
        
        try:
            # Oriented bounding box
            obb = mesh.get_oriented_bounding_box()
            extent = obb.extent
            
            # En küçük boyut (referans nesne tarafı olabilir)
            min_extent = min(extent)
            
            # Ölçek faktörü hesapla
            if min_extent > 0:
                ref.detected_size_mm = min_extent
                ref.scale_factor = expected_size_mm / min_extent
                ref.detected = True
                ref.position = tuple(obb.center)
            
        except Exception:
            ref.detected = False
        
        return ref
    
    # ==================== SEVİYE BELİRLEME ====================
    
    def _determine_level(self, result: DeteriorationResult) -> str:
        """Bozulma seviyesini belirle"""
        mean_dist = result.mean_distance
        
        if mean_dist < self.THRESHOLD_MINIMAL:
            return DeteriorationLevel.NONE.value
        elif mean_dist < self.THRESHOLD_MODERATE:
            return DeteriorationLevel.MINIMAL.value
        elif mean_dist < self.THRESHOLD_SEVERE:
            return DeteriorationLevel.MODERATE.value
        elif mean_dist < self.THRESHOLD_SEVERE * 2:
            return DeteriorationLevel.SEVERE.value
        else:
            return DeteriorationLevel.CRITICAL.value
    
    # ==================== DEĞİŞİM HARİTASI ====================
    
    def generate_change_map(
        self,
        baseline_path: str,
        current_path: str,
        output_path: str
    ) -> bool:
        """
        Değişim haritası oluştur (renklendirilmiş mesh).
        
        Değişim miktarına göre renklendirilmiş 3D model oluşturur.
        - Mavi: Değişim yok
        - Yeşil: Minimal değişim
        - Sarı: Orta değişim
        - Kırmızı: Yüksek değişim
        
        Args:
            baseline_path: Referans model
            current_path: Güncel model
            output_path: Çıktı dosya yolu (.ply)
            
        Returns:
            Başarılı mı?
        """
        try:
            baseline = o3d.io.read_triangle_mesh(baseline_path)
            current = o3d.io.read_triangle_mesh(current_path)
            
            # Point cloud'a çevir
            baseline_pc = baseline.sample_points_uniformly(50000)
            current_pc = current.sample_points_uniformly(50000)
            
            # Hizala
            transform, _ = self._icp_alignment(baseline_pc, current_pc)
            current_pc.transform(transform)
            
            # Mesafeleri hesapla
            distances = self._compute_distances(baseline_pc, current_pc)
            
            # Renkleri hesapla
            max_dist = max(np.max(distances), 1.0)
            normalized = np.clip(distances / max_dist, 0, 1)
            
            colors = np.zeros((len(distances), 3))
            
            # Renk gradyanı (mavi -> yeşil -> sarı -> kırmızı)
            for i, val in enumerate(normalized):
                if val < 0.25:
                    # Mavi -> Yeşil
                    t = val / 0.25
                    colors[i] = [0, t, 1-t]
                elif val < 0.5:
                    # Yeşil -> Sarı
                    t = (val - 0.25) / 0.25
                    colors[i] = [t, 1, 0]
                elif val < 0.75:
                    # Sarı -> Turuncu
                    t = (val - 0.5) / 0.25
                    colors[i] = [1, 1-t*0.5, 0]
                else:
                    # Turuncu -> Kırmızı
                    t = (val - 0.75) / 0.25
                    colors[i] = [1, 0.5*(1-t), 0]
            
            baseline_pc.colors = o3d.utility.Vector3dVector(colors)
            
            # Kaydet
            o3d.io.write_point_cloud(output_path, baseline_pc)
            
            return True
            
        except Exception:
            return False


# Yardımcı fonksiyon
def is_open3d_available() -> bool:
    """Open3D kullanılabilir mi?"""
    return OPEN3D_AVAILABLE
