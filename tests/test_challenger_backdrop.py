# -*- coding: utf-8 -*-
"""
test_challenger_backdrop.py
Tier-5 Adversarial-Tests für Win32-Backdrop (R5).
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ui import win32_backdrop as bd


@pytest.fixture(scope="module")
def q_app():
    app = QApplication.instance() or QApplication(sys.argv)
    return app


def test_apply_acrylic_fallback_on_non_win11(q_app):
    widget = QWidget()
    with patch.object(bd, "_is_win11", return_value=False):
        assert bd.apply_acrylic(widget) is False


def test_apply_mica_calls_dwm_on_win11(q_app):
    widget = QWidget()
    widget.show()
    with patch.object(bd, "_is_win11", return_value=True), patch.object(
        bd, "_set_dwm_attribute", return_value=True
    ) as mock_dwm:
        assert bd.apply_mica(widget) is True
        assert mock_dwm.called


def test_set_dwm_attribute_handles_os_error(q_app):
    with patch("ctypes.windll.dwmapi", side_effect=OSError("mock")):
        assert bd._set_dwm_attribute(1, 38, 3) is False


def test_remove_backdrop_without_hwnd(q_app):
    widget = MagicMock()
    widget.winId.side_effect = RuntimeError("no hwnd")
    assert bd.remove_backdrop(widget) is False
