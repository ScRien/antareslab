"""
ANTARES 3D Studio - Birim Testleri
Core modüller için testler
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Modülleri import et
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    SafeOperation, OperationResult, OperationStatus,
    PreFlightChecker, CheckStatus,
    ProjectManager, ProjectStatus, ArtifactType,
    BackupManager
)


class TestSafeOperation(unittest.TestCase):
    """SafeOperation testleri"""
    
    def test_successful_operation(self):
        """Başarılı işlem testi"""
        def success_func(x, y):
            return x + y
        
        result = SafeOperation.execute(success_func, args=(5, 3))
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, 8)
        self.assertIsNone(result.error)
    
    def test_failed_operation(self):
        """Hatalı işlem testi"""
        def fail_func():
            raise ValueError("Test hatası")
        
        result = SafeOperation.execute(fail_func)
        
        self.assertFalse(result.success)
        self.assertIn("Test hatası", result.error_message)
        self.assertEqual(result.status, OperationStatus.FAILED)
    
    def test_with_fallback(self):
        """Fallback değer testi"""
        def fail_func():
            raise Exception("Hata")
        
        result = SafeOperation.execute(fail_func, fallback_value="default")
        
        self.assertFalse(result.success)
        self.assertEqual(result.data, "default")


class TestPreFlightChecker(unittest.TestCase):
    """PreFlightChecker testleri"""
    
    def setUp(self):
        self.checker = PreFlightChecker()
    
    def test_disk_space_check(self):
        """Disk alanı kontrolü testi"""
        result = self.checker.check_disk_space(".", required_mb=1)
        
        # En az 1MB boş alan olmalı
        self.assertEqual(result.status, CheckStatus.PASSED)
    
    def test_output_directory_check(self):
        """Çıktı dizini kontrolü testi"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.checker.check_output_directory(tmpdir)
            self.assertEqual(result.status, CheckStatus.PASSED)
    
    def test_dependencies_check(self):
        """Bağımlılık kontrolü testi"""
        result = self.checker.check_dependencies()
        
        # En azından bazı kütüphaneler yüklü olmalı
        self.assertIn(result.status, [CheckStatus.PASSED, CheckStatus.WARNING])


class TestProjectManager(unittest.TestCase):
    """ProjectManager testleri"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = ProjectManager(Path(self.test_dir))
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_project(self):
        """Proje oluşturma testi"""
        project = self.manager.create_project(
            name="Test Projesi",
            artifact_type="seramik",
            excavation_site="Test Alanı"
        )
        
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "Test Projesi")
        self.assertEqual(project.artifact_type, "seramik")
        self.assertTrue(project.project_dir.exists())
    
    def test_load_project(self):
        """Proje yükleme testi"""
        # Önce oluştur
        project = self.manager.create_project(name="Yüklenecek Proje")
        project_id = project.id
        
        # Sonra yükle
        loaded = self.manager.load_project(project_id)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Yüklenecek Proje")
        self.assertEqual(loaded.id, project_id)
    
    def test_list_projects(self):
        """Proje listeleme testi"""
        # Birkaç proje oluştur
        self.manager.create_project(name="Proje 1")
        self.manager.create_project(name="Proje 2")
        self.manager.create_project(name="Proje 3")
        
        projects = self.manager.list_projects()
        
        self.assertEqual(len(projects), 3)
    
    def test_delete_project(self):
        """Proje silme testi"""
        project = self.manager.create_project(name="Silinecek Proje")
        project_id = project.id
        
        success = self.manager.delete_project(project_id, confirm=True)
        
        self.assertTrue(success)
        self.assertIsNone(self.manager.load_project(project_id))
    
    def test_update_project(self):
        """Proje güncelleme testi"""
        project = self.manager.create_project(name="Eski İsim")
        project.name = "Yeni İsim"
        
        self.manager.save_project(project)
        
        loaded = self.manager.load_project(project.id)
        self.assertEqual(loaded.name, "Yeni İsim")


class TestBackupManager(unittest.TestCase):
    """BackupManager testleri"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = tempfile.mkdtemp()
        self.manager = BackupManager(Path(self.backup_dir))
        
        # Test proje dizini oluştur
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()
        
        # Bazı dosyalar oluştur
        (self.project_dir / "project.json").write_text('{"name": "Test"}')
        (self.project_dir / "test.txt").write_text("Test içerik")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.backup_dir, ignore_errors=True)
    
    def test_create_backup(self):
        """Yedek oluşturma testi"""
        backup_path = self.manager.create_backup(
            project_dir=self.project_dir,
            project_id="test123",
            project_name="Test Proje"
        )
        
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.suffix == ".zip")
    
    def test_list_backups(self):
        """Yedek listeleme testi"""
        # Birkaç yedek oluştur
        self.manager.create_backup(self.project_dir, "proj1", "Proje 1")
        self.manager.create_backup(self.project_dir, "proj1", "Proje 1")
        
        backups = self.manager.list_backups("proj1")
        
        self.assertGreaterEqual(len(backups), 1)
    
    def test_restore_backup(self):
        """Yedekten geri yükleme testi"""
        # Yedek oluştur
        backup_path = self.manager.create_backup(
            self.project_dir, "test123", "Test"
        )
        
        # Orijinali sil
        shutil.rmtree(self.project_dir)
        
        # Geri yükle
        restore_dir = Path(self.test_dir) / "restored"
        restored = self.manager.restore_backup(backup_path, restore_dir)
        
        self.assertIsNotNone(restored)
        self.assertTrue((restored / "test.txt").exists())


class TestIntegration(unittest.TestCase):
    """Entegrasyon testleri"""
    
    def test_full_workflow(self):
        """Tam iş akışı testi"""
        test_dir = tempfile.mkdtemp()
        
        try:
            # 1. Proje oluştur
            pm = ProjectManager(Path(test_dir) / "projects")
            project = pm.create_project(
                name="Entegrasyon Testi",
                artifact_type="seramik"
            )
            
            # 2. Pre-flight kontrol
            checker = PreFlightChecker()
            report = checker.run_download_preflight(
                esp32_ip="192.168.4.1",
                output_dir=str(project.images_dir)
            )
            
            # Bağlantı olmadığı için başarısız olabilir
            self.assertIsNotNone(report)
            
            # 3. Yedekleme
            bm = BackupManager(Path(test_dir) / "backups")
            backup = bm.create_backup(
                project.project_dir,
                project.id,
                project.name
            )
            
            self.assertIsNotNone(backup)
            
            # 4. Projeyi listele
            projects = pm.list_projects()
            self.assertEqual(len(projects), 1)
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    # Test çalıştır
    print("=" * 60)
    print("ANTARES 3D Studio - Birim Testleri")
    print("=" * 60)
    print()
    
    unittest.main(verbosity=2)
