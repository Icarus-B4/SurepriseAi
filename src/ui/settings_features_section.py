"""
settings_features_section.py
Einstellungs-Sektion für Erscheinungsbild, App-Modi und Historie.
"""

from typing import Callable

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame

from src.ui.toggle_switch import ToggleRow
from src.services.config_service import config
from src.utils.app_paths import is_frozen
from src.utils import autostart


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
    card = QFrame()
    card.setObjectName("SettingsSectionCard")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(14, 12, 14, 12)
    card_layout.setSpacing(8)

    add_section(card_layout, "Erscheinungsbild", "🎨")

    def _toggle(label: str, key: str) -> ToggleRow:
        row = ToggleRow(label, checked=config.get_bool(key))
        row.toggled.connect(lambda checked, k=key: (_save_bool(k, checked), on_change(k)))
        card_layout.addWidget(row)
        return row

    _toggle("Presence-Bar (per Mausrad ein-/ausblenden)", "enable_presence_bar")
    _toggle("Windows-Akzentfarbe verwenden", "use_windows_accent")
    _toggle("Privacy-Badge in Idle-Pill", "show_privacy_badge")
    _toggle("Updates beim Start prüfen", "check_updates_on_startup")

    if is_frozen():
        autostart_row = ToggleRow(
            "Mit Windows starten",
            checked=autostart.is_enabled(),
        )
        autostart_row.toggled.connect(
            lambda checked: autostart.set_enabled(checked)
        )
        card_layout.addWidget(autostart_row)

    add_section(card_layout, "Bildschirmkontext (OCR)", "👁")
    ctx_row = ToggleRow("Bildschirmkontext für Polishing (lokal, Windows-OCR)", checked=config.get_bool("enable_screen_context"))
    ctx_row.toggled.connect(
        lambda checked: (_save_bool("enable_screen_context", checked), on_change("enable_screen_context"))
    )
    card_layout.addWidget(ctx_row)

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
    card_layout.addWidget(sel_row)

    ctx_hint = QLabel(
        "Liest beim Diktatstart markierten Text und/oder OCR aus dem aktiven Fenster – "
        "hilft Ollama bei Eigennamen und Fachbegriffen. Alles lokal."
    )
    ctx_hint.setObjectName("HintLabel")
    ctx_hint.setWordWrap(True)
    card_layout.addWidget(ctx_hint)

    add_section(card_layout, "App-Modi", "🪟")
    modes_row = ToggleRow("Stil automatisch je nach aktivem Fenster", checked=config.get_bool("enable_app_modes"))
    card_layout.addWidget(modes_row)

    modes_hint = QLabel("Fenster/Prozess = Stil, z. B. OUTLOOK=formal, slack=business")
    modes_hint.setObjectName("HintLabel")
    modes_hint.setWordWrap(True)
    card_layout.addWidget(modes_hint)

    modes_edit = QLineEdit()
    modes_edit.setPlaceholderText("OUTLOOK=formal, slack=business, discord=casual")
    modes_edit.setText(_format_app_modes(config.get("app_modes", {})))
    modes_edit.setCursorPosition(0)
    card_layout.addWidget(modes_edit)

    def _save_modes() -> None:
        parsed = _parse_app_modes(modes_edit.text())
        config.set("app_modes", parsed)
        on_change("app_modes")

    modes_edit.editingFinished.connect(_save_modes)
    modes_row.toggled.connect(
        lambda checked: (_save_bool("enable_app_modes", checked), on_change("enable_app_modes"))
    )

    add_section(card_layout, "Diff & Korrektur-Lernen", "✨")
    _toggle("Diff nach Polishing automatisch öffnen", "auto_show_diff_on_result")
    learn_row = ToggleRow(
        "Korrekturen nach Einfügen lernen",
        checked=config.get_bool("enable_correction_learning", True),
    )
    learn_row.toggled.connect(
        lambda checked: (
            _save_bool("enable_correction_learning", checked),
            on_change("enable_correction_learning"),
        )
    )
    card_layout.addWidget(learn_row)
    learn_hint = QLabel(
        "Liest nach dem Einfügen den bearbeiteten Text und merkt sich "
        "Einzelwort-Korrekturen lokal (Wörterbuch / Ersetzungen)."
    )
    learn_hint.setObjectName("HintLabel")
    learn_hint.setWordWrap(True)
    card_layout.addWidget(learn_hint)

    add_section(card_layout, "Developer & Hybrid", "⌨")
    _toggle("Developer Mode (camelCase / snake_case)", "enable_developer_mode")
    _toggle("Developer Mode automatisch in IDEs", "developer_mode_auto_ide")
    _toggle("Hybrid-Polishing (sofort + Ollama)", "enable_hybrid_polishing")
    _toggle("Hybrid: Deep-Text automatisch ersetzen", "hybrid_auto_reinject")
    dev_hint = QLabel(
        'Developer: „camel case user name" → userName. '
        "Hybrid: Instant-Text landet sofort, Ollama verfeinert danach."
    )
    dev_hint.setObjectName("HintLabel")
    dev_hint.setWordWrap(True)
    card_layout.addWidget(dev_hint)

    add_section(card_layout, "Deutsch-Engine", "🇩🇪")
    _toggle("Deutsch-native Engine (Sie/Du, Zahlen, €)", "enable_german_native_engine")
    de_hint = QLabel(
        "Formell/Business → Sie-Anrede, Casual/Kompakt → Du. "
        'Erkennt „12 komma 5" und „10 euro 50" als 12,5 bzw. 10,50 €.'
    )
    de_hint.setObjectName("HintLabel")
    de_hint.setWordWrap(True)
    card_layout.addWidget(de_hint)

    layout.addWidget(card)


def _save_bool(key: str, value: bool) -> None:
    config.set(key, value)
