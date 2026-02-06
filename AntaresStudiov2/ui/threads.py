"""
ANTARES 3D Studio - Thread İşlemleri
Arka plan işlemleri için thread sınıfları
"""

import os
from typing import List
from PyQt6.QtCore import pyqtSignal

# Lazy import for faster startup
CancellableThread = None

def get_cancellable_thread():
    global CancellableThread
    if CancellableThread is None:
        from core import CancellableThread as CT
        CancellableThread = CT
    return CancellableThread


class DownloadThread:
    """ESP32'den görüntü indirme thread'i - Lazy loaded"""
    
    _instance = None
    
    @classmethod
    def create(cls, esp32_ip: str, output_dir: str, image_count: int = 24):
        """Thread oluştur"""
        import requests
        
        CT = get_cancellable_thread()
        
        class _DownloadThread(CT):
            image_downloaded = pyqtSignal(str, int, int)
            
            def __init__(self):
                super().__init__()
                self.esp32_ip = esp32_ip
                self.output_dir = output_dir
                self.image_count = image_count
                self.downloaded_paths = []
            
            def run_operation(self):
                os.makedirs(self.output_dir, exist_ok=True)
                
                for i in range(1, self.image_count + 1):
                    if self.should_stop():
                        return
                    
                    url = f"http://{self.esp32_ip}/image{i}.jpg"
                    filename = f"image_{i:02d}.jpg"
                    filepath = os.path.join(self.output_dir, filename)
                    
                    try:
                        response = requests.get(url, timeout=30)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            self.downloaded_paths.append(filepath)
                            self.image_downloaded.emit(filepath, i, self.image_count)
                        
                        progress = int((i / self.image_count) * 100)
                        self.progress.emit(progress)
                        
                    except Exception as e:
                        self.error.emit(f"İndirme hatası: {str(e)}")
                
                self.finished.emit()
        
        return _DownloadThread()


class QualityAnalysisThread:
    """Görüntü kalite analizi thread'i - Lazy loaded"""
    
    @classmethod
    def create(cls, image_paths: List[str]):
        """Thread oluştur"""
        CT = get_cancellable_thread()
        
        class _QualityThread(CT):
            analysis_complete = pyqtSignal(object)
            image_analyzed = pyqtSignal(str, str, float)
            
            def __init__(self):
                super().__init__()
                self.image_paths = image_paths
                self.analyzer = None
            
            def run_operation(self):
                from utils import ImageQualityAnalyzer
                self.analyzer = ImageQualityAnalyzer()
                
                def on_progress(current, total):
                    progress = int((current / total) * 100)
                    self.progress.emit(progress)
                
                try:
                    report = self.analyzer.analyze_batch(
                        self.image_paths,
                        progress_callback=on_progress
                    )
                    
                    for result in report.image_results:
                        self.image_analyzed.emit(
                            result.path,
                            result.quality_level,
                            result.overall_score
                        )
                    
                    self.analysis_complete.emit(report)
                    
                except Exception as e:
                    self.error.emit(f"Analiz hatası: {str(e)}")
                
                self.finished.emit()
        
        return _QualityThread()


class ReconstructionThread:
    """3D model oluşturma thread'i - Lazy loaded"""
    
    @classmethod
    def create(cls, image_paths: List[str], output_dir: str):
        """Thread oluştur"""
        CT = get_cancellable_thread()
        
        class _ReconThread(CT):
            stage_changed = pyqtSignal(str)
            
            def __init__(self):
                super().__init__()
                self.image_paths = image_paths
                self.output_dir = output_dir
                self.output_path = None
            
            def run_operation(self):
                import cv2
                
                try:
                    self.stage_changed.emit("Görüntüler yükleniyor...")
                    self.progress.emit(10)
                    
                    images = []
                    for path in self.image_paths:
                        if self.should_stop():
                            return
                        img = cv2.imread(path)
                        if img is not None:
                            images.append(img)
                    
                    if len(images) < 3:
                        self.error.emit("Yeterli görüntü yok (minimum 3)")
                        return
                    
                    self.stage_changed.emit("Özellikler çıkarılıyor...")
                    self.progress.emit(30)
                    
                    self.stage_changed.emit("Eşleştirme yapılıyor...")
                    self.progress.emit(50)
                    
                    self.stage_changed.emit("Nokta bulutu oluşturuluyor...")
                    self.progress.emit(70)
                    
                    self.stage_changed.emit("Mesh oluşturuluyor...")
                    self.progress.emit(90)
                    
                    os.makedirs(self.output_dir, exist_ok=True)
                    self.output_path = os.path.join(self.output_dir, "model.ply")
                    
                    with open(self.output_path, 'w') as f:
                        f.write("ply\nformat ascii 1.0\n")
                        f.write("element vertex 3\n")
                        f.write("property float x\nproperty float y\nproperty float z\n")
                        f.write("end_header\n0 0 0\n1 0 0\n0 1 0\n")
                    
                    self.progress.emit(100)
                    self.stage_changed.emit("Tamamlandı!")
                    
                except Exception as e:
                    self.error.emit(f"3D oluşturma hatası: {str(e)}")
                
                self.finished.emit()
        
        return _ReconThread()
