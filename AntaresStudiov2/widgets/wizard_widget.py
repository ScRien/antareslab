"""
ANTARES 3D Studio - Wizard Widget Module
Adım adım rehber UI bileşenleri

Özellikler:
- Stepper/adım göstergesi
- İlerleme çubuğu ile entegre
- Tooltip ve yardım mesajları
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class StepStatus(Enum):
    """Adım durumu"""
    PENDING = "pending"       # Bekliyor
    ACTIVE = "active"         # Aktif/işleniyor
    COMPLETED = "completed"   # Tamamlandı
    ERROR = "error"           # Hata
    SKIPPED = "skipped"       # Atlandı


@dataclass
class WizardStep:
    """Wizard adım bilgisi"""
    name: str                            # "ESP32 Bağlantısı"
    description: str = ""                # "Kapsüle bağlanın"
    icon: str = ""                       # Emoji veya ikon
    status: StepStatus = StepStatus.PENDING
    progress: int = 0                    # 0-100 (aktif adım için)
    error_message: str = ""              # Hata mesajı


class StepIndicator(QWidget):
    """
    Adım göstergesi widget'ı.
    
    Görünüm:
    ┌─────────────────────────────────────────────────────────────────┐
    │  ● ESP32 Bağlantı  ───  ○ Görüntü İndir  ───  ○ 3D Oluştur     │
    │     [Tamamlandı]           [Bekliyor]          [Bekliyor]       │
    └─────────────────────────────────────────────────────────────────┘
    
    Kullanım:
        indicator = StepIndicator([
            WizardStep("Bağlantı", "ESP32'ye bağlan", "🔌"),
            WizardStep("İndirme", "Görüntüleri indir", "📥"),
            WizardStep("3D Model", "Model oluştur", "🏗️"),
            WizardStep("Görüntüle", "Sonucu gör", "👁️"),
        ])
        
        indicator.set_step_status(0, StepStatus.COMPLETED)
        indicator.set_step_status(1, StepStatus.ACTIVE)
    """
    
    # Sinyaller
    step_clicked = pyqtSignal(int)  # Adıma tıklandığında
    
    # Stil sabitleri
    CIRCLE_RADIUS = 18
    LINE_WIDTH = 3
    SPACING = 80
    
    # Renkler
    COLORS = {
        StepStatus.PENDING: QColor("#555555"),
        StepStatus.ACTIVE: QColor("#00d2ff"),
        StepStatus.COMPLETED: QColor("#00ff88"),
        StepStatus.ERROR: QColor("#ff4444"),
        StepStatus.SKIPPED: QColor("#888888"),
    }
    
    def __init__(self, steps: List[WizardStep] = None, parent=None):
        super().__init__(parent)
        self.steps = steps or []
        self.current_step = 0
        
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Tooltip için mouse tracking
        self.setMouseTracking(True)
    
    def set_steps(self, steps: List[WizardStep]):
        """Adımları ayarla"""
        self.steps = steps
        self.update()
    
    def set_step_status(self, index: int, status: StepStatus, error_message: str = ""):
        """Adım durumunu güncelle"""
        if 0 <= index < len(self.steps):
            self.steps[index].status = status
            self.steps[index].error_message = error_message
            
            if status == StepStatus.ACTIVE:
                self.current_step = index
            
            self.update()
    
    def set_step_progress(self, index: int, progress: int):
        """Adım ilerlemesini güncelle (aktif adım için)"""
        if 0 <= index < len(self.steps):
            self.steps[index].progress = max(0, min(100, progress))
            self.update()
    
    def next_step(self):
        """Sonraki adıma geç"""
        if self.current_step < len(self.steps) - 1:
            self.set_step_status(self.current_step, StepStatus.COMPLETED)
            self.current_step += 1
            self.set_step_status(self.current_step, StepStatus.ACTIVE)
    
    def reset(self):
        """Tüm adımları sıfırla"""
        self.current_step = 0
        for step in self.steps:
            step.status = StepStatus.PENDING
            step.progress = 0
            step.error_message = ""
        self.update()
    
    def _get_step_position(self, index: int) -> Tuple[int, int]:
        """Adımın ekran konumunu hesapla"""
        if not self.steps:
            return (0, 0)
        
        width = self.width()
        total_width = (len(self.steps) - 1) * self.SPACING + 2 * self.CIRCLE_RADIUS
        start_x = (width - total_width) // 2 + self.CIRCLE_RADIUS
        
        x = start_x + index * self.SPACING
        y = 30  # Daire merkezi y konumu
        
        return (x, y)
    
    def paintEvent(self, event):
        """Widget'ı çiz"""
        if not self.steps:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bağlantı çizgilerini çiz
        for i in range(len(self.steps) - 1):
            self._draw_connection_line(painter, i)
        
        # Daireleri ve etiketleri çiz
        for i, step in enumerate(self.steps):
            self._draw_step_circle(painter, i, step)
            self._draw_step_label(painter, i, step)
    
    def _draw_connection_line(self, painter: QPainter, index: int):
        """İki adım arasındaki çizgiyi çiz"""
        x1, y1 = self._get_step_position(index)
        x2, y2 = self._get_step_position(index + 1)
        
        # Çizgi rengi - önceki adım tamamlandıysa renkli
        if self.steps[index].status == StepStatus.COMPLETED:
            color = self.COLORS[StepStatus.COMPLETED]
        else:
            color = self.COLORS[StepStatus.PENDING]
        
        pen = QPen(color, self.LINE_WIDTH)
        painter.setPen(pen)
        painter.drawLine(
            x1 + self.CIRCLE_RADIUS, y1,
            x2 - self.CIRCLE_RADIUS, y2
        )
    
    def _draw_step_circle(self, painter: QPainter, index: int, step: WizardStep):
        """Adım dairesini çiz"""
        x, y = self._get_step_position(index)
        
        color = self.COLORS[step.status]
        
        # Daire dolgusu
        if step.status == StepStatus.ACTIVE:
            # Aktif adım - parlayan efekt
            painter.setBrush(QBrush(color.lighter(150)))
            
            # Progress göster (dış halka olarak)
            if step.progress > 0:
                progress_color = QColor("#ffffff")
                progress_color.setAlpha(100)
                painter.setPen(QPen(progress_color, 4))
                
                # Arc çiz (progress için)
                start_angle = 90 * 16  # 12 o'clock
                span_angle = -int(step.progress * 360 / 100) * 16
                painter.drawArc(
                    x - self.CIRCLE_RADIUS - 3, y - self.CIRCLE_RADIUS - 3,
                    (self.CIRCLE_RADIUS + 3) * 2, (self.CIRCLE_RADIUS + 3) * 2,
                    start_angle, span_angle
                )
        elif step.status == StepStatus.COMPLETED:
            painter.setBrush(QBrush(color))
        elif step.status == StepStatus.ERROR:
            painter.setBrush(QBrush(color))
        else:
            # Pending - sadece çerçeve
            painter.setBrush(QBrush(QColor("#1a1a1a")))
        
        # Daire çerçevesi
        painter.setPen(QPen(color, 2))
        painter.drawEllipse(
            x - self.CIRCLE_RADIUS, y - self.CIRCLE_RADIUS,
            self.CIRCLE_RADIUS * 2, self.CIRCLE_RADIUS * 2
        )
        
        # İçerik (numara veya ikon)
        painter.setPen(QPen(QColor("white") if step.status != StepStatus.PENDING else color, 1))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        if step.status == StepStatus.COMPLETED:
            text = "✓"
        elif step.status == StepStatus.ERROR:
            text = "✗"
        elif step.icon:
            text = step.icon
        else:
            text = str(index + 1)
        
        painter.drawText(
            x - self.CIRCLE_RADIUS, y - self.CIRCLE_RADIUS,
            self.CIRCLE_RADIUS * 2, self.CIRCLE_RADIUS * 2,
            Qt.AlignmentFlag.AlignCenter, text
        )
    
    def _draw_step_label(self, painter: QPainter, index: int, step: WizardStep):
        """Adım etiketini çiz"""
        x, y = self._get_step_position(index)
        
        color = self.COLORS[step.status]
        
        # Adım adı
        painter.setPen(QPen(color if step.status != StepStatus.PENDING else QColor("#888888"), 1))
        font = QFont("Segoe UI", 9)
        font.setBold(step.status == StepStatus.ACTIVE)
        painter.setFont(font)
        
        label_y = y + self.CIRCLE_RADIUS + 15
        painter.drawText(
            x - 50, label_y,
            100, 20,
            Qt.AlignmentFlag.AlignCenter, step.name
        )
        
        # Durum metni (küçük)
        status_texts = {
            StepStatus.PENDING: "Bekliyor",
            StepStatus.ACTIVE: "İşleniyor...",
            StepStatus.COMPLETED: "Tamamlandı",
            StepStatus.ERROR: "Hata!",
            StepStatus.SKIPPED: "Atlandı",
        }
        
        status_text = status_texts.get(step.status, "")
        if step.status == StepStatus.ACTIVE and step.progress > 0:
            status_text = f"%{step.progress}"
        
        painter.setPen(QPen(QColor("#666666"), 1))
        font.setPointSize(7)
        font.setBold(False)
        painter.setFont(font)
        
        painter.drawText(
            x - 50, label_y + 15,
            100, 15,
            Qt.AlignmentFlag.AlignCenter, status_text
        )
    
    def mouseMoveEvent(self, event):
        """Mouse hareketi - tooltip göster"""
        for i, step in enumerate(self.steps):
            x, y = self._get_step_position(i)
            
            # Daire içinde mi?
            dx = event.position().x() - x
            dy = event.position().y() - y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= self.CIRCLE_RADIUS:
                tooltip = f"{step.name}"
                if step.description:
                    tooltip += f"\n{step.description}"
                if step.error_message:
                    tooltip += f"\n⚠️ {step.error_message}"
                
                QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
                return
        
        QToolTip.hideText()
    
    def mousePressEvent(self, event):
        """Mouse tıklama - adım seçimi"""
        for i, step in enumerate(self.steps):
            x, y = self._get_step_position(i)
            
            dx = event.position().x() - x
            dy = event.position().y() - y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= self.CIRCLE_RADIUS:
                self.step_clicked.emit(i)
                return


class WizardPanel(QFrame):
    """
    Tam wizard paneli (stepper + içerik).
    
    Kullanım:
        wizard = WizardPanel()
        wizard.add_step("Bağlantı", connection_widget)
        wizard.add_step("İndirme", download_widget)
        wizard.add_step("3D Model", model_widget)
        
        wizard.start()
    """
    
    # Sinyaller
    step_changed = pyqtSignal(int)
    wizard_completed = pyqtSignal()
    wizard_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.steps: List[WizardStep] = []
        self.step_widgets: List[QWidget] = []
        self.current_index = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Stepper
        self.step_indicator = StepIndicator()
        layout.addWidget(self.step_indicator)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #2c5364;")
        layout.addWidget(line)
        
        # İçerik alanı (step widget'ları için)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(self.content_area, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("← Geri")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setEnabled(False)
        btn_layout.addWidget(self.btn_back)
        
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_next = QPushButton("İleri →")
        self.btn_next.clicked.connect(self.go_next)
        btn_layout.addWidget(self.btn_next)
        
        layout.addLayout(btn_layout)
        
        # Stil
        self.setStyleSheet("""
            WizardPanel {
                background-color: #15192b;
                border: 1px solid #2c5364;
                border-radius: 8px;
            }
            QPushButton {
                min-width: 80px;
            }
        """)
    
    def add_step(self, name: str, widget: QWidget, description: str = "", icon: str = ""):
        """Adım ekle"""
        step = WizardStep(name=name, description=description, icon=icon)
        self.steps.append(step)
        self.step_widgets.append(widget)
        
        # Widget'ı gizle (sadece aktif olan görünür)
        widget.setVisible(False)
        self.content_layout.addWidget(widget)
        
        # Stepper'ı güncelle
        self.step_indicator.set_steps(self.steps)
    
    def start(self):
        """Wizard'ı başlat"""
        if not self.steps:
            return
        
        self.current_index = 0
        self._show_step(0)
        self.step_indicator.set_step_status(0, StepStatus.ACTIVE)
    
    def go_next(self):
        """Sonraki adıma geç"""
        if self.current_index < len(self.steps) - 1:
            # Mevcut adımı tamamlandı olarak işaretle
            self.step_indicator.set_step_status(self.current_index, StepStatus.COMPLETED)
            
            # Sonraki adım
            self.current_index += 1
            self._show_step(self.current_index)
            self.step_indicator.set_step_status(self.current_index, StepStatus.ACTIVE)
            
            self.step_changed.emit(self.current_index)
        else:
            # Son adım tamamlandı
            self.step_indicator.set_step_status(self.current_index, StepStatus.COMPLETED)
            self.wizard_completed.emit()
    
    def go_back(self):
        """Önceki adıma dön"""
        if self.current_index > 0:
            self.step_indicator.set_step_status(self.current_index, StepStatus.PENDING)
            
            self.current_index -= 1
            self._show_step(self.current_index)
            self.step_indicator.set_step_status(self.current_index, StepStatus.ACTIVE)
            
            self.step_changed.emit(self.current_index)
    
    def go_to_step(self, index: int):
        """Belirli bir adıma git"""
        if 0 <= index < len(self.steps):
            self._show_step(index)
            self.current_index = index
            self.step_indicator.set_step_status(index, StepStatus.ACTIVE)
            self.step_changed.emit(index)
    
    def set_step_error(self, index: int, error_message: str):
        """Adımda hata göster"""
        self.step_indicator.set_step_status(index, StepStatus.ERROR, error_message)
    
    def set_step_progress(self, progress: int):
        """Mevcut adımın ilerlemesini güncelle"""
        self.step_indicator.set_step_progress(self.current_index, progress)
    
    def _show_step(self, index: int):
        """Belirli adımı göster"""
        # Tüm widget'ları gizle
        for w in self.step_widgets:
            w.setVisible(False)
        
        # Seçili widget'ı göster
        if 0 <= index < len(self.step_widgets):
            self.step_widgets[index].setVisible(True)
        
        # Buton durumları
        self.btn_back.setEnabled(index > 0)
        
        if index == len(self.steps) - 1:
            self.btn_next.setText("Tamamla ✓")
        else:
            self.btn_next.setText("İleri →")
    
    def _on_cancel(self):
        """İptal edildi"""
        self.wizard_cancelled.emit()
    
    def set_next_enabled(self, enabled: bool):
        """İleri butonunu etkinleştir/devre dışı bırak"""
        self.btn_next.setEnabled(enabled)
    
    def set_back_enabled(self, enabled: bool):
        """Geri butonunu etkinleştir/devre dışı bırak"""
        self.btn_back.setEnabled(enabled and self.current_index > 0)
