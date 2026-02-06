"""
ANTARES 3D Studio - Analysis Module
Analiz modülleri

Bu paket 3D modeller üzerinde analiz işlevleri sağlar.
"""

# Deterioration Analyzer - Bozulma/değişim analizi
from .deterioration_analyzer import (
    DeteriorationAnalyzer,
    DeteriorationResult,
    DeteriorationLevel,
    ReferenceObject,
    is_open3d_available
)


__all__ = [
    # Deterioration Analyzer
    'DeteriorationAnalyzer',
    'DeteriorationResult',
    'DeteriorationLevel',
    'ReferenceObject',
    'is_open3d_available',
]
