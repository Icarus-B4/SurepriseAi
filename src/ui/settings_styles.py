"""
settings_styles.py
QSS-Stile für das Einstellungsfenster (Glassmorphism, Toggles, Inputs).
"""

from src.ui.design_tokens import Colors, Typography, FluentIcons

# Leicht transparenter Glas-Hintergrund
GLASS_BG = "rgba(18, 18, 22, 0.78)"
GLASS_BORDER = "rgba(255, 255, 255, 0.14)"
GLASS_ELEVATED = "rgba(36, 36, 42, 0.65)"


def settings_stylesheet() -> str:
    """Gesamtes QSS für das Settings-Fenster."""
    return f"""
        QWidget#SettingsContainer {{
            background-color: {GLASS_BG};
            border: 1px solid {GLASS_BORDER};
            border-radius: 16px;
        }}
        QLabel {{
            color: {Colors.TEXT_PRIMARY_HEX};
            font-family: "{Typography.FONT_FAMILY}";
            background: transparent;
        }}
        QLabel#SectionTitle {{
            color: {Colors.TEXT_SECONDARY_HEX};
            font-weight: 600;
            letter-spacing: 0.4px;
            padding-top: 4px;
        }}
        QFrame#SectionDivider {{
            background: {Colors.BORDER_HEX};
            max-height: 1px;
            border: none;
        }}

        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 6px;
            margin: 4px 2px 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.14);
            min-height: 24px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.24);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none; border: none;
        }}

        QCheckBox {{
            color: {Colors.TEXT_SECONDARY_HEX};
            font-family: "{Typography.FONT_FAMILY}";
            font-size: 13px;
            spacing: 10px;
            padding: 2px 0;
        }}
        QCheckBox::indicator {{
            width: 36px;
            height: 20px;
            border-radius: 10px;
            border: 1px solid {Colors.BORDER_HEX};
            background-color: {GLASS_ELEVATED};
        }}
        QCheckBox::indicator:checked {{
            background-color: {Colors.ACCENT_HEX};
            border: 1px solid {Colors.ACCENT_BRIGHT_HEX};
        }}

        QComboBox, QLineEdit {{
            background-color: {GLASS_ELEVATED};
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 8px 32px 8px 12px;
            font-family: "{Typography.FONT_FAMILY}";
            font-size: 13px;
            min-height: 18px;
        }}
        QComboBox:focus, QLineEdit:focus {{
            border: 1px solid {Colors.ACCENT_HEX};
            background-color: rgba(36, 36, 42, 0.85);
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border: none;
            border-left: 1px solid {Colors.BORDER_HEX};
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT_SECONDARY_HEX};
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: rgba(28, 28, 32, 0.96);
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 4px;
            selection-background-color: {Colors.ACCENT_DARK_HEX};
        }}

        QPushButton {{
            background-color: {GLASS_ELEVATED};
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 8px;
            font-family: "{Typography.FONT_FAMILY}";
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_DARK_HEX};
            border-color: {Colors.ACCENT_HEX};
        }}
        QPushButton#CloseButton {{
            background: transparent;
            border: none;
            color: {Colors.TEXT_SECONDARY_HEX};
            font-size: 14px;
        }}
        QPushButton#CloseButton:hover {{
            color: {Colors.RECORDING_RED_HEX};
            background-color: rgba(255, 69, 58, 0.12);
        }}
    """
