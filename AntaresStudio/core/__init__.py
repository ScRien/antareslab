"""
ANTARES 3D Studio - Core Module
Çekirdek modüller

Bu paket uygulamanın temel işlevselliğini sağlar.
"""

# Safe Operation - Hata yönetimi ve güvenli işlem yürütme
from .safe_operation import (
    SafeOperation,
    CancellableThread,
    OperationResult,
    OperationStatus,
    OperationQueue
)

# Pre-Flight Checker - İşlem öncesi kontroller
from .preflight_checker import (
    PreFlightChecker,
    CheckResult,
    CheckStatus,
    PreFlightReport
)

# Project Manager - Proje yönetimi
from .project_manager import (
    ProjectManager,
    AntaresProject,
    ProjectStatus,
    ArtifactType
)

# Backup Manager - Yedekleme sistemi
from .backup_manager import (
    BackupManager,
    BackupInfo
)


__all__ = [
    # Safe Operation
    'SafeOperation',
    'CancellableThread',
    'OperationResult',
    'OperationStatus',
    'OperationQueue',
    
    # Pre-Flight Checker
    'PreFlightChecker',
    'CheckResult',
    'CheckStatus',
    'PreFlightReport',
    
    # Project Manager
    'ProjectManager',
    'AntaresProject',
    'ProjectStatus',
    'ArtifactType',
    
    # Backup Manager
    'BackupManager',
    'BackupInfo',
]
