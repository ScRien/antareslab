from PyQt6.QtWidgets import QApplication


def get_dark_industrial_stylesheet() -> str:
    """
    Uygulamanın tamamında kullanılacak merkezi 'Dark Industrial' temasını döndürür.

    Not:
    - Genel arka plan: koyu mavi-siyah tonları
    - Vurgu rengi: turkuaz / camgöbeği
    - Köşeler: hafif yuvarlatılmış
    - Padding: masabaşı uygulama hissi için genişletilmiş
    """
    return """
    QMainWindow {
        background-color: #050711;
    }

    QWidget {
        color: #E0E6ED;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 13px;
        background-color: #050711;
    }

    QTabWidget::pane {
        border: 1px solid #1f2937;
        background: #0b1020;
        border-radius: 6px;
    }

    QTabBar::tab {
        background: #050711;
        color: #9CA3AF;
        padding: 8px 18px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }

    QTabBar::tab:selected {
        background: #0b1020;
        color: #22D3EE;
        border-bottom: 2px solid #22D3EE;
    }

    QTabBar::tab:hover:!selected {
        color: #E5E7EB;
        background: #111827;
    }

    QPushButton {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 8px 14px;
        border-radius: 6px;
        color: #F9FAFB;
        font-weight: 600;
    }

    QPushButton:hover {
        background-color: #22D3EE;
        border-color: #06B6D4;
        color: #020617;
    }

    QPushButton:pressed {
        background-color: #0EA5E9;
        border-color: #0284C7;
        color: #020617;
    }

    QPushButton:disabled {
        background-color: #020617;
        border: 1px solid #111827;
        color: #4B5563;
    }

    QLineEdit,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QPlainTextEdit {
        background-color: #020617;
        border: 1px solid #1f2937;
        border-radius: 4px;
        padding: 6px 8px;
        color: #E5E7EB;
        selection-background-color: #22D3EE;
        selection-color: #020617;
    }

    QLineEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus {
        border: 1px solid #22D3EE;
        box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.35);
    }

    QListWidget {
        background-color: #020617;
        border: 1px solid #1f2937;
        border-radius: 4px;
    }

    QListWidget::item {
        padding: 6px 8px;
    }

    QListWidget::item:selected {
        background-color: #22D3EE;
        color: #020617;
    }

    QGroupBox {
        border: 1px solid #1f2937;
        border-radius: 6px;
        margin-top: 16px;
        padding-top: 10px;
        background-color: #020617;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #22D3EE;
        background-color: transparent;
    }

    QProgressBar {
        border: 1px solid #1f2937;
        border-radius: 4px;
        text-align: center;
        color: #F9FAFB;
        background-color: #020617;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: #22C55E;
        border-radius: 4px;
    }

    QScrollBar:vertical {
        background: #020617;
        width: 10px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background: #1f2937;
        min-height: 20px;
        border-radius: 4px;
    }

    QScrollBar::handle:vertical:hover {
        background: #374151;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QCheckBox {
        color: #E5E7EB;
        spacing: 6px;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid #4B5563;
        background: #020617;
    }

    QCheckBox::indicator:checked {
        background-color: #22D3EE;
        border-color: #06B6D4;
    }
    """


def apply_dark_industrial_theme(app: QApplication) -> None:
    """
    Verilen QApplication örneğine Dark Industrial stylesheet'ini uygular.
    """
    app.setStyleSheet(get_dark_industrial_stylesheet())

