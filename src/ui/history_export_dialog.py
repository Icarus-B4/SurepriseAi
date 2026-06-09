"""
history_export_dialog.py
Dateiauswahl für Historien-Export (TXT / MD / SRT).
"""

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.services.history_export import export_entry


_FORMATS = "Text (*.txt);;Markdown (*.md);;Untertitel (*.srt)"


def export_history_entry(entry: dict, parent=None) -> bool:
    """Öffnet Speichern-Dialog und exportiert den Eintrag."""
    if not entry:
        return False

    ts = entry.get("timestamp", "diktat")[:10]
    default_name = f"SurepriseAi_{ts}"

    path_str, selected_filter = QFileDialog.getSaveFileName(
        parent,
        "Diktat exportieren",
        default_name,
        _FORMATS,
    )
    if not path_str:
        return False

    path = Path(path_str)
    fmt = _filter_to_fmt(selected_filter, path.suffix)

    try:
        export_entry(entry, fmt, path)
        return True
    except Exception as exc:
        QMessageBox.warning(parent, "Export fehlgeschlagen", str(exc))
        return False


def _filter_to_fmt(selected_filter: str, suffix: str) -> str:
    if "Markdown" in selected_filter or suffix.lower() == ".md":
        return "md"
    if "Untertitel" in selected_filter or suffix.lower() == ".srt":
        return "srt"
    return "txt"
