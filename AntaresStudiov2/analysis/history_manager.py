"""
ANTARES 3D Studio - Analysis History Manager
Analiz sonuçlarını kaydetme ve yükleme
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class AnalysisRecord:
    """Tek bir analiz kaydı"""
    id: str
    timestamp: str
    baseline_path: str
    current_path: str
    overall_change: float
    volume_change: float
    area_change: float
    icp_fitness: float
    deterioration_level: str
    warnings: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisRecord':
        return cls(
            id=data.get('id', ''),
            timestamp=data.get('timestamp', ''),
            baseline_path=data.get('baseline_path', ''),
            current_path=data.get('current_path', ''),
            overall_change=data.get('overall_change', 0.0),
            volume_change=data.get('volume_change', 0.0),
            area_change=data.get('area_change', 0.0),
            icp_fitness=data.get('icp_fitness', 0.0),
            deterioration_level=data.get('deterioration_level', 'none'),
            warnings=data.get('warnings', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_display_name(self) -> str:
        """Listede gösterilecek isim"""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return self.timestamp[:16]
    
    def get_level_badge(self) -> str:
        """Seviye badge metni"""
        levels = {
            "none": "Stabil",
            "minimal": "Minimal",
            "moderate": "Orta",
            "severe": "Ciddi",
            "critical": "Kritik"
        }
        return levels.get(self.deterioration_level, "?")


class AnalysisHistoryManager:
    """Analiz geçmişi yönetimi"""
    
    HISTORY_FILENAME = "analysis_history.json"
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self._history: List[AnalysisRecord] = []
        
        if self.project_dir:
            self._load_history()
    
    def set_project_dir(self, project_dir: Path):
        """Proje dizinini ayarla ve geçmişi yükle"""
        self.project_dir = project_dir
        self._load_history()
    
    def _get_history_path(self) -> Optional[Path]:
        """Geçmiş dosyası yolunu döndür"""
        if not self.project_dir:
            return None
        analysis_dir = Path(self.project_dir) / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        return analysis_dir / self.HISTORY_FILENAME
    
    def _load_history(self):
        """Geçmişi dosyadan yükle"""
        self._history = []
        
        path = self._get_history_path()
        if not path or not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for record_data in data.get('records', []):
                record = AnalysisRecord.from_dict(record_data)
                self._history.append(record)
        except Exception:
            pass
    
    def _save_history(self):
        """Geçmişi dosyaya kaydet"""
        path = self._get_history_path()
        if not path:
            return
        
        try:
            data = {
                'version': 1,
                'records': [r.to_dict() for r in self._history]
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add_record(self, result, baseline_path: str, current_path: str) -> AnalysisRecord:
        """Yeni analiz kaydı ekle"""
        record = AnalysisRecord(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            baseline_path=baseline_path,
            current_path=current_path,
            overall_change=result.overall_change_percent,
            volume_change=result.volume_change_percent,
            area_change=result.area_change_percent,
            icp_fitness=result.icp_fitness,
            deterioration_level=result.deterioration_level,
            warnings=result.warnings
        )
        
        self._history.insert(0, record)  # En yenisi başta
        self._save_history()
        
        return record
    
    def get_records(self) -> List[AnalysisRecord]:
        """Tüm kayıtları döndür (en yenisi başta)"""
        return self._history.copy()
    
    def get_record(self, record_id: str) -> Optional[AnalysisRecord]:
        """ID ile kayıt getir"""
        for record in self._history:
            if record.id == record_id:
                return record
        return None
    
    def delete_record(self, record_id: str) -> bool:
        """Kayıt sil"""
        for i, record in enumerate(self._history):
            if record.id == record_id:
                del self._history[i]
                self._save_history()
                return True
        return False
    
    def clear_history(self):
        """Tüm geçmişi temizle"""
        self._history = []
        self._save_history()
