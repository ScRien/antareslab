from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import cv2

from .processing_strategies import Mode, choose_bg_remover, choose_feature_algo, FeatureConfig
from .reconstruction import reconstruct_sparse


@dataclass(frozen=True)
class PipelineInput:
    image_paths: list[Path]
    output_dir: Path


def run_pipeline(
    inp: PipelineInput,
    *,
    mode: Mode,
    progress_cb: Optional[Callable[[float], None]] = None,
    message_cb: Optional[Callable[[str], None]] = None,
    cancel_event=None
):
    if message_cb:
        message_cb("Görseller yükleniyor...")
    bgr_images = []
    for p in inp.image_paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Görsel okunamadı: {p}")
        bgr_images.append(img)

    # (Opsiyonel) background removal burada uygulanabilir:
    # remover = choose_bg_remover(mode)
    # ...

    if message_cb:
        message_cb("3D rekonstrüksiyon başlıyor...")
    return reconstruct_sparse(
        bgr_images,
        inp.output_dir,
        mode=mode,
        progress_cb=progress_cb,
        message_cb=message_cb,
        cancel_event=cancel_event,
    )
