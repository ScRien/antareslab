"""
ANTARES 3D Studio - UI Stilleri
Merkezi stil tanımlamaları
"""

# Ana uygulama stili
MAIN_STYLE = """
QMainWindow {
    background-color: #0a0f1a;
}

QLabel {
    color: #e0e0e0;
    background: transparent;
    border: none;
}

QLineEdit {
    background-color: #1a2535;
    color: white;
    border: 1px solid #2c5364;
    padding: 10px 15px;
    border-radius: 6px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #14a3a8;
}

QLineEdit:disabled {
    background-color: #151c28;
    color: #666;
}

QTextEdit {
    background-color: #1a2535;
    color: #e0e0e0;
    border: 1px solid #2c5364;
    border-radius: 6px;
    padding: 10px;
}

QProgressBar {
    background-color: #1a2535;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: white;
    height: 24px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #14a3a8, stop:1 #00d2ff);
    border-radius: 5px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QComboBox {
    background-color: #1a2535;
    color: white;
    border: 1px solid #2c5364;
    padding: 8px 15px;
    border-radius: 6px;
    min-width: 120px;
}

QComboBox:hover {
    border: 1px solid #14a3a8;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #1a2535;
    color: white;
    selection-background-color: #14a3a8;
    border: 1px solid #2c5364;
}

QMenuBar {
    background-color: #0a0f1a;
    color: #a0a0a0;
    border-bottom: 1px solid #1a2535;
    padding: 5px;
}

QMenuBar::item {
    padding: 8px 15px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #1a2535;
    color: white;
}

QMenu {
    background-color: #15192b;
    color: #e0e0e0;
    border: 1px solid #2c5364;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 10px 30px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #14a3a8;
}

QStatusBar {
    background-color: #0a0f1a;
    color: #666;
    border-top: 1px solid #1a2535;
}

QListWidget {
    background-color: #15192b;
    border: 1px solid #2c5364;
    border-radius: 8px;
    padding: 5px;
}

QListWidget::item {
    color: white;
    padding: 12px;
    border-radius: 6px;
    margin: 2px;
}

QListWidget::item:hover {
    background-color: rgba(255,255,255,0.05);
}

QListWidget::item:selected {
    background-color: #14a3a8;
}

QFrame {
    background: transparent;
    border: none;
}
"""

# Sidebar stili
SIDEBAR_STYLE = """
#sidebar {
    background-color: #0f1520;
    border-right: 1px solid #1a2535;
}
"""

# Sidebar buton stili
SIDEBAR_BUTTON_STYLE = """
QPushButton {
    background: transparent;
    color: #a0a0a0;
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 500;
    border-radius: 8px;
    margin: 2px 8px;
}

QPushButton:hover {
    background: rgba(255,255,255,0.05);
    color: #ffffff;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0d7377, stop:1 #14a3a8);
    color: #ffffff;
}
"""

# Ana buton stili
PRIMARY_BUTTON_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0d7377, stop:1 #14a3a8);
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 14px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #14a3a8, stop:1 #0d7377);
}

QPushButton:disabled {
    background: #2a3545;
    color: #666;
}
"""

# İkincil buton stili
SECONDARY_BUTTON_STYLE = """
QPushButton {
    background: #1a2535;
    color: white;
    border: 1px solid #2c5364;
    padding: 10px 20px;
    border-radius: 6px;
}

QPushButton:hover {
    border: 1px solid #14a3a8;
    background: #1f2d40;
}
"""

# Kart stili
CARD_STYLE = """
QFrame {
    background-color: #15192b;
    border: 1px solid #2c5364;
    border-radius: 12px;
}

QFrame:hover {
    border: 1px solid #14a3a8;
}
"""

# Onboarding kart stili
ONBOARDING_CARD_STYLE = """
QFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a2535, stop:1 #15192b);
    border: 2px dashed #2c5364;
    border-radius: 16px;
}
"""

# Uyarı stilleri
WARNING_STYLE = "color: #ff8800; font-size: 14px;"
SUCCESS_STYLE = "color: #00ff88; font-size: 14px;"
ERROR_STYLE = "color: #ff4444; font-size: 14px;"
INFO_STYLE = "color: #888; font-size: 14px;"

# Başlık stilleri
TITLE_STYLE = "color: white; font-size: 24px; font-weight: bold;"
SUBTITLE_STYLE = "color: #888; font-size: 14px;"
SECTION_TITLE_STYLE = "color: white; font-size: 18px; font-weight: bold;"
