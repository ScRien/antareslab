"""
ANTARES 3D Studio - Utils Testleri
Yardımcı modüller için testler
"""

import unittest
import sys
import os
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    ImageQualityAnalyzer, QualityLevel,
    ETACalculator, MultiStepETA,
    NotificationManager, NotificationType
)


class TestImageQualityAnalyzer(unittest.TestCase):
    """ImageQualityAnalyzer testleri"""
    
    def setUp(self):
        self.analyzer = ImageQualityAnalyzer()
        
        # Test görüntüsü oluştur
        self.test_dir = tempfile.mkdtemp()
        self.test_image = self._create_test_image()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_image(self) -> str:
        """Test için basit görüntü oluştur"""
        try:
            import cv2
            import numpy as np
            
            # 640x480 gri görüntü
            img = np.random.randint(100, 200, (480, 640, 3), dtype=np.uint8)
            
            path = os.path.join(self.test_dir, "test.jpg")
            cv2.imwrite(path, img)
            
            return path
        except ImportError:
            return None
    
    def test_analyze_single_image(self):
        """Tek görüntü analizi testi"""
        if not self.test_image:
            self.skipTest("OpenCV yüklü değil")
        
        result = self.analyzer.analyze(self.test_image)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.blur_score >= 0)
        self.assertTrue(0 <= result.brightness <= 255)
        self.assertTrue(0 <= result.light_uniformity <= 1)
    
    def test_analyze_nonexistent_image(self):
        """Olmayan görüntü testi"""
        result = self.analyzer.analyze("/nonexistent/path.jpg")
        
        self.assertFalse(result.is_acceptable)
        self.assertEqual(result.quality_level, QualityLevel.REJECTED.value)
    
    def test_analyze_batch(self):
        """Toplu analiz testi"""
        if not self.test_image:
            self.skipTest("OpenCV yüklü değil")
        
        # Birden fazla kopyası oluştur
        import shutil
        images = [self.test_image]
        
        for i in range(3):
            new_path = os.path.join(self.test_dir, f"test_{i}.jpg")
            shutil.copy(self.test_image, new_path)
            images.append(new_path)
        
        report = self.analyzer.analyze_batch(images)
        
        self.assertEqual(report.total_images, 4)
        self.assertEqual(report.analyzed_images, 4)


class TestETACalculator(unittest.TestCase):
    """ETACalculator testleri"""
    
    def test_basic_eta(self):
        """Temel ETA hesaplama testi"""
        eta = ETACalculator()
        eta.start(total_items=100)
        
        # Simüle edilmiş ilerleme
        time.sleep(0.1)
        info = eta.update(10)
        
        self.assertEqual(info.progress_percent, 10.0)
        self.assertGreater(info.elapsed_seconds, 0)
    
    def test_format_duration_seconds(self):
        """Saniye formatı testi"""
        result = ETACalculator.format_duration(45)
        self.assertEqual(result, "45 sn")
    
    def test_format_duration_minutes(self):
        """Dakika formatı testi"""
        result = ETACalculator.format_duration(125)
        self.assertEqual(result, "2 dk 5 sn")
    
    def test_format_duration_hours(self):
        """Saat formatı testi"""
        result = ETACalculator.format_duration(3700)
        self.assertEqual(result, "1 sa 1 dk")
    
    def test_format_duration_short(self):
        """Kısa format testi"""
        result = ETACalculator.format_duration_short(90)
        self.assertEqual(result, "1:30")
    
    def test_progress_text(self):
        """İlerleme metni testi"""
        eta = ETACalculator()
        eta.start(10)
        eta.update(5)
        
        text = eta.get_progress_text()
        
        self.assertIn("50%", text)
        self.assertIn("5/10", text)


class TestMultiStepETA(unittest.TestCase):
    """MultiStepETA testleri"""
    
    def test_multi_step_progress(self):
        """Çoklu adım ilerleme testi"""
        steps = [
            ("İndirme", 10),
            ("İşleme", 20),
            ("Kaydetme", 5)
        ]
        
        eta = MultiStepETA(steps)
        
        # Adım 1
        eta.start_step(0)
        for i in range(10):
            status = eta.update_step(0, i + 1)
        eta.complete_step(0)
        
        self.assertIn("1/3", status)
        self.assertIn("İndirme", status)
    
    def test_overall_progress(self):
        """Genel ilerleme testi"""
        steps = [
            ("A", 10),
            ("B", 10)
        ]
        
        eta = MultiStepETA(steps)
        eta.start_step(0)
        eta.update_step(0, 10)
        eta.complete_step(0)
        
        progress = eta.get_overall_progress()
        self.assertEqual(progress, 50.0)


class TestNotificationManager(unittest.TestCase):
    """NotificationManager testleri"""
    
    def setUp(self):
        self.notifier = NotificationManager("Test App")
    
    def test_sounds_toggle(self):
        """Ses ayarı testi"""
        self.notifier.set_sounds_enabled(False)
        self.assertFalse(self.notifier.sounds_enabled)
        
        self.notifier.set_sounds_enabled(True)
        self.assertTrue(self.notifier.sounds_enabled)
    
    def test_notifications_toggle(self):
        """Bildirim ayarı testi"""
        self.notifier.set_notifications_enabled(False)
        self.assertFalse(self.notifier.notifications_enabled)
    
    def test_callback_registration(self):
        """Callback kayıt testi"""
        callback_called = [False]
        
        def test_callback(title, message):
            callback_called[0] = True
        
        self.notifier.register_callback(NotificationType.SUCCESS, test_callback)
        
        # Bildirimi tetikle (toast olmadan)
        self.notifier.notifications_enabled = False
        self.notifier.sounds_enabled = False
        self.notifier.notify("Test", "Mesaj", NotificationType.SUCCESS)
        
        self.assertTrue(callback_called[0])


if __name__ == "__main__":
    print("=" * 60)
    print("ANTARES 3D Studio - Utils Testleri")
    print("=" * 60)
    print()
    
    unittest.main(verbosity=2)
