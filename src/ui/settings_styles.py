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
    return """
        QWidget#SettingsContainer {{
            background-color: {glass_bg};
            border: 1px solid {glass_border};
            border-radius: 18px;
            font-family: "{font}";
            font-size: {small}pt;
            color: {text_primary};
        }}

        QWidget#SettingsSidebar {{
            background-color: rgba(255, 255, 255, 0.035);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            border-top-left-radius: 18px;
            border-bottom-left-radius: 18px;
        }}

        QStackedWidget#SettingsContentStack {{
            background: transparent;
            border: none;
        }}

        QPushButton#SidebarNavButton {{
            background: transparent;
            color: {text_secondary};
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 8px 10px;
            text-align: left;
            font-family: "{font}";
            font-size: {small}pt;
            font-weight: 650;
        }}
        QPushButton#SidebarNavButton:hover {{
            background-color: rgba(255, 255, 255, 0.06);
            color: {text_primary};
            border-color: rgba(255, 255, 255, 0.08);
        }}
        QPushButton#SidebarNavButton:checked {{
            background-color: rgba(99, 102, 241, 0.22);
            color: {text_primary};
            border-color: rgba(129, 140, 248, 0.36);
        }}

        QLabel#SettingsSidebarBrand {{
            color: {text_tertiary};
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 10px 12px;
            font-size: {tiny}pt;
            font-weight: 700;
        }}

        QWidget#SettingsHero {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(99, 102, 241, 0.18),
                stop: 1 rgba(13, 13, 15, 0.00)
            );
            border: 1px solid rgba(129, 140, 248, 0.16);
            border-radius: 16px;
        }}

        QLabel#SettingsHeroTitle {{
            color: {text_primary};
            font-size: {title}pt;
            font-weight: 700;
        }}

        QLabel#SettingsHeroSubtitle {{
            color: {text_secondary};
            font-size: {tiny}pt;
        }}

        QLabel#SettingsSectionBadge {{
            color: {accent_bright};
            background: rgba(99, 102, 241, 0.12);
            border: 1px solid rgba(99, 102, 241, 0.20);
            border-radius: 999px;
            padding: 2px 8px;
            font-size: {tiny}pt;
            font-weight: 600;
        }}

        QFrame#SettingsSectionCard {{
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
        }}

        QLabel {{
            font-family: "{font}";
            background: transparent;
        }}

        QLabel#SettingsWindowTitle {{
            color: {text_primary};
            font-size: {medium}pt;
            font-weight: 700;
        }}

        QLabel#SectionTitle {{
            color: {text_secondary};
            font-size: {small}pt;
            font-weight: 600;
            letter-spacing: 0.6px;
            padding-top: 2px;
        }}

        QLabel#SectionIcon {{
            color: {accent_bright};
            font-size: {small}pt;
        }}

        QLabel#FieldLabel,
        QLabel#ToggleLabel {{
            color: {text_primary};
            font-size: {small}pt;
            font-weight: 400;
        }}

        QLabel#HintLabel {{
            color: {text_tertiary};
            font-size: {tiny}pt;
            font-weight: 400;
            line-height: 1.35;
        }}

        QFrame#SectionDivider {{
            background: {border};
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
            background-color: {elevated};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px 12px;
            font-family: "{font}";
            font-size: {small}pt;
            min-height: 20px;
        }}
        QComboBox {{
            background-color: {elevated};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px 32px 8px 12px;
            font-family: "{font}";
            font-size: {small}pt;
            min-height: 20px;
        }}
        QComboBox:focus, QLineEdit:focus {{
            border: 1px solid {accent};
            background-color: rgba(40, 40, 48, 0.98);
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border: none;
            border-left: 1px solid {border};
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            width: 0; height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {text_secondary};
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: rgba(28, 28, 32, 0.98);
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 4px;
            font-family: "{font}";
            font-size: {small}pt;
            selection-background-color: {accent_dark};
        }}

        QPushButton {{
            background-color: {elevated};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 10px 14px;
            font-family: "{font}";
            font-size: {small}pt;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {accent_dark};
            border-color: {accent};
        }}
        QPushButton#CloseButton {{
            background: transparent;
            border: none;
            color: {text_secondary};
            font-family: "Segoe UI Symbol";
            font-size: {body}pt;
            font-weight: 400;
            padding: 4px;
        }}
        QPushButton#CloseButton:hover {{
            color: {recording_red};
            background-color: rgba(255, 69, 58, 0.12);
            border-radius: 8px;
        }}

        QPushButton#HistoryButton {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 {accent},
                stop: 1 {accent_bright}
            );
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 700;
        }}
        QPushButton#HistoryButton:hover {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 {accent_bright},
                stop: 1 {accent}
            );
        }}
    """.format(
        glass_bg=GLASS_BG,
        glass_border=GLASS_BORDER,
        elevated=GLASS_ELEVATED,
        font=_FONT,
        tiny=Typography.TINY,
        small=Typography.SMALL,
        medium=Typography.MEDIUM,
        title=Typography.TITLE,
        body=Typography.BODY,
        text_primary=Colors.TEXT_PRIMARY_HEX,
        text_secondary=Colors.TEXT_SECONDARY_HEX,
        text_tertiary=Colors.TEXT_TERTIARY_HEX,
        accent=Colors.ACCENT_HEX,
        accent_bright=Colors.ACCENT_BRIGHT_HEX,
        accent_dark=Colors.ACCENT_DARK_HEX,
        border=Colors.BORDER_HEX,
        recording_red=Colors.RECORDING_RED_HEX,
    )
