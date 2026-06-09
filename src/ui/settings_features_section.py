"""
settings_features_section.py
Einstellungs-Sektion für Erscheinungsbild, Mini-FAB, App-Modi und Historie.
"""

from typing import Callable

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton

from src.ui.design_tokens import Colors, Typography
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

    def _checkbox(label: str, key: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.setChecked(config.get_bool(key))
        cb.stateChanged.connect(
            lambda state, k=key: (_save_bool(k, state == 2), on_change(k))
        )
        layout.addWidget(cb)
        return cb

    _checkbox("Windows-Akzentfarbe verwenden", "use_windows_accent")
    _checkbox("Privacy-Badge in Idle-Pill", "show_privacy_badge")
    _checkbox("Mini-FAB (schwebender Mic-Button)", "enable_mini_fab")
    _checkbox("Updates beim Start prüfen", "check_updates_on_startup")

    add_section(layout, "Bildschirmkontext (OCR)", "👁")
    ctx_cb = QCheckBox("Bildschirmkontext für Polishing (lokal, Windows-OCR)")
    ctx_cb.setChecked(config.get_bool("enable_screen_context"))
    ctx_cb.stateChanged.connect(
        lambda state: (_save_bool("enable_screen_context", state == 2), on_change("enable_screen_context"))
    )
    layout.addWidget(ctx_cb)

    sel_cb = QCheckBox("Markierten Text als Kontext (Ctrl+C beim Diktatstart)")
    sel_cb.setChecked(config.get_bool("enable_selected_text_context", True))
    sel_cb.stateChanged.connect(
        lambda state: (
            _save_bool("enable_selected_text_context", state == 2),
            on_change("enable_selected_text_context"),
        )
    )
    layout.addWidget(sel_cb)

    ctx_hint = QLabel(
        "Liest beim Diktatstart markierten Text und/oder OCR aus dem aktiven Fenster – "
        "hilft Ollama bei Eigennamen und Fachbegriffen. Alles lokal."
    )
    ctx_hint.setWordWrap(True)
    ctx_hint.setFont(Typography.get_font(Typography.TINY))
    ctx_hint.setStyleSheet(f"color: {Colors.TEXT_TERTIARY_HEX};")
    layout.addWidget(ctx_hint)

    add_section(layout, "App-Modi", "🪟")
    modes_cb = QCheckBox("Stil automatisch je nach aktivem Fenster")
    modes_cb.setChecked(config.get_bool("enable_app_modes"))
    layout.addWidget(modes_cb)

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
    modes_cb.stateChanged.connect(
        lambda state: (_save_bool("enable_app_modes", state == 2), on_change("enable_app_modes"))
    )

    if on_open_history:
        add_section(layout, "Verlauf", "📜")
        history_btn = QPushButton("Diktat-Verlauf öffnen")
        history_btn.clicked.connect(on_open_history)
        layout.addWidget(history_btn)


def _save_bool(key: str, value: bool) -> None:
    config.set(key, value)
