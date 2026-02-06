"""
ANTARES 3D Studio - Inline Help System
Tooltip ve yardım sistemi

Özellikler:
- Bağlamsal yardım tooltip'leri
- Yardım diyaloğu
- Kısayol referansı
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QTabWidget, QTextEdit, QFrame, QToolTip,
    QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QFont, QCursor
from typing import Dict, Optional


class HelpTooltip:
    """
    Gelişmiş tooltip yöneticisi.
    
    Kullanım:
        tooltip = HelpTooltip()
        tooltip.register(widget, "Bu butonun açıklaması", category="genel")
        tooltip.show_for(widget)
    """
    
    # Kategori renkleri
    CATEGORY_COLORS = {
        "genel": "#00d2ff",
        "uyari": "#ffff00",
        "hata": "#ff4444",
        "ipucu": "#00ff88"
    }
    
    def __init__(self):
        self.tooltips: Dict[int, dict] = {}
    
    def register(
        self, 
        widget: QWidget, 
        text: str, 
        category: str = "genel",
        shortcut: str = None
    ):
        """
        Widget için tooltip kaydet.
        
        Args:
            widget: Hedef widget
            text: Yardım metni
            category: Kategori (genel, uyari, hata, ipucu)
            shortcut: Kısayol tuşu (örn: "Ctrl+S")
        """
        tooltip_data = {
            'text': text,
            'category': category,
            'shortcut': shortcut
        }
        
        self.tooltips[id(widget)] = tooltip_data
        
        # Standart tooltip'i ayarla
        full_text = text
        if shortcut:
            full_text += f"\n\n⌨️ Kısayol: {shortcut}"
        
        widget.setToolTip(full_text)
    
    def get(self, widget: QWidget) -> Optional[dict]:
        """Widget'ın tooltip bilgisini al"""
        return self.tooltips.get(id(widget))
    
    def show_for(self, widget: QWidget, duration_ms: int = 3000):
        """Widget için tooltip göster"""
        data = self.get(widget)
        if data:
            pos = widget.mapToGlobal(QPoint(0, widget.height()))
            QToolTip.showText(pos, data['text'], widget, widget.rect(), duration_ms)


# Global tooltip manager
_tooltip_manager = HelpTooltip()


def register_help(widget: QWidget, text: str, shortcut: str = None):
    """Kısa yol: Yardım kaydı"""
    _tooltip_manager.register(widget, text, shortcut=shortcut)


# ==============================================================================
# YARDIM DİYALOĞU
# ==============================================================================

HELP_CONTENT = {
    "baslangic": """
# 🚀 Başlangıç Kılavuzu

## ANTARES KAPSÜL 3D STUDIO nedir?

Bu yazılım, arkeolojik eserlerin 3D dijital ikizlerini oluşturmak için tasarlanmıştır.
ESP32-CAM tabanlı ANTARES Kapsülü ile çekilen fotoğraflardan fotogrametri yöntemiyle
3D modeller üretir.

## İlk Adımlar

1. **Yeni Proje Oluştur**: Sol panelden "➕ Yeni Proje" butonuna tıklayın
2. **Kapsüle Bağlan**: ESP32'nin IP adresini girin (varsayılan: 192.168.4.1)
3. **Görüntüleri İndir**: Kapsülden fotoğrafları indirin
4. **Kalite Kontrolü**: Görüntü kalitesini analiz edin
5. **3D Model Oluştur**: Fotogrametri işlemini başlatın

## İpuçları

- En az 24 görüntü önerilir
- Eşit aydınlatma kaliteyi artırır
- Düşük kaliteli görüntüler sonucu olumsuz etkiler
""",
    
    "wizard": """
# 🧙 Wizard (Adım Adım Rehber)

Wizard, 3D model oluşturma sürecini adım adım yöneten bir sihirbazdır.

## Adımlar

### 1. 🔌 Bağlantı
ESP32 kapsüle bağlanın. IP adresi genellikle `192.168.4.1`'dir.

### 2. 📥 İndirme
Kapsüldeki görüntüleri bilgisayarınıza indirin.

### 3. ✅ Kalite Kontrolü
Görüntülerin kalitesini analiz edin:
- **Bulanıklık**: Netlik kontrolü
- **Parlaklık**: Aydınlatma dengesi
- **Işık Dağılımı**: Homojen aydınlatma (arkeolojik alanlarda kritik!)

### 4. 🏗️ 3D Model
Fotogrametri işlemiyle 3D model oluşturun.

## Kısayollar

| Tuş | İşlem |
|-----|-------|
| Enter | Sonraki adım |
| Backspace | Önceki adım |
| Esc | İptal |
""",
    
    "kalite": """
# 📊 Görüntü Kalite Analizi

## Metrikler

### Bulanıklık (Blur)
Laplacian varyansı ile ölçülür. Yüksek değer = net görüntü.

- **Mükemmel**: > 500
- **İyi**: > 200
- **Kabul edilebilir**: > 100
- **Zayıf**: > 50

### Işık Dağılımı
Arkeolojik alanlarda ışık çok değişken olduğundan bu metrik kritiktir.

- **Homojen**: Tüm görüntü eşit aydınlatılmış
- **Dengesiz**: Gölgeli veya aşırı parlak bölgeler var

### Kalite Seviyeleri

| Seviye | Renk | Açıklama |
|--------|------|----------|
| Mükemmel | 🟢 | 3D model için ideal |
| İyi | 🟢 | İyi sonuç beklenir |
| Kabul edilebilir | 🟡 | Kullanılabilir |
| Zayıf | 🟠 | Düşük kalite |
| Reddedildi | 🔴 | Kullanılamaz |
""",
    
    "viewer": """
# 🎨 3D Görüntüleyici

## Mouse Kontrolleri

| İşlem | Kontrol |
|-------|---------|
| Döndür | Sol tık + sürükle |
| Zoom | Scroll |
| Kaydır | Sağ tık + sürükle |

## Toolbar

- **🔄 Reset**: Kamerayı başlangıç konumuna getir
- **🔲 Solid**: Dolgulu görünüm
- **📐 Wireframe**: Tel kafes görünüm
- **⚫ Points**: Nokta bulutu görünüm
- **🎨 Renk**: Arka plan rengi değiştir
- **📏 Ölçüm**: Mesafe ölç
- **📷 Screenshot**: Ekran görüntüsü al

## Desteklenen Formatlar

- PLY (Point Cloud Library)
- OBJ (Wavefront)
- STL (Stereolithography)
""",
    
    "analiz": """
# 🔬 Bozulma Analizi

Zaman içinde eserlerdeki değişimi tespit etmek için kullanılır.

## İşleyiş

1. **Referans Model**: Önceki taramadan elde edilen model
2. **Güncel Model**: Yeni taramadan elde edilen model
3. **ICP Hizalama**: İki modeli otomatik hizala
4. **Karşılaştırma**: Yüzey mesafelerini hesapla

## Metrikler

- **Ortalama Mesafe**: Ortalama yüzey değişimi (mm)
- **Maksimum Mesafe**: En büyük değişim
- **Hausdorff Mesafesi**: Matematiksel maksimum mesafe
- **Hacim Değişimi**: Hacim farkı (%)
- **Yüzey Alanı Değişimi**: Alan farkı (%)

## Referans Nesne

Doğru ölçeklendirme için taramaya sabit boyutlu bir referans nesne
(örn: 1 cm küp) dahil edilebilir.

## Bozulma Seviyeleri

| Seviye | Mesafe | Açıklama |
|--------|--------|----------|
| Yok | < 0.1 mm | Değişim tespit edilmedi |
| Minimal | < 0.5 mm | Çok küçük değişim |
| Orta | < 2 mm | Belirgin değişim |
| Ciddi | < 4 mm | Önemli bozulma |
| Kritik | > 4 mm | Acil müdahale gerekli |
""",
    
    "kisayollar": """
# ⌨️ Kısayollar

## Genel

| Kısayol | İşlem |
|---------|-------|
| Ctrl+N | Yeni proje |
| Ctrl+O | Proje aç |
| Ctrl+S | Projeyi kaydet |
| Ctrl+B | Yedekle |
| F1 | Yardım |
| Esc | İptal |

## Wizard

| Kısayol | İşlem |
|---------|-------|
| Enter | Sonraki adım |
| Backspace | Önceki adım |
| Ctrl+Enter | İşlemi başlat |

## 3D Görüntüleyici

| Kısayol | İşlem |
|---------|-------|
| R | Kamerayı sıfırla |
| W | Wireframe modu |
| S | Solid modu |
| P | Nokta modu |
| Ctrl+P | Screenshot |

## Tab Navigasyonu

| Kısayol | Tab |
|---------|-----|
| Ctrl+1 | Wizard |
| Ctrl+2 | Görüntüler |
| Ctrl+3 | 3D Viewer |
| Ctrl+4 | Analiz |
"""
}


class HelpDialog(QDialog):
    """
    Yardım diyaloğu.
    
    Kullanım:
        dialog = HelpDialog(parent)
        dialog.show_topic("baslangic")
        dialog.exec()
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📚 Yardım")
        self.setMinimumSize(700, 500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Her konu için tab
        tab_icons = {
            "baslangic": "🚀",
            "wizard": "🧙",
            "kalite": "📊",
            "viewer": "🎨",
            "analiz": "🔬",
            "kisayollar": "⌨️"
        }
        
        tab_names = {
            "baslangic": "Başlangıç",
            "wizard": "Wizard",
            "kalite": "Kalite",
            "viewer": "3D Viewer",
            "analiz": "Analiz",
            "kisayollar": "Kısayollar"
        }
        
        for key, content in HELP_CONTENT.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            
            text = QTextEdit()
            text.setReadOnly(True)
            text.setMarkdown(content)
            text.setStyleSheet("""
                QTextEdit {
                    background-color: #15192b;
                    color: #e0e0e0;
                    border: none;
                    padding: 10px;
                }
            """)
            
            scroll.setWidget(text)
            
            icon = tab_icons.get(key, "📄")
            name = tab_names.get(key, key)
            self.tabs.addTab(scroll, f"{icon} {name}")
        
        layout.addWidget(self.tabs)
        
        # Kapat butonu
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0f2027;
            }
            QTabWidget::pane {
                border: 1px solid #2c5364;
                background-color: #15192b;
            }
            QTabBar::tab {
                background-color: #1a2535;
                color: #888;
                padding: 8px 15px;
            }
            QTabBar::tab:selected {
                background-color: #15192b;
                color: #00d2ff;
            }
        """)
    
    def show_topic(self, topic: str):
        """Belirli konuyu göster"""
        topic_indices = {
            "baslangic": 0,
            "wizard": 1,
            "kalite": 2,
            "viewer": 3,
            "analiz": 4,
            "kisayollar": 5
        }
        
        if topic in topic_indices:
            self.tabs.setCurrentIndex(topic_indices[topic])


class QuickHelpWidget(QFrame):
    """
    Bağlamsal hızlı yardım widget'ı.
    
    Ekranın köşesinde gösterilir.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMaximumWidth(300)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık
        title = QLabel("💡 İpucu")
        title.setStyleSheet("font-weight: bold; color: #00d2ff;")
        layout.addWidget(title)
        
        # İçerik
        self.content = QLabel()
        self.content.setWordWrap(True)
        self.content.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self.content)
        
        self.setStyleSheet("""
            QuickHelpWidget {
                background-color: #1a2535;
                border: 1px solid #2c5364;
                border-radius: 8px;
            }
        """)
    
    def show_tip(self, text: str):
        """İpucu göster"""
        self.content.setText(text)
        self.show()
    
    def hide_tip(self):
        """Gizle"""
        self.hide()


# Yardım fonksiyonları
def show_help(parent=None, topic: str = None):
    """Yardım diyaloğunu göster"""
    dialog = HelpDialog(parent)
    if topic:
        dialog.show_topic(topic)
    dialog.exec()
