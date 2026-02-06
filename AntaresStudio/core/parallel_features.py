from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
import numpy as np
import cv2

from joblib import Parallel, delayed

from .processing_strategies import FeatureConfig, create_detector, to_gray


@dataclass(frozen=True)
class Features:
    keypoints: list
    descriptors: Optional[np.ndarray]


def _extract_one(gray: np.ndarray, cfg: FeatureConfig) -> Features:
    det = create_detector(cfg)
    kp, des = det.detectAndCompute(gray, None)
    return Features(kp, des)


def extract_features_parallel(
    bgr_images: List[np.ndarray],
    cfg: FeatureConfig,
    *,
    n_jobs: int = -1,
    progress_cb: Optional[Callable[[float], None]] = None
) -> List[Features]:
    grays = [to_gray(img) for img in bgr_images]

    total = len(grays)
    done = 0

    def wrap(gray):
        nonlocal done
        out = _extract_one(gray, cfg)
        done += 1
        if progress_cb:
            progress_cb(100.0 * done / max(1, total))
        return out

    feats = Parallel(n_jobs=n_jobs, prefer="threads")(delayed(wrap)(g) for g in grays)
    return feats
