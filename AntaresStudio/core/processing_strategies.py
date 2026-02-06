from __future__ import annotations

import gc
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import numpy as np
import cv2


class Mode(str, Enum):
    FAST = "fast"
    HQ = "hq"


# -------------------------
# Background Removal
# -------------------------
class BackgroundRemover:
    def remove(self, bgr: np.ndarray) -> np.ndarray:
        """
        Returns RGBA image (alpha=0 background).
        """
        raise NotImplementedError


class GrabCutRemover(BackgroundRemover):
    def __init__(self, margin: float = 0.06, iter_count: int = 2):
        self.margin = margin
        self.iter_count = iter_count

    def remove(self, bgr: np.ndarray) -> np.ndarray:
        h, w = bgr.shape[:2]
        mx, my = int(w * self.margin), int(h * self.margin)
        rect = (mx, my, max(1, w - 2 * mx), max(1, h - 2 * my))

        mask = np.zeros((h, w), np.uint8)
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)

        cv2.grabCut(bgr, mask, rect, bgd, fgd, self.iter_count, cv2.GC_INIT_WITH_RECT)
        fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")

        rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = fg_mask
        return rgba


class RembgRemover(BackgroundRemover):
    def __init__(self):
        try:
            from rembg import remove  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "rembg import edilemedi. FAST mode kullan veya rembg/onnxruntime kurulumunu düzelt."
            ) from e
        self._remove = remove

    def remove(self, bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        out = self._remove(rgb)  # returns bytes or ndarray depending on version
        if isinstance(out, bytes):
            arr = np.frombuffer(out, dtype=np.uint8)
            rgba = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        else:
            rgba = out
        if rgba.shape[2] == 3:
            rgba = cv2.cvtColor(rgba, cv2.COLOR_RGB2BGRA)
        return rgba


# -------------------------
# Feature Extraction
# -------------------------
class FeatureAlgo(str, Enum):
    SIFT = "sift"
    ORB = "orb"
    AKAZE = "akaze"


@dataclass(frozen=True)
class FeatureConfig:
    algo: FeatureAlgo
    max_features: int = 4000


def create_detector(cfg: FeatureConfig):
    if cfg.algo == FeatureAlgo.SIFT:
        # requires opencv-contrib-python
        return cv2.SIFT_create(nfeatures=cfg.max_features)
    if cfg.algo == FeatureAlgo.AKAZE:
        return cv2.AKAZE_create()
    return cv2.ORB_create(nfeatures=cfg.max_features)


def gc_aggressive():
    gc.collect()


def to_gray(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def choose_feature_algo(mode: Mode, need_speed: bool) -> FeatureAlgo:
    if mode == Mode.FAST:
        return FeatureAlgo.ORB
    # HQ: default SIFT; ama hız gerekirse AKAZE fallback
    return FeatureAlgo.AKAZE if need_speed else FeatureAlgo.SIFT


def choose_bg_remover(mode: Mode) -> BackgroundRemover:
    return GrabCutRemover() if mode == Mode.FAST else RembgRemover()
