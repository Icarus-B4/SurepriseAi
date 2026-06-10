"""
settings_features_section.py
Einstellungs-Sektion für Erscheinungsbild, Mini-FAB, App-Modi und Historie.
"""

from typing import Callable

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton

from src.ui.design_tokens import Colors, Typography
from src.ui.toggle_switch import ToggleRow
from src.services.config_service import config


def _parse_app_modes(text: str) -> dict[str, str]:
    """Parst OUTLOOK=formal, slack=business in ein Dict."""
    modes: dict[str, str] = {}
    for part in text.replace("\n", ",").split(","):
        chunk = part.strip()
        if not chunk or "=" not in chunk:
            continue
        key, style = chunk.split("=", 1)
        key, style = key.strip(), style.strip()
        if key and style:
            modes[key] = style
    return modes


def _format_app_modes(modes: dict) -> str:
    if not isinstance(modes, dict):
        return ""
    return ", ".join(f"{k}={v}" for k, v in modes.items())


def add_features_section(
    layout: QVBoxLayout,
    add_section: Callable[[QVBoxLayout, str, str], None],
    on_change: Callable[[str], None],
    on_open_history: Callable[[], None] | None = None,
) -> None:
    """Baut die Sektion Erscheinungsbild & Integration."""
    add_section(layout, "Erscheinungsbild", "🎨")

    def _toggle(label: str, key: str) -> ToggleRow:
        row = ToggleRow(label, checked=config.get_bool(key))
        row.toggled.connect(lambda checked, k=key: (_save_bool(k, checked), on_change(k)))
        layout.addWidget(row)
        return row

    _toggle("Windows-Akzentfarbe verwenden", "use_windows_accent")
    _toggle("Privacy-Badge in Idle-Pill", "show_privacy_badge")
    _toggle("Mini-FAB (schwebender Mic-Button)", "enable_mini_fab")
    _toggle("Updates beim Start prüfen", "check_updates_on_startup")

    add_section(layout, "Bildschirmkontext (OCR)", "👁")
    ctx_row = ToggleRow("Bildschirmkontext für Polishing (lokal, Windows-OCR)", checked=config.get_bool("enable_screen_context"))
    ctx_row.toggled.connect(
        lambda checked: (_save_bool("enable_screen_context", checked), on_change("enable_screen_context"))
    )
    layout.addWidget(ctx_row)

    sel_row = ToggleRow(
        "Markierten Text als Kontext (Ctrl+C beim Diktatstart)",
        checked=config.get_bool("enable_selected_text_context", True),
    )
    sel_row.toggled.connect(
        lambda checked: (
            _save_bool("enable_selected_text_context", checked),
            on_change("enable_selected_text_context"),
        )
    )
    layout.addWidget(sel_row)

    ctx_hint = QLabel(
        "Liest beim Diktatstart markierten Text und/oder OCR aus dem aktiven Fenster – "
        "hilft Ollama bei Eigennamen und Fachbegriffen. Alles lokal."
    )
    ctx_hint.setWordWrap(True)
    ctx_hint.setFont(Typography.get_font(Typography.TINY))
    ctx_hint.setStyleSheet(f"color: {Colors.TEXT_TERTIARY_HEX};")
    layout.addWidget(ctx_hint)

    add_section(layout, "App-Modi", "🪟")
    modes_row = ToggleRow("Stil automatisch je nach aktivem Fenster", checked=config.get_bool("enable_app_modes"))
    layout.addWidget(modes_row)

    modes_hint = QLabel("Fenster/Prozess = Stil, z. B. OUTLOOK=formal, slack=business")
    modes_hint.setWordWrap(True)
    modes_hint.setFont(Typography.get_font(Typography.TINY))
    modes_hint.setStyleSheet(f"color: {Colors.TEXT_TERTIARY_HEX};")
    layout.addWidget(modes_hint)

    modes_edit = QLineEdit()
    modes_edit.setPlaceholderText("OUTLOOK=formal, slack=business, discord=casual")
    modes_edit.setText(_format_app_modes(config.get("app_modes", {})))
    modes_edit.setCursorPosition(0)
    layout.addWidget(modes_edit)

    def _save_modes() -> None:
        parsed = _parse_app_modes(modes_edit.text())
        config.set("app_modes", parsed)
        on_change("app_modes")

    modes_edit.editingFinished.connect(_save_modes)
    modes_row.toggled.connect(
        lambda checked: (_save_bool("enable_app_modes", checked), on_change("enable_app_modes"))
    )

    if on_open_history:
        add_section(layout, "Verlauf", "📜")
        history_btn = QPushButton("Diktat-Verlauf öffnen")
        history_btn.clicked.connect(on_open_history)
        layout.addWidget(history_btn)


def _save_bool(key: str, value: bool) -> None:
    config.set(key, value)
