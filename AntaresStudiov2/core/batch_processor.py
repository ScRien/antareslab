"""
ANTARES 3D Studio - Batch Processing Module
Toplu işlem yönetimi

Özellikler:
- Kuyruk tabanlı işlem yönetimi
- Çoklu proje işleme
- İlerleme takibi
- Hata yönetimi
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, QThread


class BatchJobStatus(Enum):
    """Toplu iş durumu"""
    PENDING = "pending"       # Bekliyor
    RUNNING = "running"       # Çalışıyor
    PAUSED = "paused"         # Duraklatıldı
    COMPLETED = "completed"   # Tamamlandı
    FAILED = "failed"         # Başarısız
    CANCELLED = "cancelled"   # İptal edildi


@dataclass
class BatchJob:
    """Tek bir toplu iş"""
    id: str
    name: str
    job_type: str  # "download", "analyze", "reconstruct"
    params: Dict[str, Any]
    
    status: BatchJobStatus = BatchJobStatus.PENDING
    progress: int = 0
    
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    result: Any = None
    error_message: str = ""
    
    @property
    def duration_seconds(self) -> float:
        """İşlem süresi"""
        if not self.started_at:
            return 0
        
        start = datetime.fromisoformat(self.started_at)
        
        if self.completed_at:
            end = datetime.fromisoformat(self.completed_at)
        else:
            end = datetime.now()
        
        return (end - start).total_seconds()


@dataclass
class BatchQueue:
    """Toplu iş kuyruğu"""
    jobs: List[BatchJob] = field(default_factory=list)
    
    @property
    def pending_count(self) -> int:
        return sum(1 for j in self.jobs if j.status == BatchJobStatus.PENDING)
    
    @property
    def completed_count(self) -> int:
        return sum(1 for j in self.jobs if j.status == BatchJobStatus.COMPLETED)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for j in self.jobs if j.status == BatchJobStatus.FAILED)
    
    @property
    def overall_progress(self) -> int:
        if not self.jobs:
            return 0
        
        total = len(self.jobs) * 100
        current = sum(j.progress for j in self.jobs)
        
        return int(current / total * 100)
    
    def add_job(self, job: BatchJob):
        """İş ekle"""
        self.jobs.append(job)
    
    def get_next_pending(self) -> Optional[BatchJob]:
        """Sonraki bekleyen işi al"""
        for job in self.jobs:
            if job.status == BatchJobStatus.PENDING:
                return job
        return None
    
    def clear_completed(self):
        """Tamamlanan işleri temizle"""
        self.jobs = [j for j in self.jobs if j.status not in 
                    [BatchJobStatus.COMPLETED, BatchJobStatus.CANCELLED]]


class BatchProcessor(QObject):
    """
    Toplu işlem yöneticisi.
    
    Özellikler:
    - Sıralı iş yürütme
    - Duraklatma/devam ettirme
    - Hata yönetimi
    - İlerleme takibi
    
    Kullanım:
        processor = BatchProcessor()
        
        # İş ekle
        processor.add_download_job(project1, esp32_ip)
        processor.add_download_job(project2, esp32_ip)
        processor.add_reconstruction_job(project1)
        
        # Sinyalleri bağla
        processor.job_started.connect(on_job_started)
        processor.job_completed.connect(on_job_completed)
        processor.all_completed.connect(on_all_done)
        
        # Başlat
        processor.start()
    """
    
    # Sinyaller
    job_started = pyqtSignal(str, str)  # job_id, job_name
    job_progress = pyqtSignal(str, int)  # job_id, progress
    job_completed = pyqtSignal(str, bool, str)  # job_id, success, message
    all_completed = pyqtSignal(int, int)  # success_count, fail_count
    queue_progress = pyqtSignal(int)  # overall progress
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.queue = BatchQueue()
        self._running = False
        self._paused = False
        self._current_thread: Optional[QThread] = None
        
        # İş tipleri için handler'lar
        self._handlers: Dict[str, Callable] = {}
    
    def register_handler(self, job_type: str, handler: Callable):
        """
        İş tipi için handler kaydet.
        
        Handler signature: handler(params: dict, progress_callback) -> result
        """
        self._handlers[job_type] = handler
    
    # ==================== İŞ EKLEME ====================
    
    def add_job(
        self,
        name: str,
        job_type: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Kuyruğa iş ekle.
        
        Returns:
            job_id
        """
        import uuid
        job_id = str(uuid.uuid4())[:8]
        
        job = BatchJob(
            id=job_id,
            name=name,
            job_type=job_type,
            params=params
        )
        
        self.queue.add_job(job)
        return job_id
    
    def add_download_job(
        self,
        project_name: str,
        output_dir: str,
        esp32_ip: str,
        image_count: int = 24
    ) -> str:
        """İndirme işi ekle"""
        return self.add_job(
            name=f"İndir: {project_name}",
            job_type="download",
            params={
                'output_dir': output_dir,
                'esp32_ip': esp32_ip,
                'image_count': image_count
            }
        )
    
    def add_analysis_job(
        self,
        project_name: str,
        image_paths: List[str]
    ) -> str:
        """Analiz işi ekle"""
        return self.add_job(
            name=f"Analiz: {project_name}",
            job_type="analyze",
            params={'image_paths': image_paths}
        )
    
    def add_reconstruction_job(
        self,
        project_name: str,
        image_paths: List[str],
        output_dir: str
    ) -> str:
        """3D oluşturma işi ekle"""
        return self.add_job(
            name=f"3D: {project_name}",
            job_type="reconstruct",
            params={
                'image_paths': image_paths,
                'output_dir': output_dir
            }
        )
    
    # ==================== KONTROL ====================
    
    def start(self):
        """Kuyruğu başlat"""
        if self._running:
            return
        
        self._running = True
        self._paused = False
        self._process_next()
    
    def pause(self):
        """Duraksat"""
        self._paused = True
    
    def resume(self):
        """Devam et"""
        if self._paused:
            self._paused = False
            self._process_next()
    
    def cancel(self):
        """İptal et"""
        self._running = False
        
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.terminate()
            self._current_thread.wait(2000)
        
        # Bekleyen işleri iptal et
        for job in self.queue.jobs:
            if job.status == BatchJobStatus.RUNNING:
                job.status = BatchJobStatus.CANCELLED
    
    def clear(self):
        """Kuyruğu temizle"""
        self.queue.jobs.clear()
    
    # ==================== İŞLEM ====================
    
    def _process_next(self):
        """Sonraki işi işle"""
        if not self._running or self._paused:
            return
        
        job = self.queue.get_next_pending()
        
        if job is None:
            # Tüm işler tamamlandı
            self._running = False
            self.all_completed.emit(
                self.queue.completed_count,
                self.queue.failed_count
            )
            return
        
        # İşi başlat
        self._run_job(job)
    
    def _run_job(self, job: BatchJob):
        """İşi çalıştır"""
        job.status = BatchJobStatus.RUNNING
        job.started_at = datetime.now().isoformat()
        
        self.job_started.emit(job.id, job.name)
        
        # Handler'ı bul
        handler = self._handlers.get(job.job_type)
        
        if handler is None:
            job.status = BatchJobStatus.FAILED
            job.error_message = f"Handler bulunamadı: {job.job_type}"
            self.job_completed.emit(job.id, False, job.error_message)
            self._process_next()
            return
        
        # Thread ile çalıştır
        class JobThread(QThread):
            def __init__(self, handler, params, progress_callback):
                super().__init__()
                self.handler = handler
                self.params = params
                self.progress_callback = progress_callback
                self.result = None
                self.error = None
            
            def run(self):
                try:
                    self.result = self.handler(
                        self.params, 
                        self.progress_callback
                    )
                except Exception as e:
                    self.error = str(e)
        
        def on_progress(p):
            job.progress = p
            self.job_progress.emit(job.id, p)
            self.queue_progress.emit(self.queue.overall_progress)
        
        thread = JobThread(handler, job.params, on_progress)
        
        def on_finished():
            job.completed_at = datetime.now().isoformat()
            
            if thread.error:
                job.status = BatchJobStatus.FAILED
                job.error_message = thread.error
                self.job_completed.emit(job.id, False, thread.error)
            else:
                job.status = BatchJobStatus.COMPLETED
                job.progress = 100
                job.result = thread.result
                self.job_completed.emit(job.id, True, "Tamamlandı")
            
            self._process_next()
        
        thread.finished.connect(on_finished)
        self._current_thread = thread
        thread.start()
    
    # ==================== RAPORLAMA ====================
    
    def get_summary(self) -> Dict[str, Any]:
        """Kuyruk özeti"""
        return {
            'total': len(self.queue.jobs),
            'pending': self.queue.pending_count,
            'completed': self.queue.completed_count,
            'failed': self.queue.failed_count,
            'progress': self.queue.overall_progress
        }
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """İş durumunu al"""
        for job in self.queue.jobs:
            if job.id == job_id:
                return job
        return None


# ==============================================================================
# HAZIR HANDLER'LAR
# ==============================================================================

def create_download_handler(esp32_downloader):
    """İndirme handler'ı oluştur"""
    def handler(params, progress_callback):
        output_dir = params['output_dir']
        esp32_ip = params['esp32_ip']
        image_count = params.get('image_count', 24)
        
        import requests
        
        os.makedirs(output_dir, exist_ok=True)
        downloaded = []
        
        for i in range(1, image_count + 1):
            url = f"http://{esp32_ip}/image{i}.jpg"
            filepath = os.path.join(output_dir, f"image_{i:02d}.jpg")
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                downloaded.append(filepath)
            
            progress_callback(int(i / image_count * 100))
        
        return downloaded
    
    return handler


def create_analysis_handler(analyzer):
    """Analiz handler'ı oluştur"""
    def handler(params, progress_callback):
        image_paths = params['image_paths']
        
        return analyzer.analyze_batch(
            image_paths,
            progress_callback=lambda c, t: progress_callback(int(c/t*100))
        )
    
    return handler


def create_reconstruction_handler(reconstructor):
    """3D oluşturma handler'ı oluştur"""
    def handler(params, progress_callback):
        image_paths = params['image_paths']
        output_dir = params['output_dir']
        
        # TODO: Gerçek 3D reconstruction
        for i in range(10):
            time.sleep(0.5)
            progress_callback(i * 10)
        
        output_path = os.path.join(output_dir, "model.ply")
        
        # Placeholder
        with open(output_path, 'w') as f:
            f.write("ply\nformat ascii 1.0\nend_header\n")
        
        progress_callback(100)
        return output_path
    
    return handler
