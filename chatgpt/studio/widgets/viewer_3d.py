from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox


class Viewer3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path: Path | None = None

        layout = QVBoxLayout(self)
        self.info = QLabel("3D çıktı seç veya pipeline sonrası otomatik aç.", self)

        self.btn_pick = QPushButton("3D Dosya Seç (.ply/.obj/.stl)")
        self.btn_open = QPushButton("Open in 3D Viewer (Open3D)")
        self.btn_open.setEnabled(False)

        self.btn_pick.clicked.connect(self.pick_file)
        self.btn_open.clicked.connect(self.open_external)

        layout.addWidget(self.info)
        layout.addWidget(self.btn_pick)
        layout.addWidget(self.btn_open)

    def set_current_model(self, path: str | Path):
        p = Path(path)
        self._current_path = p
        self.info.setText(f"Seçili: {p.name}")
        self.btn_open.setEnabled(p.exists())

    def pick_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "3D dosya seç", "", "3D Files (*.ply *.obj *.stl)")
        if p:
            self.set_current_model(p)

    def open_external(self):
        if not self._current_path or not self._current_path.exists():
            return

        viewer = Path(__file__).resolve().parent.parent / "tools" / "o3d_viewer.py"
        if not viewer.exists():
            QMessageBox.critical(self, "Viewer bulunamadı", f"{viewer} yok.")
            return

        try:
            subprocess.Popen([sys.executable, str(viewer), str(self._current_path)], close_fds=True)
        except Exception as e:
            QMessageBox.critical(self, "Viewer açılamadı", str(e))
