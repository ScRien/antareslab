"""
ANTARES 3D Studio - Project Manager Module
Proje yönetimi sistemi

Arkeolojik eserlerin tarama verilerini organize eder.
Her proje ayrı bir klasörde tutulur ve JSON metadata ile yönetilir.
"""

import os
import sys
import uuid
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ProjectStatus(Enum):
    """Proje durumu"""
    CREATED = "created"                    # Yeni oluşturuldu
    IMAGES_DOWNLOADING = "downloading"     # Görüntüler indiriliyor
    IMAGES_DOWNLOADED = "downloaded"       # Görüntüler indirildi
    PROCESSING = "processing"              # 3D işleme yapılıyor
    COMPLETED = "completed"                # Tamamlandı
    ERROR = "error"                        # Hata oluştu


class ArtifactType(Enum):
    """Eser türü"""
    CERAMIC = "seramik"
    METAL = "metal"
    GLASS = "cam"
    STONE = "taş"
    BONE = "kemik"
    WOOD = "ahşap"
    TEXTILE = "tekstil"
    COIN = "sikke"
    SCULPTURE = "heykel"
    OTHER = "diğer"


@dataclass
class AntaresProject:
    """
    Proje veri modeli.
    
    Her arkeolojik eser taraması bir proje olarak saklanır.
    """
    # Tanımlayıcılar
    id: str                                    # UUID (8 karakter)
    name: str                                  # "Seramik_Parçası_001"
    
    # Tarihler
    created_at: str                            # ISO format
    updated_at: str                            # ISO format
    
    # Eser bilgileri
    artifact_type: str = "diğer"               # Eser türü
    excavation_site: str = ""                  # Kazı alanı
    excavation_date: str = ""                  # Kazı tarihi
    inventory_number: str = ""                 # Envanter numarası
    
    # Klasör yolları (göreceli)
    project_dir: str = ""
    images_dir: str = "images"
    processed_dir: str = "processed"
    output_dir: str = "output"
    analysis_dir: str = "analysis"
    
    # Durum
    status: str = "created"
    image_count: int = 0
    
    # Çıktı dosyaları (göreceli yollar)
    point_cloud_path: str = ""
    mesh_path: str = ""
    
    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Kapsül verileri (Antares özel)
    capsule_session_id: str = ""               # ESP32 session ID
    capsule_temperature: float = 0.0           # Kazı anı sıcaklık
    capsule_humidity: float = 0.0              # Kazı anı nem
    
    # İstatistikler
    processing_time_seconds: float = 0.0
    model_vertices: int = 0
    model_triangles: int = 0
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Göreceli yolu mutlak yola çevir"""
        return Path(self.project_dir) / relative_path
    
    def get_images_path(self) -> Path:
        return self.get_absolute_path(self.images_dir)
    
    def get_processed_path(self) -> Path:
        return self.get_absolute_path(self.processed_dir)
    
    def get_output_path(self) -> Path:
        return self.get_absolute_path(self.output_dir)
    
    def get_analysis_path(self) -> Path:
        return self.get_absolute_path(self.analysis_dir)
    
    def to_dict(self) -> Dict[str, Any]:
        """Sözlüğe çevir (JSON serialization için)"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AntaresProject':
        """Sözlükten oluştur"""
        return cls(**data)
    
    def update_timestamp(self):
        """Güncelleme zamanını şimdiye ayarla"""
        self.updated_at = datetime.now().isoformat()


class ProjectManager:
    """
    Proje CRUD operasyonları.
    
    Kullanım:
        manager = ProjectManager()
        
        # Yeni proje oluştur
        project = manager.create_project(
            name="Seramik_Parçası_001",
            artifact_type="seramik",
            excavation_site="Efes Antik Kenti"
        )
        
        # Projeleri listele
        projects = manager.list_projects()
        
        # Proje yükle
        project = manager.load_project("a1b2c3d4")
        
        # Projeyi güncelle
        project.status = ProjectStatus.COMPLETED.value
        manager.save_project(project)
    """
    
    # Varsayılan projeler dizini
    DEFAULT_PROJECTS_DIR = Path.home() / "ANTARES_Projects"
    METADATA_FILENAME = "project.json"
    
    def __init__(self, projects_dir: Path = None):
        self.projects_dir = projects_dir or self.DEFAULT_PROJECTS_DIR
        self._ensure_projects_dir()
    
    def _ensure_projects_dir(self):
        """Projeler dizininin var olduğundan emin ol"""
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_project_path(self, project_id: str) -> Optional[Path]:
        """Proje ID'sinden klasör yolunu bul"""
        for folder in self.projects_dir.iterdir():
            if folder.is_dir() and folder.name.endswith(f"_{project_id}"):
                return folder
        return None
    
    def _save_metadata(self, project: AntaresProject):
        """Proje metadata'sını kaydet"""
        metadata_path = Path(project.project_dir) / self.METADATA_FILENAME
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_metadata(self, project_dir: Path) -> Optional[AntaresProject]:
        """Proje metadata'sını yükle"""
        metadata_path = project_dir / self.METADATA_FILENAME
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AntaresProject.from_dict(data)
        except Exception:
            return None
    
    # ==================== CRUD OPERASYONLARİ ====================
    
    def create_project(
        self,
        name: str,
        artifact_type: str = "diğer",
        excavation_site: str = "",
        excavation_date: str = "",
        inventory_number: str = "",
        notes: str = "",
        tags: List[str] = None,
        capsule_session_id: str = "",
        capsule_temperature: float = 0.0,
        capsule_humidity: float = 0.0
    ) -> AntaresProject:
        """
        Yeni proje oluştur.
        
        Args:
            name: Proje adı (örn: "Seramik_Parçası_001")
            artifact_type: Eser türü
            excavation_site: Kazı alanı
            excavation_date: Kazı tarihi
            inventory_number: Envanter numarası
            notes: Notlar
            tags: Etiketler
            capsule_session_id: ESP32 session ID
            capsule_temperature: Kazı anı sıcaklık (°C)
            capsule_humidity: Kazı anı nem (%)
            
        Returns:
            Oluşturulan AntaresProject
        """
        # Benzersiz ID oluştur
        project_id = str(uuid.uuid4())[:8]
        
        # Güvenli klasör adı oluştur
        safe_name = self._sanitize_filename(name)
        folder_name = f"{safe_name}_{project_id}"
        project_dir = self.projects_dir / folder_name
        
        # Klasör yapısını oluştur
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "images").mkdir(exist_ok=True)
        (project_dir / "processed").mkdir(exist_ok=True)
        (project_dir / "output").mkdir(exist_ok=True)
        (project_dir / "analysis").mkdir(exist_ok=True)
        (project_dir / "analysis" / "thumbnails").mkdir(exist_ok=True)
        
        # Proje nesnesi oluştur
        now = datetime.now().isoformat()
        project = AntaresProject(
            id=project_id,
            name=name,
            created_at=now,
            updated_at=now,
            artifact_type=artifact_type,
            excavation_site=excavation_site,
            excavation_date=excavation_date,
            inventory_number=inventory_number,
            project_dir=str(project_dir),
            status=ProjectStatus.CREATED.value,
            notes=notes,
            tags=tags or [],
            capsule_session_id=capsule_session_id,
            capsule_temperature=capsule_temperature,
            capsule_humidity=capsule_humidity
        )
        
        # Metadata kaydet
        self._save_metadata(project)
        
        return project
    
    def load_project(self, project_id: str) -> Optional[AntaresProject]:
        """
        Projeyi ID ile yükle.
        
        Args:
            project_id: Proje ID'si (8 karakter)
            
        Returns:
            AntaresProject veya None
        """
        project_path = self._get_project_path(project_id)
        
        if project_path is None:
            return None
        
        return self._load_metadata(project_path)
    
    def save_project(self, project: AntaresProject):
        """
        Proje değişikliklerini kaydet.
        
        Args:
            project: Güncellenmiş proje
        """
        project.update_timestamp()
        self._save_metadata(project)
    
    def delete_project(self, project_id: str, confirm: bool = False) -> bool:
        """
        Projeyi sil.
        
        Args:
            project_id: Silinecek proje ID'si
            confirm: Silme onayı (True olmalı)
            
        Returns:
            Başarılı mı?
        """
        if not confirm:
            return False
        
        project_path = self._get_project_path(project_id)
        
        if project_path is None:
            return False
        
        try:
            shutil.rmtree(project_path)
            return True
        except Exception:
            return False
    
    def list_projects(
        self,
        status: str = None,
        artifact_type: str = None,
        search: str = None,
        sort_by: str = "updated_at",
        reverse: bool = True
    ) -> List[AntaresProject]:
        """
        Tüm projeleri listele.
        
        Args:
            status: Durum filtresi (opsiyonel)
            artifact_type: Eser türü filtresi (opsiyonel)
            search: Arama terimi (ad veya notlarda)
            sort_by: Sıralama alanı
            reverse: Ters sıralama
            
        Returns:
            Proje listesi
        """
        projects = []
        
        for folder in self.projects_dir.iterdir():
            if not folder.is_dir():
                continue
            
            project = self._load_metadata(folder)
            if project is None:
                continue
            
            # Filtreler
            if status and project.status != status:
                continue
            
            if artifact_type and project.artifact_type != artifact_type:
                continue
            
            if search:
                search_lower = search.lower()
                if (search_lower not in project.name.lower() and
                    search_lower not in project.notes.lower() and
                    search_lower not in project.excavation_site.lower()):
                    continue
            
            projects.append(project)
        
        # Sıralama
        try:
            projects.sort(key=lambda p: getattr(p, sort_by, ""), reverse=reverse)
        except:
            pass
        
        return projects
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """
        Tüm projeler için istatistikler.
        
        Returns:
            İstatistik sözlüğü
        """
        projects = self.list_projects()
        
        if not projects:
            return {
                "total": 0,
                "by_status": {},
                "by_type": {},
                "total_images": 0,
                "total_size_mb": 0
            }
        
        # Durum bazında sayım
        by_status = {}
        for project in projects:
            status = project.status
            by_status[status] = by_status.get(status, 0) + 1
        
        # Tür bazında sayım
        by_type = {}
        for project in projects:
            atype = project.artifact_type
            by_type[atype] = by_type.get(atype, 0) + 1
        
        # Toplam görüntü sayısı
        total_images = sum(p.image_count for p in projects)
        
        # Toplam boyut
        total_size = 0
        for project in projects:
            try:
                project_path = Path(project.project_dir)
                if project_path.exists():
                    total_size += sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
            except:
                pass
        
        return {
            "total": len(projects),
            "by_status": by_status,
            "by_type": by_type,
            "total_images": total_images,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    # ==================== EXPORT/IMPORT ====================
    
    def export_project(self, project_id: str, output_path: Path) -> Optional[Path]:
        """
        Projeyi ZIP olarak dışa aktar.
        
        Args:
            project_id: Proje ID'si
            output_path: Çıktı ZIP dosyası yolu
            
        Returns:
            ZIP dosya yolu veya None
        """
        project = self.load_project(project_id)
        if project is None:
            return None
        
        project_path = Path(project.project_dir)
        
        try:
            # ZIP oluştur
            shutil.make_archive(
                str(output_path.with_suffix('')),
                'zip',
                project_path.parent,
                project_path.name
            )
            return output_path.with_suffix('.zip')
        except Exception:
            return None
    
    def import_project(self, zip_path: Path) -> Optional[AntaresProject]:
        """
        ZIP'ten proje içe aktar.
        
        Args:
            zip_path: ZIP dosya yolu
            
        Returns:
            İçe aktarılan proje veya None
        """
        try:
            import zipfile
            
            # Geçici dizine çıkar
            temp_dir = self.projects_dir / f"_import_temp_{uuid.uuid4().hex[:8]}"
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
            
            # project.json'u bul
            metadata_files = list(temp_dir.rglob(self.METADATA_FILENAME))
            
            if not metadata_files:
                shutil.rmtree(temp_dir)
                return None
            
            # Proje klasörünü bul
            project_folder = metadata_files[0].parent
            
            # Yeni ID ver (çakışma önleme)
            project = self._load_metadata(project_folder)
            if project is None:
                shutil.rmtree(temp_dir)
                return None
            
            new_id = str(uuid.uuid4())[:8]
            new_folder_name = f"{self._sanitize_filename(project.name)}_{new_id}"
            new_project_path = self.projects_dir / new_folder_name
            
            # Taşı
            shutil.move(str(project_folder), str(new_project_path))
            
            # Temp'i temizle
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            # Metadata güncelle
            project.id = new_id
            project.project_dir = str(new_project_path)
            project.update_timestamp()
            self._save_metadata(project)
            
            return project
            
        except Exception:
            return None
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _sanitize_filename(self, name: str) -> str:
        """Güvenli dosya adı oluştur"""
        # Türkçe karakterleri dönüştür
        replacements = {
            'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        
        for tr, en in replacements.items():
            name = name.replace(tr, en)
        
        # Geçersiz karakterleri kaldır
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        name = ''.join(c if c in valid_chars else '_' for c in name)
        
        # Çoklu alt çizgileri tek yap
        while '__' in name:
            name = name.replace('__', '_')
        
        # Baştaki ve sondaki alt çizgileri kaldır
        name = name.strip('_')
        
        return name or "proje"
    
    def get_recent_projects(self, count: int = 5) -> List[AntaresProject]:
        """Son kullanılan projeleri getir"""
        projects = self.list_projects(sort_by="updated_at", reverse=True)
        return projects[:count]
    
    def duplicate_project(self, project_id: str, new_name: str = None) -> Optional[AntaresProject]:
        """
        Projeyi kopyala (görüntüler hariç).
        
        Args:
            project_id: Kaynak proje ID'si
            new_name: Yeni proje adı
            
        Returns:
            Yeni proje veya None
        """
        source_project = self.load_project(project_id)
        if source_project is None:
            return None
        
        # Yeni proje oluştur
        new_project = self.create_project(
            name=new_name or f"{source_project.name}_kopya",
            artifact_type=source_project.artifact_type,
            excavation_site=source_project.excavation_site,
            excavation_date=source_project.excavation_date,
            inventory_number=source_project.inventory_number,
            notes=source_project.notes,
            tags=source_project.tags.copy()
        )
        
        return new_project
