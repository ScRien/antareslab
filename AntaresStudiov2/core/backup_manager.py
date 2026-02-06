"""
ANTARES 3D Studio - Backup Manager Module
Yerel yedekleme sistemi

Projeleri otomatik veya manuel olarak yedekler.
JSON metadata + folder yapısı kullanır.
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class BackupInfo:
    """Yedek bilgisi"""
    backup_path: Path
    project_id: str
    project_name: str
    created_at: datetime
    size_mb: float
    
    @property
    def filename(self) -> str:
        return self.backup_path.name
    
    @property
    def age_days(self) -> int:
        delta = datetime.now() - self.created_at
        return delta.days


class BackupManager:
    """
    Yerel yedekleme sistemi.
    
    Özellikler:
    - Manuel yedekleme
    - Otomatik yedekleme (işlem sonrası)
    - Yedekten geri yükleme
    - Eski yedekleri temizleme
    
    Kullanım:
        backup_manager = BackupManager()
        
        # Yedekle
        backup_path = backup_manager.create_backup(project)
        
        # Yedekleri listele
        backups = backup_manager.list_backups(project_id="a1b2c3d4")
        
        # Geri yükle
        restored_path = backup_manager.restore_backup(backup_path)
    """
    
    DEFAULT_BACKUP_DIR = Path.home() / "ANTARES_Backups"
    MAX_BACKUPS_PER_PROJECT = 5
    BACKUP_FILENAME_FORMAT = "{project_name}_{timestamp}.zip"
    
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or self.DEFAULT_BACKUP_DIR
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Yedek dizininin var olduğundan emin ol"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_project_backup_dir(self, project_id: str) -> Path:
        """Proje için yedek dizini"""
        backup_path = self.backup_dir / project_id
        backup_path.mkdir(parents=True, exist_ok=True)
        return backup_path
    
    def _generate_backup_filename(self, project_name: str) -> str:
        """Yedek dosya adı oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(project_name)
        return f"{safe_name}_{timestamp}.zip"
    
    def _sanitize_filename(self, name: str) -> str:
        """Güvenli dosya adı oluştur"""
        replacements = {
            'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        for tr, en in replacements.items():
            name = name.replace(tr, en)
        
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        name = ''.join(c if c in valid_chars else '_' for c in name)
        
        while '__' in name:
            name = name.replace('__', '_')
        
        return name.strip('_') or "backup"
    
    # ==================== YEDEKLEME ====================
    
    def create_backup(
        self,
        project_dir: Path,
        project_id: str,
        project_name: str,
        include_output: bool = True,
        compression_level: int = 6
    ) -> Optional[Path]:
        """
        Proje yedeği oluştur.
        
        Args:
            project_dir: Proje klasörü yolu
            project_id: Proje ID'si
            project_name: Proje adı
            include_output: 3D çıktı dosyalarını dahil et
            compression_level: Sıkıştırma seviyesi (1-9)
            
        Returns:
            Yedek dosya yolu veya None
        """
        if not project_dir.exists():
            return None
        
        # Yedek dizini
        backup_project_dir = self._get_project_backup_dir(project_id)
        
        # Dosya adı
        backup_filename = self._generate_backup_filename(project_name)
        backup_path = backup_project_dir / backup_filename
        
        try:
            with zipfile.ZipFile(
                backup_path, 
                'w', 
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=compression_level
            ) as zf:
                for file_path in project_dir.rglob('*'):
                    if file_path.is_file():
                        # Output klasörünü atla (istenirse)
                        if not include_output and 'output' in file_path.parts:
                            continue
                        
                        # Göreceli yol
                        arcname = file_path.relative_to(project_dir)
                        zf.write(file_path, arcname)
            
            # Eski yedekleri temizle
            self.cleanup_old_backups(project_id)
            
            return backup_path
            
        except Exception as e:
            # Hatalı yedek dosyasını sil
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def create_quick_backup(self, project_dir: Path, project_id: str, project_name: str) -> Optional[Path]:
        """
        Hızlı yedek (sadece metadata ve görüntüler, output hariç).
        
        Kullanım: İşlem öncesi güvenlik yedeği
        """
        return self.create_backup(
            project_dir=project_dir,
            project_id=project_id,
            project_name=project_name,
            include_output=False,
            compression_level=1  # Hızlı sıkıştırma
        )
    
    # ==================== GERİ YÜKLEME ====================
    
    def restore_backup(
        self,
        backup_path: Path,
        restore_dir: Path = None,
        overwrite: bool = False
    ) -> Optional[Path]:
        """
        Yedekten geri yükle.
        
        Args:
            backup_path: Yedek ZIP dosyası
            restore_dir: Geri yükleme hedef dizini (None = orijinal konum)
            overwrite: Varsa üzerine yaz
            
        Returns:
            Geri yüklenen proje dizini veya None
        """
        if not backup_path.exists():
            return None
        
        try:
            # Hedef dizini belirle
            if restore_dir is None:
                # ZIP içinden project.json oku, orijinal konumu bul
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    if 'project.json' in zf.namelist():
                        import json
                        with zf.open('project.json') as pf:
                            project_data = json.load(pf)
                            restore_dir = Path(project_data.get('project_dir', ''))
                    else:
                        return None
            
            if restore_dir.exists() and not overwrite:
                # Çakışma - yeni isim ver
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                restore_dir = restore_dir.parent / f"{restore_dir.name}_restored_{timestamp}"
            
            # Çıkar
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(restore_dir)
            
            # project.json güncelle (yeni dizin yolu)
            metadata_path = restore_dir / 'project.json'
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                project_data['project_dir'] = str(restore_dir)
                project_data['updated_at'] = datetime.now().isoformat()
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            return restore_dir
            
        except Exception:
            return None
    
    # ==================== LİSTELEME ====================
    
    def list_backups(self, project_id: str = None) -> List[BackupInfo]:
        """
        Yedekleri listele.
        
        Args:
            project_id: Belirli projenin yedekleri (None = tümü)
            
        Returns:
            Yedek bilgileri listesi
        """
        backups = []
        
        if project_id:
            search_dirs = [self._get_project_backup_dir(project_id)]
        else:
            search_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir()]
        
        for backup_dir in search_dirs:
            for backup_file in backup_dir.glob('*.zip'):
                try:
                    # Dosya bilgilerini al
                    stat = backup_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    created_at = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Proje bilgilerini ZIP'ten oku
                    proj_id = backup_dir.name
                    proj_name = backup_file.stem.rsplit('_', 2)[0]  # timestamp'i çıkar
                    
                    backups.append(BackupInfo(
                        backup_path=backup_file,
                        project_id=proj_id,
                        project_name=proj_name,
                        created_at=created_at,
                        size_mb=round(size_mb, 2)
                    ))
                except Exception:
                    continue
        
        # Tarihe göre sırala (yeniden eskiye)
        backups.sort(key=lambda b: b.created_at, reverse=True)
        
        return backups
    
    def get_latest_backup(self, project_id: str) -> Optional[BackupInfo]:
        """Projenin en son yedeğini getir"""
        backups = self.list_backups(project_id)
        return backups[0] if backups else None
    
    # ==================== TEMİZLİK ====================
    
    def cleanup_old_backups(self, project_id: str, keep_count: int = None) -> int:
        """
        Eski yedekleri temizle.
        
        Args:
            project_id: Proje ID'si
            keep_count: Tutulacak yedek sayısı
            
        Returns:
            Silinen yedek sayısı
        """
        keep_count = keep_count or self.MAX_BACKUPS_PER_PROJECT
        
        backups = self.list_backups(project_id)
        
        if len(backups) <= keep_count:
            return 0
        
        # Silinecek yedekler (en eskiler)
        to_delete = backups[keep_count:]
        
        deleted_count = 0
        for backup in to_delete:
            try:
                backup.backup_path.unlink()
                deleted_count += 1
            except Exception:
                continue
        
        return deleted_count
    
    def cleanup_all_old_backups(self, keep_count: int = None) -> Dict[str, int]:
        """
        Tüm projelerin eski yedeklerini temizle.
        
        Returns:
            {project_id: silinen_sayısı} sözlüğü
        """
        result = {}
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                project_id = backup_dir.name
                deleted = self.cleanup_old_backups(project_id, keep_count)
                if deleted > 0:
                    result[project_id] = deleted
        
        return result
    
    def delete_backup(self, backup_path: Path) -> bool:
        """Belirli bir yedeği sil"""
        try:
            if backup_path.exists():
                backup_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    # ==================== İSTATİSTİKLER ====================
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Yedekleme istatistikleri.
        
        Returns:
            İstatistik sözlüğü
        """
        all_backups = self.list_backups()
        
        if not all_backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'projects_with_backups': 0,
                'oldest_backup': None,
                'newest_backup': None
            }
        
        total_size = sum(b.size_mb for b in all_backups)
        unique_projects = len(set(b.project_id for b in all_backups))
        
        return {
            'total_backups': len(all_backups),
            'total_size_mb': round(total_size, 2),
            'projects_with_backups': unique_projects,
            'oldest_backup': min(all_backups, key=lambda b: b.created_at).created_at.isoformat(),
            'newest_backup': max(all_backups, key=lambda b: b.created_at).created_at.isoformat()
        }
    
    def get_backup_size(self, project_id: str = None) -> float:
        """
        Toplam yedek boyutu (MB).
        
        Args:
            project_id: Belirli proje (None = tümü)
        """
        backups = self.list_backups(project_id)
        return sum(b.size_mb for b in backups)
