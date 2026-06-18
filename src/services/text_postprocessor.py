"""
text_postprocessor.py
Orchestriert Developer-Syntax, Deutsch-Engine und IDE-Kontext.
"""

from __future__ import annotations

from typing import Optional

from src.services.config_service import config
from src.services.developer_syntax import apply_developer_syntax
from src.services.german_text_engine import apply_german_native
from src.services.app_mode_service import is_developer_context

_DEV_STYLE = "developer"


def should_apply_developer_mode(
    hwnd: Optional[int] = None,
    style: Optional[str] = None,
) -> bool:
    if not config.get_bool("enable_developer_mode", True):
        return False
    if style == _DEV_STYLE:
        return True
    if config.get_bool("developer_mode_auto_ide", True) and hwnd:
        return is_developer_context(hwnd)
    return False


def apply_postprocessing(
    text: str,
    style: Optional[str] = None,
    *,
    hwnd: Optional[int] = None,
    developer: Optional[bool] = None,
) -> str:
    """Wendet Developer-Syntax und Deutsch-Engine auf Text an."""
    if not text or not text.strip():
        return text

    result = text
    use_dev = developer if developer is not None else should_apply_developer_mode(hwnd, style)
    if use_dev:
        result = apply_developer_syntax(result)
    result = apply_german_native(result, style)
    return result
