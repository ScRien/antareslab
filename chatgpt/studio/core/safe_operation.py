"""
ANTARES 3D Studio - Safe Operation Module
Güvenli işlem yürütme ve hata yakalama

Bu modül, uygulamanın hiçbir zaman beklenmedik şekilde çökmemesini sağlar.
Her işlem try-catch ile sarılır ve kullanıcıya anlaşılır hata mesajları gösterilir.
"""

import sys
import traceback
from typing import Callable, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QThread, pyqtSignal


class OperationStatus(Enum):
    """İşlem durumu"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class OperationResult:
    """İşlem sonucu"""
    success: bool
    result: Any = None
    error_message: str = ""
    error_traceback: str = ""
    status: OperationStatus = OperationStatus.PENDING


class SafeOperation:
    """
    Her işlemi güvenli şekilde çalıştırır.
    Hata durumunda UI'ı bilgilendirir ve işlemi zararsız şekilde sonlandırır.
    
    Kullanım:
        result = SafeOperation.execute(
            func=lambda: process_images(images),
            error_callback=self.show_error_dialog,
            finally_callback=self.cleanup
        )
        
        if result.success:
            print(f"Sonuç: {result.result}")
        else:
            print(f"Hata: {result.error_message}")
    """
    
    @staticmethod
    def execute(
        func: Callable,
        error_callback: Optional[Callable[[str, str], None]] = None,
        finally_callback: Optional[Callable[[], None]] = None,
        default_return: Any = None
    ) -> OperationResult:
        """
        Fonksiyonu güvenli şekilde çalıştır.
        
        Args:
            func: Çalıştırılacak fonksiyon
            error_callback: Hata durumunda çağrılacak fonksiyon (message, traceback)
            finally_callback: Her durumda çağrılacak temizlik fonksiyonu
            default_return: Hata durumunda döndürülecek varsayılan değer
            
        Returns:
            OperationResult: İşlem sonucu
        """
        try:
            result = func()
            return OperationResult(
                success=True,
                result=result,
                status=OperationStatus.COMPLETED
            )
        except Exception as e:
            error_msg = str(e)
            error_tb = traceback.format_exc()
            
            if error_callback:
                try:
                    error_callback(error_msg, error_tb)
                except:
                    pass  # Error callback kendisi hata vermemeli
            
            return OperationResult(
                success=False,
                result=default_return,
                error_message=error_msg,
                error_traceback=error_tb,
                status=OperationStatus.ERROR
            )
        finally:
            if finally_callback:
                try:
                    finally_callback()
                except:
                    pass  # Finally callback kendisi hata vermemeli
    
    @staticmethod
    def wrap(error_callback: Optional[Callable] = None):
        """
        Dekoratör olarak kullanım için wrapper.
        
        Kullanım:
            @SafeOperation.wrap(error_callback=self.log_error)
            def risky_function():
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                return SafeOperation.execute(
                    func=lambda: func(*args, **kwargs),
                    error_callback=error_callback
                )
            return wrapper
        return decorator


class CancellableThread(QThread):
    """
    İptal edilebilir QThread base class.
    
    Tüm uzun süren işlemler bu class'ı extend etmeli.
    Bu sayede kullanıcı herhangi bir anda işlemi iptal edebilir.
    
    Kullanım:
        class MyProcessThread(CancellableThread):
            def run(self):
                for i in range(100):
                    if self.should_stop():
                        self.log.emit("⚠️ İşlem iptal edildi")
                        return
                    
                    # İşlem yap
                    self.progress.emit(i)
    """
    
    # Signals
    progress = pyqtSignal(int)           # İlerleme yüzdesi (0-100)
    log = pyqtSignal(str)                 # Log mesajı
    error = pyqtSignal(str, str)          # Hata (message, traceback)
    status_changed = pyqtSignal(str)      # Durum değişikliği
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False
        self._is_paused = False
        self._status = OperationStatus.PENDING
    
    def cancel(self):
        """İşlemi iptal et"""
        self._is_cancelled = True
        self._status = OperationStatus.CANCELLED
        self.status_changed.emit("cancelled")
        self.log.emit("⏹️ İptal isteği alındı...")
    
    def pause(self):
        """İşlemi duraklat"""
        self._is_paused = True
        self.status_changed.emit("paused")
        self.log.emit("⏸️ İşlem duraklatıldı")
    
    def resume(self):
        """İşleme devam et"""
        self._is_paused = False
        self.status_changed.emit("running")
        self.log.emit("▶️ İşleme devam ediliyor...")
    
    def should_stop(self) -> bool:
        """İşlemin durması gerekip gerekmediğini kontrol et"""
        return self._is_cancelled
    
    def wait_if_paused(self):
        """Duraklatılmışsa bekle"""
        while self._is_paused and not self._is_cancelled:
            self.msleep(100)
    
    def safe_emit_progress(self, value: int):
        """Güvenli progress emit (0-100 aralığında)"""
        clamped = max(0, min(100, value))
        self.progress.emit(clamped)
    
    def safe_run(self, func: Callable) -> OperationResult:
        """
        Ana işlemi güvenli şekilde çalıştır.
        
        Alt sınıflar run() metodunda bunu kullanmalı:
            def run(self):
                result = self.safe_run(self._do_work)
                if result.success:
                    self.finished.emit(result.result)
        """
        self._status = OperationStatus.RUNNING
        self.status_changed.emit("running")
        
        result = SafeOperation.execute(
            func=func,
            error_callback=lambda msg, tb: self.error.emit(msg, tb)
        )
        
        if result.success:
            self._status = OperationStatus.COMPLETED
            self.status_changed.emit("completed")
        
        return result
    
    @property
    def status(self) -> OperationStatus:
        return self._status
    
    @property
    def is_running(self) -> bool:
        return self._status == OperationStatus.RUNNING
    
    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled


class OperationQueue:
    """
    İşlem kuyruğu yöneticisi.
    Batch processing için kullanılır.
    """
    
    def __init__(self):
        self.queue: list = []
        self.current_index: int = 0
        self.is_processing: bool = False
    
    def add(self, operation: CancellableThread):
        """Kuyruğa işlem ekle"""
        self.queue.append(operation)
    
    def clear(self):
        """Kuyruğu temizle"""
        self.queue.clear()
        self.current_index = 0
    
    def get_progress(self) -> Tuple[int, int]:
        """
        Toplam ilerleme
        Returns: (tamamlanan, toplam)
        """
        return (self.current_index, len(self.queue))
    
    def cancel_all(self):
        """Tüm işlemleri iptal et"""
        for op in self.queue:
            if op.isRunning():
                op.cancel()
        self.is_processing = False
