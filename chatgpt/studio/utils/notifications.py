from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PyQt6.QtWidgets import QMessageBox


@dataclass(frozen=True)
class FriendlyError:
    title: str
    message: str
    hint: Optional[str] = None
    details: Optional[str] = None


def classify_error(short: str, details: str | None = None) -> FriendlyError:
    s = (short or "").lower()

    if "connection" in s or "timeout" in s or "wifi" in s:
        return FriendlyError(
            title="Bağlantı sorunu",
            message="ESP32-CAM ile bağlantı kurulamadı veya koptu.",
            hint="WiFi ağı/IP doğru mu? ESP32 AP modunda mısın? Aynı ağa bağlı mısın?",
            details=details,
        )
    if "open3d" in s or "glfw" in s:
        return FriendlyError(
            title="3D görüntüleyici sorunu",
            message="Open3D penceresi başlatılamadı.",
            hint="Ekran kartı sürücülerini kontrol et veya harici viewer modunu kullan.",
            details=details,
        )
    if "rembg" in s or "onnx" in s:
        return FriendlyError(
            title="Arka plan kaldırma sorunu",
            message="rembg/onnxruntime çalışmadı.",
            hint="FAST mod (GrabCut) kullan veya rembg + onnxruntime kurulumunu düzelt.",
            details=details,
        )

    return FriendlyError(
        title="Beklenmeyen hata",
        message=short,
        hint="Log detayını geliştiriciye gönder.",
        details=details,
    )


def show_error(parent, err: FriendlyError) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(err.title)
    text = err.message
    if err.hint:
        text += f"\n\nÖneri: {err.hint}"
    box.setText(text)
    if err.details:
        box.setDetailedText(err.details)
    box.exec()
