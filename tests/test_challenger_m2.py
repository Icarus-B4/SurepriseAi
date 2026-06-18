# -*- coding: utf-8 -*-
"""
test_challenger_m2.py
Empirische Grenzfalltests für Mausrad-Navigation und Hub-Aktionen (Challenger M2_1).
"""

import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ui.island_states import IslandState, IslandStateMachine
from src.ui.dynamic_island import DynamicIslandWindow
from src.ui.widgets.basics_widget import BRAND_TEXT
from src.services.config_service import config


@pytest.fixture(scope="session")
def q_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def app_setup(q_app):
    state_machine = IslandStateMachine()
    with patch("subprocess.run") as mock_run:
        window = DynamicIslandWindow(state_machine)
        config.set("enable_presence_bar", False)
        window.show()
        yield window, state_machine, mock_run
        window.close()


def test_mouse_wheel_transitions(app_setup):
    window, sm, _ = app_setup
    assert sm.current == IslandState.IDLE

    event_up = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, 120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    window.wheelEvent(event_up)
    QApplication.processEvents()
    assert sm.current == IslandState.BASICS

    event_down = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, -120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    window.wheelEvent(event_down)
    QApplication.processEvents()
    assert sm.current == IslandState.IDLE


def test_rapid_scroll_stress(app_setup):
    window, sm, _ = app_setup
    assert sm.current == IslandState.IDLE

    event_up = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, 120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    event_down = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, -120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )

    for _ in range(25):
        window.wheelEvent(event_up)
        window.wheelEvent(event_down)
    QApplication.processEvents()
    assert sm.current in (IslandState.IDLE, IslandState.BASICS)


def test_hub_typewriter_brand(app_setup):
    """Hub zeigt SurepriseAI per Typewriter."""
    window, sm, _ = app_setup
    sm.transition_to(IslandState.BASICS)
    QApplication.processEvents()

    basics_w = window.pill.basics_widget
    QTest.qWait(800)
    QApplication.processEvents()
    assert BRAND_TEXT.startswith(basics_w.title_label.text()[:4])


def test_hub_history_button(app_setup):
    window, sm, _ = app_setup
    sm.transition_to(IslandState.BASICS)
    QApplication.processEvents()

    called = {"ok": False}
    window.hub_history_callback = lambda: called.update(ok=True)
    window.pill.basics_widget.btn_history.click()
    QApplication.processEvents()
    assert called["ok"]


def test_hub_transcript_button(app_setup):
    window, sm, _ = app_setup
    sm.transition_to(IslandState.BASICS)
    QApplication.processEvents()

    called = {"ok": False}
    window.hub_transcript_callback = lambda: called.update(ok=True)
    window.pill.basics_widget.btn_transcript.click()
    QApplication.processEvents()
    assert called["ok"]


def test_hub_rewrite_button(app_setup):
    window, sm, _ = app_setup
    sm.transition_to(IslandState.BASICS)
    QApplication.processEvents()

    called = {"ok": False}
    window.hub_rewrite_callback = lambda: called.update(ok=True)
    window.pill.basics_widget.btn_rewrite.click()
    QApplication.processEvents()
    assert called["ok"]


def test_uncontrolled_state_transitions(app_setup):
    """Scrollen während Hub-Modus bleibt stabil."""
    window, sm, mock_run = app_setup
    sm.transition_to(IslandState.BASICS)
    QApplication.processEvents()

    event_down = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, -120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    window.wheelEvent(event_down)
    QApplication.processEvents()
    assert sm.current == IslandState.IDLE

    event_up = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10),
        QPoint(0, 0), QPoint(0, 120),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    window.wheelEvent(event_up)
    QApplication.processEvents()
    assert sm.current == IslandState.BASICS
    mock_run.assert_not_called()
