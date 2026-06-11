"""
settings_styles.py
QSS-Stile für das Einstellungsfenster (Glassmorphism, Toggles, Inputs).
Typografie ausschließlich über Design-Tokens – keine gemischten px/pt-Werte.
"""

from src.ui.design_tokens import Colors, Typography

# Undurchsichtigerer Glas-Hintergrund – kein Durchscheinen der Island
GLASS_BG = "rgba(22, 22, 28, 0.96)"
GLASS_BORDER = "rgba(255, 255, 255, 0.12)"
GLASS_ELEVATED = "rgba(36, 36, 44, 0.92)"

_FONT = Typography.FONT_FAMILY


def settings_stylesheet() -> str:
    """Gesamtes QSS für das Settings-Fenster."""
    return f"""
        QWidget#SettingsContainer {{
            background-color: {GLASS_BG};
            border: 1px solid {GLASS_BORDER};
            border-radius: 16px;
            font-family: "{_FONT}";
            font-size: {Typography.SMALL}pt;
            color: {Colors.TEXT_PRIMARY_HEX};
        }}

        QLabel {{
            font-family: "{_FONT}";
            background: transparent;
        }}

        QLabel#SettingsWindowTitle {{
            color: {Colors.TEXT_PRIMARY_HEX};
            font-size: {Typography.MEDIUM}pt;
            font-weight: 700;
        }}

        QLabel#SectionTitle {{
            color: {Colors.TEXT_SECONDARY_HEX};
            font-size: {Typography.SMALL}pt;
            font-weight: 600;
            letter-spacing: 0.6px;
            padding-top: 2px;
        }}

        QLabel#SectionIcon {{
            color: {Colors.ACCENT_BRIGHT_HEX};
            font-size: {Typography.SMALL}pt;
        }}

        QLabel#FieldLabel,
        QLabel#ToggleLabel {{
            color: {Colors.TEXT_PRIMARY_HEX};
            font-size: {Typography.SMALL}pt;
            font-weight: 400;
        }}

        QLabel#HintLabel {{
            color: {Colors.TEXT_TERTIARY_HEX};
            font-size: {Typography.TINY}pt;
            font-weight: 400;
            line-height: 1.35;
        }}

        QFrame#SectionDivider {{
            background: {Colors.BORDER_HEX};
            max-height: 1px;
            border: none;
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}

        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 4px 0 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.16);
            min-height: 28px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.28);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none; border: none;
        }}

        QLineEdit {{
            background-color: {GLASS_ELEVATED};
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 8px 12px;
            font-family: "{_FONT}";
            font-size: {Typography.SMALL}pt;
            min-height: 20px;
        }}
        QComboBox {{
            background-color: {GLASS_ELEVATED};
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 8px 32px 8px 12px;
            font-family: "{_FONT}";
            font-size: {Typography.SMALL}pt;
            min-height: 20px;
        }}
        QComboBox:focus, QLineEdit:focus {{
            border: 1px solid {Colors.ACCENT_HEX};
            background-color: rgba(40, 40, 48, 0.98);
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
            background-color: rgba(28, 28, 32, 0.98);
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 4px;
            font-family: "{_FONT}";
            font-size: {Typography.SMALL}pt;
            selection-background-color: {Colors.ACCENT_DARK_HEX};
        }}

        QPushButton {{
            background-color: {GLASS_ELEVATED};
            color: {Colors.TEXT_PRIMARY_HEX};
            border: 1px solid {Colors.BORDER_HEX};
            border-radius: 8px;
            padding: 10px 14px;
            font-family: "{_FONT}";
            font-size: {Typography.SMALL}pt;
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
            font-family: "Segoe UI Symbol";
            font-size: {Typography.BODY}pt;
            font-weight: 400;
            padding: 4px;
        }}
        QPushButton#CloseButton:hover {{
            color: {Colors.RECORDING_RED_HEX};
            background-color: rgba(255, 69, 58, 0.12);
            border-radius: 8px;
        }}
    """
