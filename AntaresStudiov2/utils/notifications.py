"""
ANTARES 3D Studio - Notification Manager Module
Bildirim sistemi

Özellikler:
- Windows toast bildirimleri
- Ses bildirimleri
- Durum çubuğu mesajları
"""

import sys
import os
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


class NotificationType(Enum):
    """Bildirim türü"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationManager:
    """
    Bildirim yöneticisi.
    
    Özellikler:
    - Windows 10/11 toast bildirimleri
    - Sistem sesleri
    - Callback desteği
    
    Kullanım:
        notifier = NotificationManager()
        
        # Basit bildirim
        notifier.notify("Başarılı!", "3D model oluşturuldu.", NotificationType.SUCCESS)
        
        # Sadece ses
        notifier.play_sound(NotificationType.SUCCESS)
    """
    
    # Ses dosyaları klasörü
    SOUNDS_DIR = Path(__file__).parent.parent / "sounds"
    
    # Varsayılan sesler (Windows sistem sesleri)
    SYSTEM_SOUNDS = {
        NotificationType.INFO: "SystemAsterisk",
        NotificationType.SUCCESS: "SystemExclamation",
        NotificationType.WARNING: "SystemHand",
        NotificationType.ERROR: "SystemHand"
    }
    
    def __init__(self, app_name: str = "ANTARES 3D Studio"):
        self.app_name = app_name
        self.sounds_enabled = True
        self.notifications_enabled = True
        self._toast_available = self._check_toast_support()
        self._callbacks: dict = {}
    
    def _check_toast_support(self) -> bool:
        """Windows toast bildirimi desteğini kontrol et"""
        if sys.platform != 'win32':
            return False
        
        try:
            from win10toast import ToastNotifier
            return True
        except ImportError:
            return False
    
    # ==================== BİLDİRİMLER ====================
    
    def notify(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        duration: int = 5,
        play_sound: bool = True
    ) -> bool:
        """
        Bildirim gönder.
        
        Args:
            title: Bildirim başlığı
            message: Bildirim mesajı
            notification_type: Bildirim türü
            duration: Görünme süresi (saniye)
            play_sound: Ses çalsın mı?
            
        Returns:
            Başarılı mı?
        """
        if not self.notifications_enabled:
            return False
        
        success = False
        
        # Toast bildirimi
        if self._toast_available:
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                
                # İkon belirleme
                icon_path = self._get_icon_path(notification_type)
                
                toaster.show_toast(
                    title=f"{self.app_name} - {title}",
                    msg=message,
                    duration=duration,
                    threaded=True,
                    icon_path=icon_path
                )
                success = True
            except Exception:
                pass
        
        # Ses çal
        if play_sound and self.sounds_enabled:
            self.play_sound(notification_type)
        
        # Callback çağır
        if notification_type in self._callbacks:
            try:
                self._callbacks[notification_type](title, message)
            except:
                pass
        
        return success
    
    def notify_success(self, title: str, message: str):
        """Başarı bildirimi"""
        return self.notify(title, message, NotificationType.SUCCESS)
    
    def notify_error(self, title: str, message: str):
        """Hata bildirimi"""
        return self.notify(title, message, NotificationType.ERROR)
    
    def notify_warning(self, title: str, message: str):
        """Uyarı bildirimi"""
        return self.notify(title, message, NotificationType.WARNING)
    
    def notify_info(self, title: str, message: str):
        """Bilgi bildirimi"""
        return self.notify(title, message, NotificationType.INFO)
    
    # ==================== SES ====================
    
    def play_sound(self, notification_type: NotificationType = NotificationType.INFO) -> bool:
        """
        Bildirim sesi çal.
        
        Args:
            notification_type: Ses türü
            
        Returns:
            Başarılı mı?
        """
        if not self.sounds_enabled:
            return False
        
        if sys.platform == 'win32':
            return self._play_windows_sound(notification_type)
        else:
            return self._play_cross_platform_sound(notification_type)
    
    def _play_windows_sound(self, notification_type: NotificationType) -> bool:
        """Windows'ta ses çal"""
        try:
            import winsound
            
            # Önce özel ses dosyasını dene
            sound_file = self._get_sound_file(notification_type)
            if sound_file and sound_file.exists():
                winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            
            # Sistem sesini çal
            sound_alias = self.SYSTEM_SOUNDS.get(notification_type, "SystemAsterisk")
            winsound.PlaySound(sound_alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
            return True
            
        except Exception:
            return False
    
    def _play_cross_platform_sound(self, notification_type: NotificationType) -> bool:
        """Platformlar arası ses çalma"""
        try:
            sound_file = self._get_sound_file(notification_type)
            if not sound_file or not sound_file.exists():
                return False
            
            # PyGame veya simpleaudio kullan
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(str(sound_file))
                pygame.mixer.music.play()
                return True
            except ImportError:
                pass
            
            try:
                import simpleaudio as sa
                wave_obj = sa.WaveObject.from_wave_file(str(sound_file))
                wave_obj.play()
                return True
            except ImportError:
                pass
            
            return False
            
        except Exception:
            return False
    
    def _get_sound_file(self, notification_type: NotificationType) -> Optional[Path]:
        """Ses dosyası yolunu al"""
        sound_names = {
            NotificationType.INFO: "info.wav",
            NotificationType.SUCCESS: "success.wav",
            NotificationType.WARNING: "warning.wav",
            NotificationType.ERROR: "error.wav"
        }
        
        filename = sound_names.get(notification_type)
        if filename:
            sound_path = self.SOUNDS_DIR / filename
            if sound_path.exists():
                return sound_path
        
        return None
    
    def _get_icon_path(self, notification_type: NotificationType) -> Optional[str]:
        """Bildirim ikonu yolunu al"""
        # TODO: Özel ikonlar eklenebilir
        return None
    
    # ==================== AYARLAR ====================
    
    def set_sounds_enabled(self, enabled: bool):
        """Sesleri aç/kapat"""
        self.sounds_enabled = enabled
    
    def set_notifications_enabled(self, enabled: bool):
        """Bildirimleri aç/kapat"""
        self.notifications_enabled = enabled
    
    def register_callback(self, notification_type: NotificationType, callback: Callable):
        """
        Bildirim callback'i kaydet.
        
        Callback signature: callback(title: str, message: str)
        """
        self._callbacks[notification_type] = callback
    
    def unregister_callback(self, notification_type: NotificationType):
        """Callback'i kaldır"""
        if notification_type in self._callbacks:
            del self._callbacks[notification_type]
    
    # ==================== HAZIR BİLDİRİMLER ====================
    
    def notify_3d_complete(self, project_name: str, output_path: str):
        """3D model tamamlandı bildirimi"""
        self.notify_success(
            "3D Model Hazır!",
            f"{project_name} projesi için 3D model başarıyla oluşturuldu.\n"
            f"Konum: {output_path}"
        )
    
    def notify_download_complete(self, image_count: int):
        """İndirme tamamlandı bildirimi"""
        self.notify_success(
            "İndirme Tamamlandı",
            f"{image_count} görüntü başarıyla indirildi."
        )
    
    def notify_processing_error(self, error_message: str):
        """İşleme hatası bildirimi"""
        self.notify_error(
            "İşlem Hatası",
            f"Bir hata oluştu: {error_message}"
        )
    
    def notify_low_disk_space(self, available_mb: int):
        """Düşük disk alanı uyarısı"""
        self.notify_warning(
            "Düşük Disk Alanı",
            f"Yalnızca {available_mb} MB boş alan kaldı.\n"
            "Bazı dosyaları silmeniz önerilir."
        )
    
    def notify_connection_lost(self):
        """Bağlantı koptu bildirimi"""
        self.notify_error(
            "Bağlantı Koptu",
            "ESP32 ile bağlantı kesildi.\n"
            "Lütfen cihazı kontrol edin."
        )
    
    def notify_backup_complete(self, project_name: str):
        """Yedekleme tamamlandı bildirimi"""
        self.notify_info(
            "Yedekleme Tamamlandı",
            f"{project_name} projesi yedeklendi."
        )


# Kolay kullanım için global instance
_default_notifier: Optional[NotificationManager] = None


def get_notifier() -> NotificationManager:
    """Global NotificationManager instance'ını al"""
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = NotificationManager()
    return _default_notifier


def notify(title: str, message: str, 
           notification_type: NotificationType = NotificationType.INFO):
    """Kısa yol: Bildirim gönder"""
    return get_notifier().notify(title, message, notification_type)


def notify_success(title: str, message: str):
    """Kısa yol: Başarı bildirimi"""
    return get_notifier().notify_success(title, message)


def notify_error(title: str, message: str):
    """Kısa yol: Hata bildirimi"""
    return get_notifier().notify_error(title, message)
