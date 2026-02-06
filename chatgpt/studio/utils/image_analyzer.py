"""
ANTARES 3D Studio - Image Quality Analyzer Module
Görüntü kalite analizi

Arkeolojik alan fotoğrafları için optimize edilmiş kalite kontrolü.
Özellikler:
- Bulanıklık tespiti (Laplacian variance)
- Parlaklık ve kontrast analizi
- Işık dağılımı analizi (arkeolojik alanlarda kritik)
- Örtüşme (overlap) tahmini
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class QualityLevel(Enum):
    """Kalite seviyesi"""
    EXCELLENT = "excellent"   # Mükemmel
    GOOD = "good"             # İyi
    ACCEPTABLE = "acceptable" # Kabul edilebilir
    POOR = "poor"             # Zayıf
    REJECTED = "rejected"     # Reddedildi


@dataclass
class ImageQuality:
    """Tek görüntü kalite raporu"""
    path: str
    filename: str
    
    # Temel metrikler
    blur_score: float = 0.0          # Bulanıklık skoru (yüksek = net)
    brightness: float = 0.0           # Ortalama parlaklık (0-255)
    contrast: float = 0.0             # Kontrast (std deviation)
    sharpness: float = 0.0            # Keskinlik
    
    # Işık dağılımı (arkeolojik alan için kritik)
    light_uniformity: float = 0.0     # Işık homojenliği (0-1, 1=homojen)
    dark_regions_percent: float = 0.0 # Karanlık bölge yüzdesi
    overexposed_percent: float = 0.0  # Aşırı parlak bölge yüzdesi
    shadow_balance: float = 0.0       # Gölge dengesi (0-1, 0.5=dengeli)
    
    # Sonuç
    quality_level: str = "acceptable"
    is_acceptable: bool = True
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Görüntü boyutları
    width: int = 0
    height: int = 0
    
    @property
    def overall_score(self) -> float:
        """Genel kalite skoru (0-100)"""
        # Ağırlıklı skor hesabı
        blur_norm = min(self.blur_score / 500, 1.0) * 30  # Max 30 puan
        bright_score = (1 - abs(self.brightness - 128) / 128) * 20  # Max 20 puan
        contrast_norm = min(self.contrast / 80, 1.0) * 20  # Max 20 puan
        light_score = self.light_uniformity * 30  # Max 30 puan
        
        return blur_norm + bright_score + contrast_norm + light_score


@dataclass
class QualityReport:
    """Toplu kalite raporu"""
    total_images: int
    analyzed_images: int
    
    # Sayımlar
    excellent_count: int = 0
    good_count: int = 0
    acceptable_count: int = 0
    poor_count: int = 0
    rejected_count: int = 0
    
    # Ortalamalar
    avg_blur_score: float = 0.0
    avg_brightness: float = 0.0
    avg_contrast: float = 0.0
    avg_light_uniformity: float = 0.0
    
    # Genel
    overall_quality: str = "acceptable"
    can_proceed_with_3d: bool = True
    
    # Uyarılar ve öneriler
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Detaylı sonuçlar
    image_results: List[ImageQuality] = field(default_factory=list)
    
    def to_html(self) -> str:
        """HTML formatında rapor"""
        quality_colors = {
            "excellent": "#00ff00",
            "good": "#90EE90",
            "acceptable": "#ffff00",
            "poor": "#ffa500",
            "rejected": "#ff0000"
        }
        
        html = f"""
        <h3>📊 Görüntü Kalite Raporu</h3>
        <table style='width:100%; border-collapse: collapse;'>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>Toplam Görüntü</td>
                <td style='padding:8px;'><b>{self.total_images}</b></td>
            </tr>
            <tr>
                <td style='padding:8px;'>Mükemmel</td>
                <td style='padding:8px; color:#00ff00;'>✅ {self.excellent_count}</td>
            </tr>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>İyi</td>
                <td style='padding:8px; color:#90EE90;'>👍 {self.good_count}</td>
            </tr>
            <tr>
                <td style='padding:8px;'>Kabul Edilebilir</td>
                <td style='padding:8px; color:#ffff00;'>⚠️ {self.acceptable_count}</td>
            </tr>
            <tr style='background:#203a43;'>
                <td style='padding:8px;'>Zayıf</td>
                <td style='padding:8px; color:#ffa500;'>⚡ {self.poor_count}</td>
            </tr>
            <tr>
                <td style='padding:8px;'>Reddedilen</td>
                <td style='padding:8px; color:#ff0000;'>❌ {self.rejected_count}</td>
            </tr>
        </table>
        
        <h4>📈 Ortalama Değerler</h4>
        <ul>
            <li>Netlik Skoru: {self.avg_blur_score:.1f}</li>
            <li>Parlaklık: {self.avg_brightness:.1f}/255</li>
            <li>Kontrast: {self.avg_contrast:.1f}</li>
            <li>Işık Homojenliği: {self.avg_light_uniformity*100:.1f}%</li>
        </ul>
        
        <h4>Genel Değerlendirme</h4>
        <p style='color:{quality_colors.get(self.overall_quality, "white")};'>
            <b>{self.overall_quality.upper()}</b>
        </p>
        """
        
        if self.warnings:
            html += "<h4>⚠️ Uyarılar</h4><ul>"
            for w in self.warnings:
                html += f"<li>{w}</li>"
            html += "</ul>"
        
        if self.suggestions:
            html += "<h4>💡 Öneriler</h4><ul>"
            for s in self.suggestions:
                html += f"<li>{s}</li>"
            html += "</ul>"
        
        return html


class ImageQualityAnalyzer:
    """
    Görüntü kalite analizi.
    
    Arkeolojik alanlarda ışık çok değişken olduğundan,
    özellikle ışık dağılımı analizi kritik önem taşır.
    
    Kullanım:
        analyzer = ImageQualityAnalyzer()
        
        # Tek görüntü
        result = analyzer.analyze(image_path)
        print(f"Kalite: {result.quality_level}")
        
        # Toplu analiz
        report = analyzer.analyze_batch(image_paths)
        if not report.can_proceed_with_3d:
            show_warning(report.to_html())
    """
    
    # Eşik değerleri
    BLUR_THRESHOLD_EXCELLENT = 500.0
    BLUR_THRESHOLD_GOOD = 200.0
    BLUR_THRESHOLD_ACCEPTABLE = 100.0
    BLUR_THRESHOLD_POOR = 50.0
    
    BRIGHTNESS_MIN = 40
    BRIGHTNESS_MAX = 220
    BRIGHTNESS_OPTIMAL_MIN = 80
    BRIGHTNESS_OPTIMAL_MAX = 180
    
    CONTRAST_MIN = 30.0
    
    DARK_REGION_THRESHOLD = 30      # Bu değerin altı karanlık
    OVEREXPOSED_THRESHOLD = 250     # Bu değerin üstü aşırı parlak
    ACCEPTABLE_DARK_PERCENT = 15.0  # Maksimum kabul edilebilir karanlık %
    ACCEPTABLE_BRIGHT_PERCENT = 10.0  # Maksimum kabul edilebilir aşırı parlak %
    
    MIN_IMAGES_FOR_3D = 8
    MIN_ACCEPTABLE_RATIO = 0.7  # En az %70 kabul edilebilir olmalı
    
    def __init__(self):
        pass
    
    def analyze(self, image_path: str) -> ImageQuality:
        """
        Tek görüntüyü analiz et.
        
        Args:
            image_path: Görüntü dosya yolu
            
        Returns:
            ImageQuality sonucu
        """
        result = ImageQuality(
            path=image_path,
            filename=os.path.basename(image_path)
        )
        
        try:
            # Görüntüyü yükle
            img = cv2.imread(image_path)
            if img is None:
                result.is_acceptable = False
                result.quality_level = QualityLevel.REJECTED.value
                result.warnings.append("Görüntü yüklenemedi")
                return result
            
            result.height, result.width = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Bulanıklık analizi
            result.blur_score = self._calculate_blur(gray)
            
            # 2. Parlaklık ve kontrast
            result.brightness = self._calculate_brightness(gray)
            result.contrast = self._calculate_contrast(gray)
            
            # 3. Keskinlik
            result.sharpness = self._calculate_sharpness(gray)
            
            # 4. Işık dağılımı analizi (arkeolojik alan için kritik!)
            light_analysis = self._analyze_light_distribution(gray)
            result.light_uniformity = light_analysis['uniformity']
            result.dark_regions_percent = light_analysis['dark_percent']
            result.overexposed_percent = light_analysis['overexposed_percent']
            result.shadow_balance = light_analysis['shadow_balance']
            
            # 5. Kalite seviyesi belirleme
            self._determine_quality_level(result)
            
            return result
            
        except Exception as e:
            result.is_acceptable = False
            result.quality_level = QualityLevel.REJECTED.value
            result.warnings.append(f"Analiz hatası: {str(e)}")
            return result
    
    def analyze_batch(self, image_paths: List[str], progress_callback=None) -> QualityReport:
        """
        Birden fazla görüntüyü analiz et.
        
        Args:
            image_paths: Görüntü dosya yolları listesi
            progress_callback: İlerleme callback (index, total)
            
        Returns:
            QualityReport
        """
        total = len(image_paths)
        results = []
        
        for i, path in enumerate(image_paths):
            result = self.analyze(path)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        # Rapor oluştur
        report = QualityReport(
            total_images=total,
            analyzed_images=len(results)
        )
        
        # Kalite sayımları
        for r in results:
            if r.quality_level == QualityLevel.EXCELLENT.value:
                report.excellent_count += 1
            elif r.quality_level == QualityLevel.GOOD.value:
                report.good_count += 1
            elif r.quality_level == QualityLevel.ACCEPTABLE.value:
                report.acceptable_count += 1
            elif r.quality_level == QualityLevel.POOR.value:
                report.poor_count += 1
            else:
                report.rejected_count += 1
        
        # Ortalamalar
        if results:
            report.avg_blur_score = sum(r.blur_score for r in results) / len(results)
            report.avg_brightness = sum(r.brightness for r in results) / len(results)
            report.avg_contrast = sum(r.contrast for r in results) / len(results)
            report.avg_light_uniformity = sum(r.light_uniformity for r in results) / len(results)
        
        # Genel kalite
        report.overall_quality = self._determine_overall_quality(report)
        
        # 3D için uygunluk
        acceptable_count = (report.excellent_count + report.good_count + 
                          report.acceptable_count)
        acceptable_ratio = acceptable_count / total if total > 0 else 0
        
        report.can_proceed_with_3d = (
            acceptable_count >= self.MIN_IMAGES_FOR_3D and
            acceptable_ratio >= self.MIN_ACCEPTABLE_RATIO
        )
        
        # Uyarılar ve öneriler
        self._generate_batch_warnings(report, results)
        
        report.image_results = results
        
        return report
    
    # ==================== ANALİZ METODLARI ====================
    
    def _calculate_blur(self, gray: np.ndarray) -> float:
        """
        Bulanıklık hesapla (Laplacian variance).
        Düşük değer = bulanık, Yüksek değer = net
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()
    
    def _calculate_brightness(self, gray: np.ndarray) -> float:
        """Ortalama parlaklık (0-255)"""
        return float(np.mean(gray))
    
    def _calculate_contrast(self, gray: np.ndarray) -> float:
        """Kontrast (standart sapma)"""
        return float(np.std(gray))
    
    def _calculate_sharpness(self, gray: np.ndarray) -> float:
        """
        Keskinlik hesapla (Sobel gradient magnitude).
        """
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        return float(np.mean(magnitude))
    
    def _analyze_light_distribution(self, gray: np.ndarray) -> Dict[str, float]:
        """
        Işık dağılımı analizi.
        
        Arkeolojik alanlarda ışık çok değişken olduğundan,
        bu analiz 3D model kalitesi için kritik önem taşır.
        
        Returns:
            - uniformity: Işık homojenliği (0-1, 1 = çok homojen)
            - dark_percent: Karanlık bölge yüzdesi
            - overexposed_percent: Aşırı parlak bölge yüzdesi
            - shadow_balance: Gölge dengesi (0-1, 0.5 = dengeli)
        """
        h, w = gray.shape
        
        # Görüntüyü 4 bölgeye ayır (üst-sol, üst-sağ, alt-sol, alt-sağ)
        mid_h, mid_w = h // 2, w // 2
        
        regions = [
            gray[:mid_h, :mid_w],      # Üst-sol
            gray[:mid_h, mid_w:],      # Üst-sağ
            gray[mid_h:, :mid_w],      # Alt-sol
            gray[mid_h:, mid_w:]       # Alt-sağ
        ]
        
        # Her bölgenin ortalama parlaklığı
        region_means = [float(np.mean(r)) for r in regions]
        
        # Homojenlik: Bölgeler arası varyans düşükse homojen
        variance = np.var(region_means)
        max_possible_variance = 128**2  # Maksimum olası varyans
        uniformity = 1 - min(variance / max_possible_variance, 1.0)
        
        # Karanlık bölge yüzdesi
        dark_pixels = np.sum(gray < self.DARK_REGION_THRESHOLD)
        dark_percent = (dark_pixels / gray.size) * 100
        
        # Aşırı parlak bölge yüzdesi
        overexposed_pixels = np.sum(gray > self.OVEREXPOSED_THRESHOLD)
        overexposed_percent = (overexposed_pixels / gray.size) * 100
        
        # Gölge dengesi: Sol-sağ parlaklık dengesi
        left_mean = float(np.mean(gray[:, :mid_w]))
        right_mean = float(np.mean(gray[:, mid_w:]))
        
        if max(left_mean, right_mean) > 0:
            balance_ratio = min(left_mean, right_mean) / max(left_mean, right_mean)
        else:
            balance_ratio = 1.0
        
        # 0.5'e normalize et (0 = çok dengesiz, 0.5 = mükemmel dengeli, 1 = ters dengesiz)
        # Aslında balance_ratio zaten 0-1 arasında, 1 = mükemmel
        shadow_balance = balance_ratio
        
        return {
            'uniformity': uniformity,
            'dark_percent': dark_percent,
            'overexposed_percent': overexposed_percent,
            'shadow_balance': shadow_balance,
            'region_means': region_means
        }
    
    # ==================== KALİTE BELİRLEME ====================
    
    def _determine_quality_level(self, result: ImageQuality):
        """Kalite seviyesi ve uyarıları belirle"""
        warnings = []
        suggestions = []
        
        # Bulanıklık kontrolü
        if result.blur_score >= self.BLUR_THRESHOLD_EXCELLENT:
            blur_level = "excellent"
        elif result.blur_score >= self.BLUR_THRESHOLD_GOOD:
            blur_level = "good"
        elif result.blur_score >= self.BLUR_THRESHOLD_ACCEPTABLE:
            blur_level = "acceptable"
            warnings.append("Görüntü biraz bulanık")
            suggestions.append("Kamerayı sabit tutun veya tripod kullanın")
        elif result.blur_score >= self.BLUR_THRESHOLD_POOR:
            blur_level = "poor"
            warnings.append("Görüntü bulanık")
            suggestions.append("Fotoğrafı yeniden çekin")
        else:
            blur_level = "rejected"
            warnings.append("Görüntü çok bulanık - kullanılamaz")
        
        # Parlaklık kontrolü
        if result.brightness < self.BRIGHTNESS_MIN:
            warnings.append(f"Görüntü çok karanlık ({result.brightness:.0f}/255)")
            suggestions.append("Daha fazla ışık kullanın")
        elif result.brightness > self.BRIGHTNESS_MAX:
            warnings.append(f"Görüntü çok parlak ({result.brightness:.0f}/255)")
            suggestions.append("Işığı azaltın veya pozlamayı düşürün")
        elif result.brightness < self.BRIGHTNESS_OPTIMAL_MIN:
            warnings.append("Görüntü biraz karanlık")
        elif result.brightness > self.BRIGHTNESS_OPTIMAL_MAX:
            warnings.append("Görüntü biraz parlak")
        
        # Kontrast kontrolü
        if result.contrast < self.CONTRAST_MIN:
            warnings.append("Düşük kontrast")
            suggestions.append("Nesne ve arka plan arasında daha fazla kontrast sağlayın")
        
        # Işık dağılımı kontrolü (kritik!)
        if result.light_uniformity < 0.6:
            warnings.append(f"Işık dağılımı dengesiz ({result.light_uniformity*100:.0f}% homojen)")
            suggestions.append("Tüm yüzeyleri eşit aydınlatın - diffuse ışık kullanın")
        
        if result.dark_regions_percent > self.ACCEPTABLE_DARK_PERCENT:
            warnings.append(f"Fazla karanlık bölge ({result.dark_regions_percent:.1f}%)")
            suggestions.append("Gölgeli bölgeleri aydınlatın - 3D modelde bu bölgeler gürültülü olacak")
        
        if result.overexposed_percent > self.ACCEPTABLE_BRIGHT_PERCENT:
            warnings.append(f"Aşırı parlak bölgeler ({result.overexposed_percent:.1f}%)")
            suggestions.append("Yansımaları ve parlak noktaları azaltın")
        
        if result.shadow_balance < 0.7:
            warnings.append("Sol-sağ ışık dengesi bozuk")
            suggestions.append("Işık kaynaklarını nesnenin her iki tarafına da yerleştirin")
        
        # Genel seviye belirleme
        levels = {
            "excellent": 5,
            "good": 4,
            "acceptable": 3,
            "poor": 2,
            "rejected": 1
        }
        
        # Minimum seviyeyi al (en kötü metrik belirler)
        min_level = levels[blur_level]
        
        # Işık sorunları varsa düşür
        if result.light_uniformity < 0.5:
            min_level = min(min_level, 2)
        elif result.light_uniformity < 0.7:
            min_level = min(min_level, 3)
        
        if result.dark_regions_percent > 30:
            min_level = min(min_level, 2)
        
        if result.brightness < self.BRIGHTNESS_MIN or result.brightness > self.BRIGHTNESS_MAX:
            min_level = min(min_level, 2)
        
        # Seviye eşleştirme
        level_names = {v: k for k, v in levels.items()}
        result.quality_level = level_names[min_level]
        result.is_acceptable = min_level >= 3
        result.warnings = warnings
        result.suggestions = suggestions
    
    def _determine_overall_quality(self, report: QualityReport) -> str:
        """Genel kalite seviyesi belirleme"""
        total = report.analyzed_images
        if total == 0:
            return "rejected"
        
        excellent_ratio = report.excellent_count / total
        good_ratio = (report.excellent_count + report.good_count) / total
        acceptable_ratio = (report.excellent_count + report.good_count + 
                          report.acceptable_count) / total
        
        if excellent_ratio >= 0.7:
            return "excellent"
        elif good_ratio >= 0.7:
            return "good"
        elif acceptable_ratio >= 0.7:
            return "acceptable"
        elif acceptable_ratio >= 0.5:
            return "poor"
        else:
            return "rejected"
    
    def _generate_batch_warnings(self, report: QualityReport, results: List[ImageQuality]):
        """Toplu rapor için uyarı ve öneriler"""
        warnings = []
        suggestions = []
        
        if report.rejected_count > 0:
            warnings.append(f"{report.rejected_count} görüntü kullanılamaz durumda")
        
        if report.poor_count > 0:
            warnings.append(f"{report.poor_count} görüntü düşük kaliteli")
        
        # Ortalama ışık homojenliği düşükse
        if report.avg_light_uniformity < 0.6:
            warnings.append("Genel olarak ışık dağılımı dengesiz")
            suggestions.append("Diffuse aydınlatma kullanın (light box veya softbox)")
            suggestions.append("Tüm yüzeyleri eşit şekilde aydınlatın")
        
        # Ortalama bulanıklık yüksekse
        if report.avg_blur_score < self.BLUR_THRESHOLD_ACCEPTABLE:
            warnings.append("Genel olarak görüntüler bulanık")
            suggestions.append("Tripod kullanın veya kamerayı sabitleyin")
            suggestions.append("Deklanşör hızını artırın")
        
        # 3D için yeterli görüntü yoksa
        acceptable_count = (report.excellent_count + report.good_count + 
                          report.acceptable_count)
        
        if acceptable_count < self.MIN_IMAGES_FOR_3D:
            warnings.append(f"3D model için yeterli kaliteli görüntü yok ({acceptable_count}/{self.MIN_IMAGES_FOR_3D})")
            suggestions.append("Daha fazla kaliteli görüntü çekin")
        
        report.warnings = warnings
        suggestions_unique = list(dict.fromkeys(suggestions))  # Tekrarları kaldır
        report.suggestions = suggestions_unique
    
    # ==================== YARDIMCI METODLAR ====================
    
    def create_thumbnail(
        self, 
        image_path: str, 
        output_path: str, 
        size: Tuple[int, int] = (200, 200),
        quality_overlay: bool = True
    ) -> bool:
        """
        Kalite göstergeli thumbnail oluştur.
        
        Args:
            image_path: Kaynak görüntü
            output_path: Çıktı yolu
            size: Thumbnail boyutu
            quality_overlay: Kalite göstergesi ekle
            
        Returns:
            Başarılı mı?
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return False
            
            # Boyutlandır
            h, w = img.shape[:2]
            scale = min(size[0] / w, size[1] / h)
            new_size = (int(w * scale), int(h * scale))
            thumbnail = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
            
            # Kalite göstergesi ekle
            if quality_overlay:
                quality = self.analyze(image_path)
                
                # Renk belirleme
                colors = {
                    "excellent": (0, 255, 0),    # Yeşil
                    "good": (144, 238, 144),      # Açık yeşil
                    "acceptable": (0, 255, 255),  # Sarı
                    "poor": (0, 165, 255),        # Turuncu
                    "rejected": (0, 0, 255)       # Kırmızı
                }
                color = colors.get(quality.quality_level, (255, 255, 255))
                
                # Çerçeve ekle
                cv2.rectangle(thumbnail, (0, 0), (new_size[0]-1, new_size[1]-1), color, 3)
                
                # Skor ekle
                score_text = f"{quality.overall_score:.0f}"
                cv2.putText(thumbnail, score_text, (5, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            cv2.imwrite(output_path, thumbnail)
            return True
            
        except Exception:
            return False
    
    def generate_thumbnails(
        self, 
        image_paths: List[str], 
        output_dir: str,
        progress_callback=None
    ) -> List[str]:
        """
        Birden fazla görüntü için thumbnail oluştur.
        
        Returns:
            Oluşturulan thumbnail yolları
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        thumbnails = []
        total = len(image_paths)
        
        for i, img_path in enumerate(image_paths):
            filename = Path(img_path).stem + "_thumb.jpg"
            thumb_path = output_path / filename
            
            if self.create_thumbnail(img_path, str(thumb_path)):
                thumbnails.append(str(thumb_path))
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return thumbnails
