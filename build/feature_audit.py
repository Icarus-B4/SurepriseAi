"""
feature_audit.py
Statischer Feature-Check gegen README.md – prüft Code-Pfade, Imports und Kern-APIs.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class AuditResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.failed: list[str] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def fail(self, msg: str) -> None:
        self.failed.append(msg)


def _has_callable(obj: Any, name: str) -> bool:
    return callable(getattr(obj, name, None))


def audit_dynamic_island(r: AuditResult) -> None:
    from src.ui.island_states import IslandState, IslandStateMachine
    from src.ui.dynamic_island import DynamicIslandWindow
    from src.ui.island_pill import IslandPill

    sm = IslandStateMachine()
    for state in (
        IslandState.IDLE,
        IslandState.RECORDING,
        IslandState.PROCESSING,
        IslandState.SUCCESS,
        IslandState.EXPANDED,
        IslandState.BASICS,
    ):
        if state not in IslandState:
            r.fail(f"Dynamic Island: State {state} fehlt")
            return
    r.ok("Dynamic Island: alle UI-States definiert (Idle/Rec/Proc/Success/Expanded/Basics)")

    for method in ("dragEnterEvent", "dropEvent", "mouseDoubleClickEvent", "reset_to_start_position"):
        if not _has_callable(DynamicIslandWindow, method):
            r.fail(f"Dynamic Island: {method} fehlt")
            return
    r.ok("Dynamic Island: Drag&Drop, Doppelklick, Reset vorhanden")

    if not _has_callable(IslandPill, "wheelEvent"):
        r.fail("Basics-Modus: wheelEvent fehlt")
    else:
        r.ok("Basics-Modus: Mausrad IDLE<->BASICS implementiert")


def audit_live_transcription(r: AuditResult) -> None:
    from src.services.transcription_pipeline import TranscriptionPipeline

    p = TranscriptionPipeline()
    if not _has_callable(p, "set_partial_callback"):
        r.fail("Live-Transkription: partial callback fehlt")
        return
    if not hasattr(p, "_live_transcription_worker"):
        r.fail("Live-Transkription: Worker fehlt")
        return
    r.ok("Live-Transkription: Pipeline-Partial-Worker vorhanden")


def audit_polishing(r: AuditResult) -> None:
    from src.services.polishing_service import PolishingService
    from src.services.style_definitions import STYLE_DEFINITIONS

    ps = PolishingService()
    for method in ("polish", "polish_instant", "check_ollama_status"):
        if not _has_callable(ps, method):
            r.fail(f"KI-Polishing: {method} fehlt")
            return

    readme_chips = {"casual", "business", "bullet_points", "concise", "formal"}
    code_keys = {k for k, _ in STYLE_DEFINITIONS}
    if not readme_chips.issubset(code_keys):
        r.fail(f"Stil-Chips: README-Stile fehlen: {readme_chips - code_keys}")
    extra = code_keys - readme_chips
    if extra:
        r.warn(f"Stil-Chips: README nennt 5, Code hat zusätzlich {sorted(extra)}")
    r.ok("KI-Polishing + README-Stil-Chips im Code vorhanden")


def audit_engines(r: AuditResult) -> None:
    from src.services.transcription_service import (
        TranscriptionService,
        SHERPA_AVAILABLE,
        WHISPER_AVAILABLE,
    )

    svc = TranscriptionService()
    if not _has_callable(svc, "initialize"):
        r.fail("Transkription: initialize fehlt")
        return
    if not WHISPER_AVAILABLE and not SHERPA_AVAILABLE:
        r.fail("Transkription: weder Whisper noch Parakeet importierbar")
        return
    engines = []
    if WHISPER_AVAILABLE:
        engines.append("whisper")
    if SHERPA_AVAILABLE:
        engines.append("parakeet")
    r.ok(f"Transkriptions-Engines importierbar: {', '.join(engines)}")


def audit_auto_typing(r: AuditResult) -> None:
    from src.services.clipboard_service import ClipboardService
    from src.services.config_service import config

    cs = ClipboardService()
    if not _has_callable(cs, "inject_text"):
        r.fail("Auto-Typing: inject_text fehlt")
        return
    if not config.get_bool("auto_inject_text", True) and "auto_inject_text" not in config._config:
        r.warn("Auto-Typing: config-Key auto_inject_text nicht in Defaults")
    r.ok("Auto-Typing: Clipboard-Inject implementiert")


def audit_tray(r: AuditResult) -> None:
    from src.ui.tray_icon import SurepriseTrayIcon

    signals = (
        "toggle_island",
        "open_settings",
        "toggle_recording",
        "style_selected",
        "open_history",
        "transcribe_url",
        "check_updates",
        "quit_app",
    )
    for sig in signals:
        if not hasattr(SurepriseTrayIcon, sig):
            r.fail(f"System-Tray: Signal {sig} fehlt")
            return
    r.ok("System-Tray: Diktat, Stil, URL, Historie, Updates, Beenden")


def audit_file_import(r: AuditResult) -> None:
    src = (ROOT / "src/ui/dynamic_island.py").read_text(encoding="utf-8")
    exts = (".mp3", ".wav", ".m4a", ".mp4", ".avi", ".mov", ".ogg", ".flac")
    if not all(ext in src for ext in exts):
        r.fail("Datei-Import: nicht alle README-Formate in dragEnterEvent")
        return
    r.ok("Datei-Import: Audio/Video Drag&Drop-Filter vorhanden")


def audit_url_import(r: AuditResult) -> None:
    from src.services.media_url_service import is_media_url, download_media_audio

    samples = [
        "https://www.youtube.com/watch?v=abc",
        "https://youtu.be/abc",
        "https://vimeo.com/123",
        "https://soundcloud.com/x/y",
    ]
    for url in samples:
        if not is_media_url(url):
            r.fail(f"URL-Import: {url} nicht erkannt")
            return
    if not _has_callable(download_media_audio, "__call__"):
        r.fail("URL-Import: download_media_audio fehlt")
        return
    r.ok("URL-Import: Host-Erkennung + yt-dlp-Download vorhanden")


def audit_context_polishing(r: AuditResult) -> None:
    from src.services.dictation_context_service import DictationContextService, merge_polish_context
    from src.services.selected_text_service import SelectedTextService
    from src.services.screen_context_service import ScreenContextService

    d = DictationContextService()
    for svc in (d.screen, d.selected):
        if not _has_callable(svc, "capture_async") or not _has_callable(svc, "get_context"):
            r.fail("Kontext-Polishing: capture/get fehlt")
            return
    merged = merge_polish_context("OCR-Text", "Markierung")
    if not merged or "Markierter Text" not in merged:
        r.fail("Kontext-Polishing: merge_polish_context fehlerhaft")
        return
    r.ok("Kontext-Polishing: Markierung + OCR-Merge implementiert")


def audit_history_export(r: AuditResult) -> None:
    from src.services.history_export import export_entry, _as_txt, _as_markdown, _as_srt

    entry = {
        "polished": "Hallo Welt.",
        "raw": "hallo welt",
        "timestamp": "2026-01-01T12:00:00",
        "style": "casual",
        "words": 2,
        "wpm": 80,
    }
    for fn, label in ((_as_txt, "TXT"), (_as_markdown, "MD"), (_as_srt, "SRT")):
        out = fn(entry)
        if not out or not out.strip():
            r.fail(f"Historien-Export: {label} leer")
            return

    tmp = ROOT / "build" / "_audit_export_test.txt"
    try:
        export_entry(entry, "txt", tmp)
        if not tmp.exists():
            r.fail("Historien-Export: export_entry schreibt keine Datei")
            return
    finally:
        tmp.unlink(missing_ok=True)

    r.ok("Historien-Export: TXT, Markdown, SRT")


def audit_hotkey(r: AuditResult) -> None:
    from src.services.hotkey_service import HotkeyService, PYNPUT_AVAILABLE

    if not PYNPUT_AVAILABLE:
        r.warn("Hotkey F8: pynput nicht installiert (nur Dev-Umgebung?)")
        return
    hk = HotkeyService()
    for m in ("start", "stop", "restart", "set_start_callback", "set_stop_callback"):
        if not _has_callable(hk, m):
            r.fail(f"Hotkey: {m} fehlt")
            return
    r.ok("Hotkey F8: Start/Stop/Restart vorhanden")


def audit_updates(r: AuditResult) -> None:
    from src.services.update_service import UpdateService, is_newer, parse_version
    from src.version import __version__

    us = UpdateService()
    if not _has_callable(us, "check_async") or not _has_callable(us, "_fetch_latest"):
        r.fail("Auto-Update: check_async/_fetch_latest fehlt")
        return
    assert parse_version("v0.2.0") > parse_version("0.1.0")
    assert is_newer("v9.9.9", __version__)
    r.ok("Auto-Update: Version-Vergleich + UpdateService vorhanden")


def audit_readme_controls(r: AuditResult) -> None:
    """README-Bedienung vs. Code."""
    ctrl_src = (ROOT / "src/services/app_controller.py").read_text(encoding="utf-8")
    island_src = (ROOT / "src/ui/dynamic_island.py").read_text(encoding="utf-8")

    if "idle_widget.mouseDoubleClickEvent = lambda e: self.app.pipeline.toggle()" in ctrl_src:
        r.fail(
            "README-Konflikt: Doppelklick auf Idle-Pill startet Diktat, "
            "README sagt Doppelklick = Einstellungen"
        )
    elif "_on_open_settings" in island_src and "mouseDoubleClickEvent" in island_src:
        r.ok("Einstellungen: Doppelklick auf Island oeffnet Settings (dynamic_island)")

    if "outside_dismiss_callback" not in ctrl_src:
        r.fail("Expanded schliessen: outside_dismiss_callback nicht verdrahtet")
    else:
        r.ok("Expanded schliessen: Klick-ausserhalb + X-Button verdrahtet")


def audit_transcription_windows_safe(r: AuditResult) -> None:
    from src.services.transcription_service import TranscriptionService

    svc = TranscriptionService()
    svc._initialized = True
    model = SimpleNamespace()
    model.transcribe = lambda *_a, **_k: ([SimpleNamespace(text="Audit OK")], {})
    svc._whisper_model = model
    audio = np.zeros(8000, dtype=np.float32)

    with patch("builtins.print", side_effect=UnicodeEncodeError("charmap", "x", 0, 1, "x")):
        text = svc._transcribe_whisper(audio)
    if text != "Audit OK":
        r.fail("Transkription: Windows-Log bricht Ergebnis noch ab")
        return
    r.ok("Transkription: Ergebnis unabhängig von Konsolen-Encoding")


def run_audit() -> AuditResult:
    r = AuditResult()
    audits = [
        audit_dynamic_island,
        audit_live_transcription,
        audit_polishing,
        audit_engines,
        audit_auto_typing,
        audit_tray,
        audit_file_import,
        audit_url_import,
        audit_context_polishing,
        audit_history_export,
        audit_hotkey,
        audit_updates,
        audit_readme_controls,
        audit_transcription_windows_safe,
    ]
    for fn in audits:
        try:
            fn(r)
        except Exception as exc:
            r.fail(f"{fn.__name__}: Exception {exc}")
    return r


def main() -> None:
    r = run_audit()
    print(f"\n=== SurepriseAi Feature-Audit ===\n")
    print(f"OK ({len(r.passed)}):")
    for line in r.passed:
        print(f"  [OK]   {line}")
    if r.warnings:
        print(f"\nHinweise ({len(r.warnings)}):")
        for line in r.warnings:
            print(f"  [WARN] {line}")
    if r.failed:
        print(f"\nFehler ({len(r.failed)}):")
        for line in r.failed:
            print(f"  [FAIL] {line}")
        sys.exit(1)
    print(f"\nAlle {len(r.passed)} Checks bestanden.")
    if r.warnings:
        print(f"({len(r.warnings)} Hinweise – siehe oben)")


if __name__ == "__main__":
    main()
