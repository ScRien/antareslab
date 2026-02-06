"""
ANTARES 3D Studio - Flat Design Tema Sistemi
Border-free, shadow-based, WCAG uyumlu

Tasarım Prensipleri:
- Kenarlık yerine gölge ve spacing
- Yüksek kontrast (WCAG AA uyumlu)
- Modern flat design
- Animasyonlu progress bar
"""

from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"


@dataclass
class ThemeColors:
    """Tema renk paleti - Flat Design"""
    
    # Ana renkler
    primary: str = "#14a3a8"
    primary_hover: str = "#0d7377"
    primary_light: str = "#1cc4ca"
    primary_subtle: str = "rgba(20, 163, 168, 0.1)"
    
    secondary: str = "#6c5ce7"
    accent: str = "#00d2ff"
    
    # Arkaplan - Gradyan destekli
    bg_primary: str = "#0a0f1a"
    bg_secondary: str = "#0f1520"
    bg_card: str = "#141a28"
    bg_input: str = "#1a2535"
    bg_hover: str = "rgba(255, 255, 255, 0.03)"
    bg_elevated: str = "#181f2e"
    
    # Metin - Yüksek kontrast
    text_primary: str = "#ffffff"
    text_secondary: str = "#b0b8c4"
    text_muted: str = "#6b7280"
    text_disabled: str = "#4b5563"
    
    # Gölgeler (border yerine)
    shadow_sm: str = "0 1px 2px rgba(0, 0, 0, 0.3)"
    shadow_md: str = "0 4px 12px rgba(0, 0, 0, 0.25)"
    shadow_lg: str = "0 8px 24px rgba(0, 0, 0, 0.3)"
    shadow_glow: str = "0 0 20px rgba(20, 163, 168, 0.15)"
    
    # Durum renkleri
    success: str = "#10b981"
    success_bg: str = "rgba(16, 185, 129, 0.1)"
    warning: str = "#f59e0b"
    warning_bg: str = "rgba(245, 158, 11, 0.1)"
    error: str = "#ef4444"
    error_bg: str = "rgba(239, 68, 68, 0.1)"
    info: str = "#3b82f6"
    info_bg: str = "rgba(59, 130, 246, 0.1)"
    
    # Sidebar
    sidebar_bg: str = "#0c1118"
    sidebar_hover: str = "rgba(255, 255, 255, 0.04)"
    sidebar_active: str = "rgba(20, 163, 168, 0.15)"
    
    # Diğer
    divider: str = "rgba(255, 255, 255, 0.06)"
    overlay: str = "rgba(0, 0, 0, 0.6)"


# Koyu Tema - Premium Dark
DARK_THEME = ThemeColors()

# Açık Tema - Profesyonel Light Mode (WCAG Uyumlu)
LIGHT_THEME = ThemeColors(
    primary="#0891b2",
    primary_hover="#0e7490",
    primary_light="#06b6d4",
    primary_subtle="rgba(8, 145, 178, 0.08)",
    
    secondary="#7c3aed",
    accent="#0ea5e9",
    
    bg_primary="#f8fafc",
    bg_secondary="#ffffff",
    bg_card="#ffffff",
    bg_input="#f1f5f9",
    bg_hover="rgba(0, 0, 0, 0.02)",
    bg_elevated="#ffffff",
    
    # Yüksek kontrast yazılar (WCAG AA)
    text_primary="#0f172a",
    text_secondary="#334155",
    text_muted="#64748b",
    text_disabled="#94a3b8",
    
    # Açık tema gölgeleri
    shadow_sm="0 1px 2px rgba(0, 0, 0, 0.05)",
    shadow_md="0 4px 12px rgba(0, 0, 0, 0.08)",
    shadow_lg="0 8px 24px rgba(0, 0, 0, 0.12)",
    shadow_glow="0 0 20px rgba(8, 145, 178, 0.1)",
    
    success="#059669",
    success_bg="rgba(5, 150, 105, 0.08)",
    warning="#d97706",
    warning_bg="rgba(217, 119, 6, 0.08)",
    error="#dc2626",
    error_bg="rgba(220, 38, 38, 0.08)",
    info="#2563eb",
    info_bg="rgba(37, 99, 235, 0.08)",
    
    sidebar_bg="#ffffff",
    sidebar_hover="rgba(0, 0, 0, 0.03)",
    sidebar_active="rgba(8, 145, 178, 0.1)",
    
    divider="rgba(0, 0, 0, 0.06)",
    overlay="rgba(0, 0, 0, 0.4)"
)


def get_stylesheet(theme: ThemeColors) -> str:
    """Modern Flat Design stil sayfası - Border-free"""
    return f"""
    /* ==================== GLOBAL ==================== */
    
    QMainWindow {{
        background-color: {theme.bg_primary};
    }}
    
    QWidget {{
        font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
        font-size: 13px;
    }}
    
    /* ==================== LABEL - Clean & Minimal ==================== */
    
    QLabel {{
        color: {theme.text_primary};
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }}
    
    /* ==================== INPUT - Soft Borders ==================== */
    
    QLineEdit {{
        background-color: {theme.bg_input};
        color: {theme.text_primary};
        border: none;
        border-radius: 10px;
        padding: 14px 18px;
        font-size: 14px;
        selection-background-color: {theme.primary};
    }}
    
    QLineEdit:focus {{
        background-color: {theme.bg_elevated};
        outline: 2px solid {theme.primary};
        outline-offset: -2px;
    }}
    
    QLineEdit:disabled {{
        background-color: {theme.bg_hover};
        color: {theme.text_disabled};
    }}
    
    QLineEdit::placeholder {{
        color: {theme.text_muted};
    }}
    
    /* ==================== TEXT EDIT ==================== */
    
    QTextEdit {{
        background-color: {theme.bg_input};
        color: {theme.text_primary};
        border: none;
        border-radius: 12px;
        padding: 14px;
        font-size: 13px;
    }}
    
    QTextEdit:focus {{
        outline: 2px solid {theme.primary};
        outline-offset: -2px;
    }}
    
    /* ==================== BUTTON - Modern Flat ==================== */
    
    QPushButton {{
        background-color: {theme.primary};
        color: white;
        border: none;
        padding: 14px 28px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
    }}
    
    QPushButton:hover {{
        background-color: {theme.primary_hover};
    }}
    
    QPushButton:pressed {{
        background-color: {theme.primary_light};
        transform: scale(0.98);
    }}
    
    QPushButton:disabled {{
        background-color: {theme.bg_input};
        color: {theme.text_disabled};
    }}
    
    /* ==================== PROGRESS BAR - Modern Slim ==================== */
    
    QProgressBar {{
        background-color: {theme.bg_input};
        border: none;
        border-radius: 6px;
        text-align: center;
        color: transparent;
        height: 8px;
        min-height: 8px;
        max-height: 8px;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {theme.primary}, 
            stop:0.5 {theme.accent},
            stop:1 {theme.primary_light});
        border-radius: 6px;
    }}
    
    /* ==================== LIST WIDGET - Shadow Based ==================== */
    
    QListWidget {{
        background-color: {theme.bg_card};
        border: none;
        border-radius: 16px;
        padding: 12px;
        outline: none;
    }}
    
    QListWidget::item {{
        color: {theme.text_primary};
        padding: 16px 20px;
        border-radius: 12px;
        margin: 4px 0;
        background-color: transparent;
    }}
    
    QListWidget::item:hover {{
        background-color: {theme.bg_hover};
    }}
    
    QListWidget::item:selected {{
        background-color: {theme.primary_subtle};
        color: {theme.primary};
    }}
    
    /* ==================== SCROLL BAR - Minimal ==================== */
    
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {theme.divider};
        border-radius: 4px;
        min-height: 40px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {theme.text_muted};
    }}
    
    QScrollBar::add-line:vertical, 
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
        border: none;
        height: 0;
    }}
    
    /* ==================== MENU - Clean ==================== */
    
    QMenuBar {{
        background-color: {theme.bg_secondary};
        color: {theme.text_secondary};
        border: none;
        padding: 6px 12px;
    }}
    
    QMenuBar::item {{
        padding: 10px 18px;
        border-radius: 8px;
        background: transparent;
    }}
    
    QMenuBar::item:selected {{
        background-color: {theme.bg_hover};
        color: {theme.text_primary};
    }}
    
    QMenu {{
        background-color: {theme.bg_elevated};
        color: {theme.text_primary};
        border: none;
        border-radius: 14px;
        padding: 10px;
    }}
    
    QMenu::item {{
        padding: 12px 28px;
        border-radius: 8px;
    }}
    
    QMenu::item:selected {{
        background-color: {theme.primary_subtle};
        color: {theme.primary};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {theme.divider};
        margin: 8px 16px;
    }}
    
    /* ==================== STATUS BAR ==================== */
    
    QStatusBar {{
        background-color: {theme.bg_secondary};
        color: {theme.text_muted};
        border: none;
        padding: 8px;
    }}
    
    /* ==================== FRAME - Shadow Based ==================== */
    
    QFrame {{
        background: transparent;
        border: none;
    }}
    
    /* ==================== SCROLL AREA ==================== */
    
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}
    """


def get_sidebar_style(theme: ThemeColors) -> str:
    """Sidebar stili - Minimal"""
    return f"""
    #sidebar {{
        background-color: {theme.sidebar_bg};
        border: none;
    }}
    """


def get_sidebar_button_style(theme: ThemeColors) -> str:
    """Sidebar buton stili - Flat"""
    return f"""
    QPushButton {{
        background: transparent;
        color: {theme.text_secondary};
        border: none;
        text-align: left;
        padding: 16px 24px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 12px;
        margin: 2px 12px;
    }}
    
    QPushButton:hover {{
        background: {theme.sidebar_hover};
        color: {theme.text_primary};
    }}
    
    QPushButton:checked {{
        background: {theme.sidebar_active};
        color: {theme.primary};
        font-weight: 600;
    }}
    """


def get_card_style(theme: ThemeColors, accent: str = None) -> str:
    """Kart stili - Border-free, Shadow-based"""
    accent_color = accent or theme.primary
    return f"""
    QFrame {{
        background-color: {theme.bg_card};
        border: none;
        border-radius: 20px;
    }}
    """


def get_alert_style(theme: ThemeColors, alert_type: str = "info") -> str:
    """Alert stili - Subtle background"""
    colors = {
        "info": (theme.info, theme.info_bg),
        "warning": (theme.warning, theme.warning_bg),
        "success": (theme.success, theme.success_bg),
        "error": (theme.error, theme.error_bg)
    }
    fg, bg = colors.get(alert_type, (theme.info, theme.info_bg))
    
    return f"""
    QFrame {{
        background-color: {bg};
        border: none;
        border-left: 4px solid {fg};
        border-radius: 12px;
    }}
    """


# Varsayılan tema
_current_theme: ThemeColors = DARK_THEME
_current_mode: ThemeMode = ThemeMode.DARK


def get_current_theme() -> ThemeColors:
    return _current_theme


def get_current_mode() -> ThemeMode:
    return _current_mode


def set_theme(mode: ThemeMode):
    global _current_theme, _current_mode
    _current_mode = mode
    _current_theme = DARK_THEME if mode == ThemeMode.DARK else LIGHT_THEME


def is_dark_mode() -> bool:
    return _current_mode == ThemeMode.DARK
