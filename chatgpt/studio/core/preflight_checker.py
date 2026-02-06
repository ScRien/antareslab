"""
ANTARES 3D Studio - Pre-flight Checker Module
İşlem öncesi kontroller

Her kritik işlemden önce gerekli koşulların sağlandığından emin olur.
Eksik veya hatalı durumlar kullanıcıya anlaşılır şekilde raporlanır.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import requests


class CheckStatus(Enum):
    """Kontrol durumu"""
    PASSED = "passed"      # ✅ Başarılı
    WARNING = "warning"    # ⚠️ Uyarı (devam edilebilir)
    FAILED = "failed"      # ❌ Başarısız (devam edilemez)
    SKIPPED = "skipped"    # ⏭️ Atlandı


@dataclass
class CheckResult:
    """Tek bir kontrolün sonucu"""
    name: str
    status: CheckStatus
    message: str
    suggestion: str = ""   # Düzeltme önerisi
    details: str = ""      # Teknik detaylar
    
    @property
    def passed(self) -> bool:
        return self.status in [CheckStatus.PASSED, CheckStatus.WARNING, CheckStatus.SKIPPED]
    
    @property
    def icon(self) -> str:
        icons = {
            CheckStatus.PASSED: "✅",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.FAILED: "❌",
            CheckStatus.SKIPPED: "⏭️"
        }
        return icons.get(self.status, "❓")


@dataclass
class PreFlightReport:
    """Tüm kontrollerin raporu"""
    checks: List[CheckResult]
    can_proceed: bool
    summary: str
    
    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASSED)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARNING)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAILED)
    
    def to_html(self) -> str:
        """HTML formatında rapor"""
        html = "<h3>🔍 Ön Kontrol Raporu</h3><ul>"
        for check in self.checks:
            color = {
                CheckStatus.PASSED: "green",
                CheckStatus.WARNING: "orange", 
                CheckStatus.FAILED: "red",
                CheckStatus.SKIPPED: "gray"
            }.get(check.status, "black")
            
            html += f"<li style='color:{color}'>{check.icon} <b>{check.name}</b>: {check.message}"
            if check.suggestion:
                html += f"<br><i>💡 {check.suggestion}</i>"
            html += "</li>"
        
        html += "</ul>"
        html += f"<p><b>Sonuç:</b> {self.summary}</p>"
        return html


class PreFlightChecker:
    """
    İşlem öncesi kontrol sistemi.
    
    Kullanım:
        checker = PreFlightChecker()
        
        # Tek kontrol
        result = checker.check_esp32_connection("192.168.4.1")
        if not result.passed:
            print(result.message)
        
        # Toplu kontrol (3D model oluşturma öncesi)
        report = checker.run_3d_preflight(
            esp32_ip="192.168.4.1",
            image_paths=images,
            output_dir=output_path
        )
        
        if not report.can_proceed:
            show_error_dialog(report.to_html())
    """
    
    # Sabitler
    MIN_IMAGES_FOR_3D = 8
    RECOMMENDED_IMAGES = 12
    MIN_DISK_SPACE_MB = 500
    ESP32_TIMEOUT = 5
    
    def __init__(self):
        self._dependency_cache: Dict[str, bool] = {}
    
    # ==================== BAĞLANTI KONTROLLER ====================
    
    def check_esp32_connection(self, ip: str) -> CheckResult:
        """ESP32 bağlantısını kontrol et"""
        try:
            response = requests.get(f"http://{ip}/", timeout=self.ESP32_TIMEOUT)
            
            if response.status_code == 200:
                return CheckResult(
                    name="ESP32 Bağlantısı",
                    status=CheckStatus.PASSED,
                    message=f"ESP32'ye başarıyla bağlanıldı ({ip})"
                )
            else:
                return CheckResult(
                    name="ESP32 Bağlantısı",
                    status=CheckStatus.FAILED,
                    message=f"ESP32 yanıt verdi ama HTTP {response.status_code} döndü",
                    suggestion="ESP32'yi yeniden başlatmayı deneyin"
                )
                
        except requests.exceptions.Timeout:
            return CheckResult(
                name="ESP32 Bağlantısı",
                status=CheckStatus.FAILED,
                message=f"ESP32 ({ip}) yanıt vermiyor - zaman aşımı",
                suggestion="1. WiFi bağlantınızı kontrol edin (ANTARES_KAPSUL_V8)\n"
                          "2. ESP32'nin açık olduğundan emin olun\n"
                          "3. IP adresini doğrulayın"
            )
        except requests.exceptions.ConnectionError:
            return CheckResult(
                name="ESP32 Bağlantısı",
                status=CheckStatus.FAILED,
                message=f"ESP32 ({ip}) ile bağlantı kurulamadı",
                suggestion="WiFi ağına bağlı olduğunuzdan emin olun"
            )
        except Exception as e:
            return CheckResult(
                name="ESP32 Bağlantısı",
                status=CheckStatus.FAILED,
                message=f"Beklenmeyen hata: {str(e)}",
                details=str(e)
            )
    
    # ==================== GÖRÜNTÜ KONTROLLERİ ====================
    
    def check_image_count(self, image_paths: List[str]) -> CheckResult:
        """Minimum görüntü sayısını kontrol et"""
        count = len(image_paths)
        
        if count >= self.RECOMMENDED_IMAGES:
            return CheckResult(
                name="Görüntü Sayısı",
                status=CheckStatus.PASSED,
                message=f"{count} görüntü mevcut (önerilen: {self.RECOMMENDED_IMAGES}+)"
            )
        elif count >= self.MIN_IMAGES_FOR_3D:
            return CheckResult(
                name="Görüntü Sayısı",
                status=CheckStatus.WARNING,
                message=f"{count} görüntü mevcut (minimum: {self.MIN_IMAGES_FOR_3D})",
                suggestion=f"Daha iyi sonuç için {self.RECOMMENDED_IMAGES}+ görüntü önerilir"
            )
        else:
            return CheckResult(
                name="Görüntü Sayısı",
                status=CheckStatus.FAILED,
                message=f"Yetersiz görüntü: {count}/{self.MIN_IMAGES_FOR_3D}",
                suggestion="3D model için en az 8 görüntü gereklidir. "
                          "Lütfen önce tarama yapın."
            )
    
    def check_images_exist(self, image_paths: List[str]) -> CheckResult:
        """Görüntü dosyalarının varlığını kontrol et"""
        missing = []
        
        for path in image_paths:
            if not os.path.exists(path):
                missing.append(os.path.basename(path))
        
        if not missing:
            return CheckResult(
                name="Görüntü Dosyaları",
                status=CheckStatus.PASSED,
                message=f"Tüm görüntüler mevcut ({len(image_paths)} dosya)"
            )
        else:
            return CheckResult(
                name="Görüntü Dosyaları",
                status=CheckStatus.FAILED,
                message=f"{len(missing)} görüntü bulunamadı",
                details=", ".join(missing[:5]) + ("..." if len(missing) > 5 else ""),
                suggestion="Görüntüleri yeniden indirmeyi deneyin"
            )
    
    # ==================== SİSTEM KONTROLLERİ ====================
    
    def check_disk_space(self, target_dir: str, required_mb: int = None) -> CheckResult:
        """Yeterli disk alanı var mı"""
        required_mb = required_mb or self.MIN_DISK_SPACE_MB
        
        try:
            # Hedef dizinin bulunduğu sürücüyü bul
            if sys.platform == 'win32':
                drive = os.path.splitdrive(target_dir)[0]
                if not drive:
                    drive = os.path.splitdrive(os.getcwd())[0]
                target_path = drive + "\\"
            else:
                target_path = target_dir
            
            total, used, free = shutil.disk_usage(target_path)
            free_mb = free // (1024 * 1024)
            
            if free_mb >= required_mb:
                return CheckResult(
                    name="Disk Alanı",
                    status=CheckStatus.PASSED,
                    message=f"{free_mb:,} MB boş alan mevcut"
                )
            else:
                return CheckResult(
                    name="Disk Alanı",
                    status=CheckStatus.FAILED,
                    message=f"Yetersiz disk alanı: {free_mb:,} MB (gerekli: {required_mb:,} MB)",
                    suggestion="Disk alanı açın veya farklı bir sürücü seçin"
                )
                
        except Exception as e:
            return CheckResult(
                name="Disk Alanı",
                status=CheckStatus.WARNING,
                message=f"Disk alanı kontrol edilemedi: {str(e)}"
            )
    
    def check_output_directory(self, output_dir: str) -> CheckResult:
        """Çıktı dizinini kontrol et (oluşturulabilir mi?)"""
        try:
            path = Path(output_dir)
            
            if path.exists():
                if path.is_dir():
                    # Yazılabilir mi?
                    test_file = path / ".antares_test"
                    try:
                        test_file.touch()
                        test_file.unlink()
                        return CheckResult(
                            name="Çıktı Dizini",
                            status=CheckStatus.PASSED,
                            message=f"Dizin mevcut ve yazılabilir: {output_dir}"
                        )
                    except PermissionError:
                        return CheckResult(
                            name="Çıktı Dizini",
                            status=CheckStatus.FAILED,
                            message=f"Dizine yazma izni yok: {output_dir}",
                            suggestion="Farklı bir dizin seçin veya izinleri kontrol edin"
                        )
                else:
                    return CheckResult(
                        name="Çıktı Dizini",
                        status=CheckStatus.FAILED,
                        message=f"Hedef bir dizin değil, dosya: {output_dir}",
                        suggestion="Farklı bir dizin seçin"
                    )
            else:
                # Dizin yok, oluşturulabilir mi?
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    return CheckResult(
                        name="Çıktı Dizini",
                        status=CheckStatus.PASSED,
                        message=f"Dizin oluşturuldu: {output_dir}"
                    )
                except PermissionError:
                    return CheckResult(
                        name="Çıktı Dizini",
                        status=CheckStatus.FAILED,
                        message=f"Dizin oluşturulamadı (izin hatası): {output_dir}",
                        suggestion="Farklı bir konum seçin"
                    )
                    
        except Exception as e:
            return CheckResult(
                name="Çıktı Dizini",
                status=CheckStatus.FAILED,
                message=f"Dizin kontrolü başarısız: {str(e)}"
            )
    
    # ==================== BAĞIMLILIK KONTROLLERİ ====================
    
    def check_dependency(self, module_name: str, package_name: str = None, 
                        required: bool = True) -> CheckResult:
        """Python modülünün yüklü olup olmadığını kontrol et"""
        package_name = package_name or module_name
        
        # Cache kontrolü
        if module_name in self._dependency_cache:
            is_available = self._dependency_cache[module_name]
        else:
            try:
                __import__(module_name)
                is_available = True
            except ImportError:
                is_available = False
            self._dependency_cache[module_name] = is_available
        
        if is_available:
            return CheckResult(
                name=f"Kütüphane: {package_name}",
                status=CheckStatus.PASSED,
                message=f"{package_name} yüklü"
            )
        else:
            status = CheckStatus.FAILED if required else CheckStatus.WARNING
            return CheckResult(
                name=f"Kütüphane: {package_name}",
                status=status,
                message=f"{package_name} yüklü değil",
                suggestion=f"Kurulum: pip install {package_name}"
            )
    
    def check_dependencies(self, include_optional: bool = True) -> List[CheckResult]:
        """Tüm bağımlılıkları kontrol et"""
        results = []
        
        # Zorunlu bağımlılıklar
        required = [
            ("cv2", "opencv-python"),
            ("numpy", "numpy"),
            ("PIL", "Pillow"),
            ("PyQt6", "PyQt6"),
            ("requests", "requests"),
        ]
        
        for module, package in required:
            results.append(self.check_dependency(module, package, required=True))
        
        # Opsiyonel bağımlılıklar
        if include_optional:
            optional = [
                ("open3d", "open3d"),
                ("rembg", "rembg"),
                ("pyvista", "pyvista"),
            ]
            
            for module, package in optional:
                results.append(self.check_dependency(module, package, required=False))
        
        return results
    
    # ==================== TOPLU KONTROLLER ====================
    
    def run_connection_preflight(self, esp32_ip: str) -> PreFlightReport:
        """ESP32 bağlantısı öncesi kontroller"""
        checks = [
            self.check_esp32_connection(esp32_ip)
        ]
        
        can_proceed = all(c.passed for c in checks)
        
        return PreFlightReport(
            checks=checks,
            can_proceed=can_proceed,
            summary="ESP32 bağlantısı başarılı" if can_proceed else "Bağlantı kurulamadı"
        )
    
    def run_download_preflight(self, esp32_ip: str, output_dir: str) -> PreFlightReport:
        """İndirme öncesi kontroller"""
        checks = [
            self.check_esp32_connection(esp32_ip),
            self.check_disk_space(output_dir),
            self.check_output_directory(output_dir),
        ]
        
        can_proceed = all(c.status != CheckStatus.FAILED for c in checks)
        
        if can_proceed:
            summary = "İndirme başlatılabilir"
        else:
            failed = [c.name for c in checks if c.status == CheckStatus.FAILED]
            summary = f"İndirme başlatılamaz: {', '.join(failed)}"
        
        return PreFlightReport(
            checks=checks,
            can_proceed=can_proceed,
            summary=summary
        )
    
    def run_3d_preflight(self, image_paths: List[str], output_dir: str) -> PreFlightReport:
        """3D model oluşturma öncesi kontroller"""
        checks = [
            self.check_image_count(image_paths),
            self.check_images_exist(image_paths),
            self.check_disk_space(output_dir),
            self.check_output_directory(output_dir),
        ]
        
        # Bağımlılık kontrolü
        checks.extend(self.check_dependencies())
        
        can_proceed = all(c.status != CheckStatus.FAILED for c in checks)
        
        if can_proceed:
            warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)
            if warnings:
                summary = f"İşlem başlatılabilir ({warnings} uyarı)"
            else:
                summary = "Tüm kontroller başarılı, işlem başlatılabilir"
        else:
            failed = [c.name for c in checks if c.status == CheckStatus.FAILED]
            summary = f"İşlem başlatılamaz: {', '.join(failed)}"
        
        return PreFlightReport(
            checks=checks,
            can_proceed=can_proceed,
            summary=summary
        )
