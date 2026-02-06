"""
ANTARES 3D Studio - ETA Calculator Module
İşlem süresi tahmini

Uzun süren işlemler için kalan süreyi tahmin eder.
"""

import time
from typing import Optional, Tuple
from collections import deque
from dataclasses import dataclass


@dataclass
class ETAInfo:
    """ETA bilgisi"""
    elapsed_seconds: float
    remaining_seconds: float
    total_estimated_seconds: float
    progress_percent: float
    rate_per_second: float
    
    @property
    def elapsed_formatted(self) -> str:
        return ETACalculator.format_duration(self.elapsed_seconds)
    
    @property
    def remaining_formatted(self) -> str:
        return ETACalculator.format_duration(self.remaining_seconds)
    
    @property
    def total_formatted(self) -> str:
        return ETACalculator.format_duration(self.total_estimated_seconds)


class ETACalculator:
    """
    İşlem süresi tahmini hesaplayıcı.
    
    Özellikler:
    - Hareketli ortalama ile yumuşatılmış tahmin
    - Değişken hızlı işlemler için adaptif
    - Formatlanmış süre çıktısı
    
    Kullanım:
        eta = ETACalculator()
        
        # İşlemi başlat
        eta.start(total_items=100)
        
        for i in range(100):
            # İşlemi yap
            process_item(i)
            
            # ETA güncelle
            eta.update(completed=i+1)
            
            # Kalan süreyi göster
            print(f"Kalan: {eta.get_remaining_formatted()}")
    """
    
    def __init__(self, smoothing_window: int = 10):
        """
        Args:
            smoothing_window: Hareketli ortalama pencere boyutu
        """
        self.smoothing_window = smoothing_window
        self.reset()
    
    def reset(self):
        """Hesaplayıcıyı sıfırla"""
        self.started_at: Optional[float] = None
        self.total_items: int = 0
        self.completed_items: int = 0
        self.last_update_time: Optional[float] = None
        self.rate_samples: deque = deque(maxlen=self.smoothing_window)
    
    def start(self, total_items: int):
        """
        İşlemi başlat.
        
        Args:
            total_items: Toplam işlenecek öğe sayısı
        """
        self.reset()
        self.total_items = total_items
        self.started_at = time.time()
        self.last_update_time = self.started_at
    
    def update(self, completed: int) -> ETAInfo:
        """
        İlerlemeyi güncelle ve ETA hesapla.
        
        Args:
            completed: Tamamlanan öğe sayısı
            
        Returns:
            ETAInfo
        """
        if self.started_at is None:
            self.start(max(completed, 1))
        
        now = time.time()
        
        # Hız hesapla (öğe/saniye)
        if self.last_update_time and completed > self.completed_items:
            time_delta = now - self.last_update_time
            items_delta = completed - self.completed_items
            
            if time_delta > 0:
                current_rate = items_delta / time_delta
                self.rate_samples.append(current_rate)
        
        self.completed_items = completed
        self.last_update_time = now
        
        # Toplam geçen süre
        elapsed = now - self.started_at
        
        # Ortalama hız
        if self.rate_samples:
            avg_rate = sum(self.rate_samples) / len(self.rate_samples)
        elif elapsed > 0 and completed > 0:
            avg_rate = completed / elapsed
        else:
            avg_rate = 0
        
        # Kalan süre tahmini
        remaining_items = self.total_items - completed
        
        if avg_rate > 0:
            remaining_seconds = remaining_items / avg_rate
        else:
            remaining_seconds = 0
        
        total_estimated = elapsed + remaining_seconds
        progress = (completed / self.total_items * 100) if self.total_items > 0 else 0
        
        return ETAInfo(
            elapsed_seconds=elapsed,
            remaining_seconds=remaining_seconds,
            total_estimated_seconds=total_estimated,
            progress_percent=progress,
            rate_per_second=avg_rate
        )
    
    def get_remaining(self) -> float:
        """Kalan süreyi saniye olarak döndür"""
        info = self.update(self.completed_items)
        return info.remaining_seconds
    
    def get_remaining_formatted(self) -> str:
        """Kalan süreyi formatlanmış olarak döndür"""
        remaining = self.get_remaining()
        return self.format_duration(remaining)
    
    def get_elapsed(self) -> float:
        """Geçen süreyi saniye olarak döndür"""
        if self.started_at is None:
            return 0
        return time.time() - self.started_at
    
    def get_elapsed_formatted(self) -> str:
        """Geçen süreyi formatlanmış olarak döndür"""
        return self.format_duration(self.get_elapsed())
    
    def get_progress_text(self) -> str:
        """İlerleme metni: "45% (3/10 tamamlandı, ~2 dk kaldı)" """
        info = self.update(self.completed_items)
        
        progress_text = f"{info.progress_percent:.0f}%"
        count_text = f"{self.completed_items}/{self.total_items}"
        remaining_text = self.format_duration(info.remaining_seconds)
        
        return f"{progress_text} ({count_text} tamamlandı, ~{remaining_text} kaldı)"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Süreyi okunabilir formata çevir.
        
        Örnekler:
            45 -> "45 sn"
            90 -> "1 dk 30 sn"
            3700 -> "1 sa 1 dk"
        """
        if seconds < 0:
            return "0 sn"
        
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds} sn"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            if secs > 0:
                return f"{minutes} dk {secs} sn"
            return f"{minutes} dk"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} sa {minutes} dk"
            return f"{hours} sa"
    
    @staticmethod
    def format_duration_short(seconds: float) -> str:
        """
        Kısa format: "1:30" veya "01:05:30"
        """
        if seconds < 0:
            return "0:00"
        
        seconds = int(seconds)
        
        if seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"


class MultiStepETA:
    """
    Çoklu adımlı işlemler için ETA hesaplayıcı.
    
    Kullanım:
        eta = MultiStepETA([
            ("İndirme", 24),      # 24 dosya indirilecek
            ("AI İşleme", 24),    # 24 görüntü işlenecek
            ("3D Oluşturma", 1),  # 1 model oluşturulacak
        ])
        
        # Adım 1
        eta.start_step(0)
        for i in range(24):
            download_file(i)
            print(eta.update_step(0, i+1))
        
        # Adım 2
        eta.start_step(1)
        ...
    """
    
    def __init__(self, steps: list):
        """
        Args:
            steps: [(name, item_count), ...] formatında adımlar
        """
        self.steps = steps
        self.calculators = [ETACalculator() for _ in steps]
        self.step_times = [0.0] * len(steps)  # Her adımın gerçek süresi
        self.current_step = -1
    
    def start_step(self, step_index: int):
        """Adımı başlat"""
        self.current_step = step_index
        _, item_count = self.steps[step_index]
        self.calculators[step_index].start(item_count)
    
    def update_step(self, step_index: int, completed: int) -> str:
        """
        Adım ilerlemesini güncelle.
        
        Returns:
            Format: "Adım 2/3: AI İşleme - 45% (~2 dk kaldı)"
        """
        calc = self.calculators[step_index]
        info = calc.update(completed)
        
        step_name, _ = self.steps[step_index]
        step_num = step_index + 1
        total_steps = len(self.steps)
        
        remaining = ETACalculator.format_duration(info.remaining_seconds)
        
        return f"Adım {step_num}/{total_steps}: {step_name} - {info.progress_percent:.0f}% (~{remaining} kaldı)"
    
    def complete_step(self, step_index: int):
        """Adımı tamamla"""
        calc = self.calculators[step_index]
        self.step_times[step_index] = calc.get_elapsed()
    
    def get_total_remaining(self) -> float:
        """Tüm kalan süre tahmini"""
        remaining = 0.0
        
        for i, calc in enumerate(self.calculators):
            if i < self.current_step:
                # Tamamlanmış adım - atla
                continue
            elif i == self.current_step:
                # Mevcut adım - kalan süresini ekle
                remaining += calc.get_remaining()
            else:
                # Gelecek adım - tahmin yap
                # Önceki adımların ortalamasını kullan
                completed_times = [t for t in self.step_times[:i] if t > 0]
                if completed_times:
                    avg_time = sum(completed_times) / len(completed_times)
                    remaining += avg_time
                else:
                    # Varsayılan tahmin: adım başına 60 saniye
                    remaining += 60
        
        return remaining
    
    def get_overall_progress(self) -> float:
        """Genel ilerleme yüzdesi"""
        total_items = sum(count for _, count in self.steps)
        completed_items = 0
        
        for i, calc in enumerate(self.calculators):
            if i < self.current_step:
                _, count = self.steps[i]
                completed_items += count
            elif i == self.current_step:
                completed_items += calc.completed_items
        
        return (completed_items / total_items * 100) if total_items > 0 else 0
