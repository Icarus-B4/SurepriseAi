"""Unit-Tests für HotkeyService (Basics-Gating, Callback-Aufruf)."""

from unittest.mock import MagicMock

import pytest

pynput = pytest.importorskip("pynput")

from src.services.hotkey_service import HotkeyService


def test_basics_letter_keys_ignored_when_hub_inactive():
    service = HotkeyService()
    mute_cb = MagicMock()
    service.set_mute_toggle_callback(mute_cb)
    service.set_basics_active_callback(lambda: False)

    char_m = pynput.keyboard.KeyCode.from_char("m")
    service._on_press(char_m)

    mute_cb.assert_not_called()


def test_basics_letter_keys_fire_when_hub_active():
    service = HotkeyService()
    mute_cb = MagicMock()
    service.set_mute_toggle_callback(mute_cb)
    service.set_basics_active_callback(lambda: True)

    char_m = pynput.keyboard.KeyCode.from_char("m")
    service._on_press(char_m)

    mute_cb.assert_called_once()


def test_function_hotkeys_work_without_basics_mode():
    service = HotkeyService()
    rewrite_cb = MagicMock()
    service.set_rewrite_callback(rewrite_cb)
    service.set_basics_active_callback(lambda: False)

    service._on_press(pynput.keyboard.Key.f9)

    rewrite_cb.assert_called_once()


def test_global_hotkey_works_without_basics_mode(monkeypatch):
    from src.services.config_service import config

    monkeypatch.setattr(config, "get_str", lambda key, default="": {
        "global_hotkey": "F8",
    }.get(key, default))
    monkeypatch.setattr(config, "get_bool", lambda key, default=False: {
        "enable_translate_hotkeys": True,
        "push_to_talk": False,
    }.get(key, default))

    service = HotkeyService()
    start_cb = MagicMock()
    service.set_start_callback(start_cb)
    service.set_basics_active_callback(lambda: False)

    service._on_press(pynput.keyboard.Key.f8)

    start_cb.assert_called_once()


def test_resolve_key_accepts_uppercase_function_keys():
    service = HotkeyService()
    assert service._resolve_key("F8") == pynput.keyboard.Key.f8
    assert service._resolve_key("f8") == pynput.keyboard.Key.f8
