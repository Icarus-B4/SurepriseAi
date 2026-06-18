"""
crash_diagnostics.py
Globale Absturz- und Fehlerdiagnose – sehr früh beim App-Start installieren.
Schreibt in SurepriseAi-Diktat.log (Desktop + AppData) und aktiviert faulthandler.
"""

from __future__ import annotations

import atexit
import faulthandler
import os
import sys
import threading
import traceback
from types import TracebackType
from typing import Any, Optional, TextIO

_fault_log_file: Optional[TextIO] = None
_installed = False


def install_crash_handlers() -> None:
    """Registriert Hooks für Segfaults, uncaught Exceptions und Thread-Crashes."""
    global _installed
    if _installed:
        return
    _installed = True

    from src.services import dictation_logger as dlog

    dlog.write_boot_probe()

    primary = dlog.primary_log_path()
    try:
        primary.parent.mkdir(parents=True, exist_ok=True)
        global _fault_log_file
        _fault_log_file = open(primary, "a", encoding="utf-8", buffering=1)
        faulthandler.enable(file=_fault_log_file, all_threads=True)
        dlog.write("faulthandler aktiv (Segfault-Dump → Diktat-Log)", also_print=False, sync=True)
    except OSError as exc:
        dlog.write(f"WARNUNG faulthandler nicht aktivierbar: {exc}", also_print=True, sync=True)
        faulthandler.enable(all_threads=True)

    sys.excepthook = _global_excepthook
    threading.excepthook = _thread_excepthook
    if hasattr(sys, "unraisablehook"):
        sys.unraisablehook = _unraisable_hook

    atexit.register(_on_exit)


def install_qt_message_handler() -> None:
    """Qt-Warnungen und kritische Meldungen ins Diktat-Log."""
    try:
        from PyQt6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError:
        return

    _labels = {
        QtMsgType.QtWarningMsg: "QT-WARN",
        QtMsgType.QtCriticalMsg: "QT-CRITICAL",
        QtMsgType.QtFatalMsg: "QT-FATAL",
        QtMsgType.QtSystemMsg: "QT-SYSTEM",
        QtMsgType.QtInfoMsg: "QT-INFO",
        QtMsgType.QtDebugMsg: "QT-DEBUG",
    }
    _skip = {QtMsgType.QtDebugMsg, QtMsgType.QtInfoMsg}
    _critical = {
        QtMsgType.QtCriticalMsg,
        QtMsgType.QtFatalMsg,
        QtMsgType.QtSystemMsg,
    }

    def _handler(mode: QtMsgType, context: object, message: str) -> None:
        try:
            if mode in _skip:
                return
            label = _labels.get(mode, "QT")
            from src.services import dictation_logger as dlog

            loc = ""
            if context is not None and hasattr(context, "file") and context.file:
                loc = f" ({context.file}:{getattr(context, 'line', '?')})"
            sync = mode in _critical
            dlog.write(f"{label}{loc}: {message}", also_print=sync, sync=sync)
            if mode == QtMsgType.QtFatalMsg:
                dlog.write_crash("QT_FATAL", message)
        except Exception as exc:
            try:
                print(f"[QT-Handler] Logging fehlgeschlagen: {exc}", file=sys.stderr)
            except Exception:
                pass

    qInstallMessageHandler(_handler)


def _global_excepthook(
    exc_type: type[BaseException],
    exc: BaseException,
    tb: Optional[TracebackType],
) -> None:
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc, tb)
        return
    from src.services import dictation_logger as dlog

    detail = "".join(traceback.format_exception(exc_type, exc, tb))
    dlog.write_crash("UNCAUGHT_EXCEPTION", detail)
    sys.__excepthook__(exc_type, exc, tb)


def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
    if args.exc_type and issubclass(args.exc_type, (KeyboardInterrupt, SystemExit)):
        return
    from src.services import dictation_logger as dlog

    detail = "".join(
        traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
    )
    thread_name = getattr(args.thread, "name", "?") if args.thread else "?"
    dlog.write_crash(f"THREAD_EXCEPTION [{thread_name}]", detail)


def _unraisable_hook(unraisable: Any) -> None:
    from src.services import dictation_logger as dlog

    exc = unraisable.exc_value
    obj = unraisable.object
    err_msg = getattr(exc, "args", (str(exc),))[0] if exc else "?"
    dlog.write_crash(
        "UNRAISABLE_EXCEPTION",
        f"object={obj!r}\nerr_msg={err_msg!r}\n"
        f"{''.join(traceback.format_exception(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback))}",
    )
    if hasattr(sys, "__unraisablehook__"):
        sys.__unraisablehook__(unraisable)


def _on_exit() -> None:
    from src.services import dictation_logger as dlog

    dlog.write("Prozess beendet (atexit)", also_print=False, sync=True)
    global _fault_log_file
    if _fault_log_file is not None:
        try:
            _fault_log_file.flush()
            os.fsync(_fault_log_file.fileno())
            _fault_log_file.close()
        except OSError:
            pass
        _fault_log_file = None
