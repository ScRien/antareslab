"""
ANTARES 3D Studio - Auto Calibration Module
Otomatik kamera kalibrasyonu

Özellikler:
- Dama tahtası kalibrasyon
- Lens distorsiyon düzeltme
- İç ve dış kamera parametreleri
- Otomatik görsellerdeki dama tahtası tespiti
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

# OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False


@dataclass
class CalibrationResult:
    """Kalibrasyon sonucu"""
    
    # Başarılı mı?
    success: bool = False
    
    # Kamera matrisi (3x3)
    camera_matrix: Optional[List[List[float]]] = None
    
    # Distorsiyon katsayıları (1x5)
    dist_coeffs: Optional[List[float]] = None
    
    # Reprojection hatası (piksel)
    reprojection_error: float = 0.0
    
    # Görüntü boyutu
    image_size: Tuple[int, int] = (0, 0)
    
    # Kullanılan görüntü sayısı
    images_used: int = 0
    
    # Işım merkezi (principal point)
    principal_point: Tuple[float, float] = (0.0, 0.0)
    
    # Odak uzaklığı (piksel)
    focal_length: Tuple[float, float] = (0.0, 0.0)
    
    # Kalibrasyon tarihi
    calibration_date: str = ""
    
    # Uyarılar
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON serileştirme"""
        return {
            'success': self.success,
            'camera_matrix': self.camera_matrix,
            'dist_coeffs': self.dist_coeffs,
            'reprojection_error': self.reprojection_error,
            'image_size': self.image_size,
            'images_used': self.images_used,
            'principal_point': self.principal_point,
            'focal_length': self.focal_length,
            'calibration_date': self.calibration_date,
            'warnings': self.warnings
        }
    
    def save(self, filepath: str) -> bool:
        """Dosyaya kaydet"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except:
            return False
    
    @classmethod
    def load(cls, filepath: str) -> Optional['CalibrationResult']:
        """Dosyadan yükle"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = cls()
            result.success = data.get('success', False)
            result.camera_matrix = data.get('camera_matrix')
            result.dist_coeffs = data.get('dist_coeffs')
            result.reprojection_error = data.get('reprojection_error', 0.0)
            result.image_size = tuple(data.get('image_size', (0, 0)))
            result.images_used = data.get('images_used', 0)
            result.principal_point = tuple(data.get('principal_point', (0.0, 0.0)))
            result.focal_length = tuple(data.get('focal_length', (0.0, 0.0)))
            result.calibration_date = data.get('calibration_date', '')
            result.warnings = data.get('warnings', [])
            
            return result
        except:
            return None
    
    def to_html(self) -> str:
        """HTML formatında rapor"""
        if not self.success:
            return "<h3>❌ Kalibrasyon Başarısız</h3>"
        
        html = f"""
        <h3>✅ Kalibrasyon Başarılı</h3>
        <p><b>Tarih:</b> {self.calibration_date}</p>
        
        <h4>📐 Parametreler</h4>
        <table style='width:100%; border-collapse: collapse;'>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>Odak Uzaklığı (fx)</td>
                <td style='padding:8px;'><b>{self.focal_length[0]:.2f} px</b></td>
            </tr>
            <tr>
                <td style='padding:8px;'>Odak Uzaklığı (fy)</td>
                <td style='padding:8px;'>{self.focal_length[1]:.2f} px</td>
            </tr>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>Merkez (cx)</td>
                <td style='padding:8px;'>{self.principal_point[0]:.2f} px</td>
            </tr>
            <tr>
                <td style='padding:8px;'>Merkez (cy)</td>
                <td style='padding:8px;'>{self.principal_point[1]:.2f} px</td>
            </tr>
        </table>
        
        <h4>📊 Kalite</h4>
        <ul>
            <li>Reprojection Hatası: <b>{self.reprojection_error:.4f} px</b></li>
            <li>Kullanılan Görüntü: {self.images_used}</li>
            <li>Görüntü Boyutu: {self.image_size[0]}x{self.image_size[1]}</li>
        </ul>
        """
        
        if self.warnings:
            html += "<h4>⚠️ Uyarılar</h4><ul>"
            for w in self.warnings:
                html += f"<li>{w}</li>"
            html += "</ul>"
        
        return html


class CameraCalibrator:
    """
    Otomatik kamera kalibrasyonu.
    
    Dama tahtası kalibrasyon görüntülerinden kamera parametrelerini hesaplar.
    
    Kullanım:
        calibrator = CameraCalibrator(
            checkerboard_size=(9, 6),  # İç köşe sayısı
            square_size_mm=25.0        # Kare boyutu (mm)
        )
        
        # Görüntülerden kalibre et
        result = calibrator.calibrate_from_images(image_paths)
        
        if result.success:
            # Kalibrasyon verilerini kaydet
            result.save("calibration.json")
            
            # Distorsiyonu düzelt
            undistorted = calibrator.undistort(image, result)
    
    Not:
        Dama tahtası boyutu İÇ KÖŞE sayısıdır, kare sayısı değil.
        Örnek: 10x7 kareli bir tahtanın iç köşe sayısı 9x6'dır.
    """
    
    # Kalibrasyon kalite eşikleri
    GOOD_REPROJECTION_ERROR = 0.5    # < 0.5 px = iyi
    ACCEPTABLE_ERROR = 1.0           # < 1.0 px = kabul edilebilir
    MIN_CALIBRATION_IMAGES = 10      # Minimum görüntü sayısı
    
    def __init__(
        self,
        checkerboard_size: Tuple[int, int] = (9, 6),
        square_size_mm: float = 25.0
    ):
        """
        Args:
            checkerboard_size: Dama tahtası iç köşe sayısı (columns, rows)
            square_size_mm: Kare kenar uzunluğu (mm)
        """
        if not OPENCV_AVAILABLE:
            raise ImportError(
                "OpenCV yüklü değil. Kurulum: pip install opencv-python"
            )
        
        self.checkerboard_size = checkerboard_size
        self.square_size_mm = square_size_mm
        
        # Kalibrasyon sonucu (cache)
        self._calibration: Optional[CalibrationResult] = None
        
        # Köşe tespiti kriterleri
        self._criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
            30, 0.001
        )
    
    def calibrate_from_images(
        self,
        image_paths: List[str],
        progress_callback=None
    ) -> CalibrationResult:
        """
        Görüntülerden kalibrasyon yap.
        
        Args:
            image_paths: Kalibrasyon görüntü yolları
            progress_callback: İlerleme callback (current, total)
            
        Returns:
            CalibrationResult
        """
        result = CalibrationResult()
        result.calibration_date = datetime.now().isoformat()
        
        if len(image_paths) < self.MIN_CALIBRATION_IMAGES:
            result.warnings.append(
                f"Yetersiz görüntü sayısı. "
                f"En az {self.MIN_CALIBRATION_IMAGES} görüntü önerilir."
            )
        
        # 3D dünya koordinatları
        objp = np.zeros((self.checkerboard_size[0] * self.checkerboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.checkerboard_size[0], 0:self.checkerboard_size[1]].T.reshape(-1, 2)
        objp *= self.square_size_mm
        
        # Tüm görüntülerden köşe noktaları
        obj_points = []  # 3D dünya koordinatları
        img_points = []  # 2D görüntü koordinatları
        
        img_size = None
        
        for i, path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i + 1, len(image_paths))
            
            # Görüntüyü yükle
            img = cv2.imread(path)
            if img is None:
                continue
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if img_size is None:
                img_size = gray.shape[::-1]
            
            # Dama tahtası köşelerini bul
            ret, corners = cv2.findChessboardCorners(
                gray, self.checkerboard_size, None
            )
            
            if ret:
                # Köşeleri refine et
                corners2 = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1), self._criteria
                )
                
                obj_points.append(objp)
                img_points.append(corners2)
        
        result.images_used = len(obj_points)
        
        if result.images_used < 3:
            result.success = False
            result.warnings.append(
                f"Dama tahtası yalnızca {result.images_used} görüntüde tespit edildi. "
                "En az 3 geçerli görüntü gerekli."
            )
            return result
        
        # Kalibrasyon yap
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, img_size, None, None
        )
        
        # Sonuçları kaydet
        result.success = True
        result.camera_matrix = mtx.tolist()
        result.dist_coeffs = dist.flatten().tolist()
        result.reprojection_error = ret
        result.image_size = img_size
        
        # Odak uzaklığı ve merkez
        result.focal_length = (mtx[0, 0], mtx[1, 1])
        result.principal_point = (mtx[0, 2], mtx[1, 2])
        
        # Kalite uyarıları
        if ret > self.ACCEPTABLE_ERROR:
            result.warnings.append(
                f"Yüksek reprojection hatası ({ret:.2f} px). "
                "Kalibrasyon kalitesi düşük olabilir."
            )
        elif ret > self.GOOD_REPROJECTION_ERROR:
            result.warnings.append(
                f"Kabul edilebilir reprojection hatası ({ret:.2f} px). "
                "Daha iyi sonuç için daha fazla görüntü kullanın."
            )
        
        self._calibration = result
        return result
    
    def calibrate_from_folder(
        self,
        folder_path: str,
        extensions: List[str] = ['.jpg', '.jpeg', '.png'],
        progress_callback=None
    ) -> CalibrationResult:
        """
        Klasördeki görüntülerden kalibrasyon yap.
        
        Args:
            folder_path: Görüntü klasörü
            extensions: Dosya uzantıları
            
        Returns:
            CalibrationResult
        """
        folder = Path(folder_path)
        
        images = []
        for ext in extensions:
            images.extend(folder.glob(f"*{ext}"))
            images.extend(folder.glob(f"*{ext.upper()}"))
        
        return self.calibrate_from_images(
            [str(p) for p in sorted(images)],
            progress_callback
        )
    
    def undistort(
        self,
        image,
        calibration: CalibrationResult = None
    ):
        """
        Distorsiyonu düzelt.
        
        Args:
            image: Girdi görüntüsü (numpy array veya yol)
            calibration: Kalibrasyon sonucu (None ise cache kullan)
            
        Returns:
            Düzeltilmiş görüntü
        """
        cal = calibration or self._calibration
        
        if cal is None or not cal.success:
            raise ValueError("Geçerli kalibrasyon verisi yok")
        
        # Görüntüyü yükle
        if isinstance(image, str):
            img = cv2.imread(image)
        else:
            img = image
        
        if img is None:
            return None
        
        # Numpy array'lere çevir
        mtx = np.array(cal.camera_matrix)
        dist = np.array(cal.dist_coeffs)
        
        h, w = img.shape[:2]
        
        # Optimal kamera matrisi
        new_mtx, roi = cv2.getOptimalNewCameraMatrix(
            mtx, dist, (w, h), 1, (w, h)
        )
        
        # Distorsiyonu düzelt
        undist = cv2.undistort(img, mtx, dist, None, new_mtx)
        
        # ROI ile kırp
        x, y, w, h = roi
        if w > 0 and h > 0:
            undist = undist[y:y+h, x:x+w]
        
        return undist
    
    def undistort_folder(
        self,
        input_folder: str,
        output_folder: str,
        calibration: CalibrationResult = None,
        progress_callback=None
    ) -> int:
        """
        Klasördeki tüm görüntülerin distorsiyonunu düzelt.
        
        Returns:
            İşlenen görüntü sayısı
        """
        cal = calibration or self._calibration
        
        if cal is None or not cal.success:
            raise ValueError("Geçerli kalibrasyon verisi yok")
        
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        extensions = ['.jpg', '.jpeg', '.png']
        images = []
        for ext in extensions:
            images.extend(input_path.glob(f"*{ext}"))
            images.extend(input_path.glob(f"*{ext.upper()}"))
        
        count = 0
        
        for i, img_path in enumerate(sorted(images)):
            if progress_callback:
                progress_callback(i + 1, len(images))
            
            undist = self.undistort(str(img_path), cal)
            
            if undist is not None:
                out_file = output_path / img_path.name
                cv2.imwrite(str(out_file), undist)
                count += 1
        
        return count
    
    def detect_checkerboard(
        self,
        image_path: str,
        draw: bool = True
    ) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Görüntüdeki dama tahtasını tespit et.
        
        Args:
            image_path: Görüntü yolu
            draw: Köşeleri çiz
            
        Returns:
            (tespit edildi mi?, görselleştirilmiş görüntü)
        """
        img = cv2.imread(image_path)
        if img is None:
            return False, None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        ret, corners = cv2.findChessboardCorners(
            gray, self.checkerboard_size, None
        )
        
        if ret and draw:
            corners2 = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), self._criteria
            )
            cv2.drawChessboardCorners(
                img, self.checkerboard_size, corners2, ret
            )
        
        return ret, img


def is_opencv_available() -> bool:
    """OpenCV kullanılabilir mi?"""
    return OPENCV_AVAILABLE
