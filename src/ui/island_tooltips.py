"""
island_tooltips.py
Zentrale Tooltips für alle Dynamic-Island-Zustände und Buttons.
"""

from src.services.audio_devices import input_device_display_name
from src.services.config_service import config
from src.services.style_definitions import STYLE_LABELS
from src.ui.design_tokens import FluentIcons
from src.utils.translation import tr


def _hotkey(key: str, default: str) -> str:
    return config.get_str(key, default).upper()


def refresh_island_tooltips(window) -> None:
    """Setzt/aktualisiert alle Island-Tooltips (Sprache, Hotkeys, Gerät)."""
    pill = window.pill
    hotkey = _hotkey("global_hotkey", "f8")
    device = input_device_display_name(
        config.get_str("recording_device", "default")
    )

    if hasattr(window, "presence_bar"):
        window.presence_bar.setToolTip(tr("island_presence_hint"))

    idle = pill.idle_widget
    idle.time_label.setToolTip(
        tr("island_idle_hint").format(hotkey=hotkey)
    )
    idle.center_col.setToolTip(idle.time_label.toolTip())
    idle.drag_handle.setToolTip(tr("island_drag"))
    _refresh_idle_mic_tooltip(idle, device)

    rec = pill.rec_widget
    rec.rec_icon.setToolTip(
        tr("island_recording").format(hotkey=hotkey)
    )
    rec.rec_timer_label.setToolTip(rec.rec_icon.toolTip())
    rec.level_indicator.setToolTip(tr("island_level"))
    rec.waveform.setToolTip(tr("island_waveform"))

    proc = pill.proc_widget
    proc.proc_icon.setToolTip(tr("island_processing"))
    proc.proc_label.setToolTip(tr("island_processing"))

    succ = pill.success_widget
    succ.succ_icon.setToolTip(tr("island_success"))
    succ.success_label.setToolTip(tr("island_success"))
    succ.success_text_preview.setToolTip(tr("island_success"))

    basics = pill.basics_widget
    muted = basics._is_muted
    basics.btn_mute.setToolTip(
        tr("island_mute_on") if muted else tr("island_mute_off")
    )
    basics.btn_device.setToolTip(
        tr("island_device").format(device=device)
    )
    basics.btn_history.setToolTip(tr("island_hub_history"))
    basics.btn_transcript.setToolTip(tr("island_hub_transcript"))
    rewrite_tip = tr("island_hub_rewrite").format(
        hotkey=_hotkey("selected_text_hotkey", "f9")
    )
    basics.btn_rewrite.setToolTip(rewrite_tip)
    if not basics._status_restore_timer.isActive():
        basics.title_label.setToolTip(tr("island_basics_title_hint"))

    expanded = pill.expanded_widget
    expanded.box_copy_btn.setToolTip(tr("island_copy"))
    expanded.exp_close_btn.setToolTip(tr("island_close"))
    for key, btn in expanded.chips.items():
        label = STYLE_LABELS.get(key, key)
        btn.setToolTip(tr("island_style_apply").format(style=label))


def _refresh_idle_mic_tooltip(idle, device: str) -> None:
    """Behält Geräte-/Mute-Hinweis am Mikrofon-Icon."""
    short = device[:24] + "…" if len(device) > 24 else device
    icon = idle.mic_icon.text()
    if icon == FluentIcons.MUTE:
        idle.mic_icon.setToolTip(f"{tr('island_mute_on')}\n{short}")
    else:
        idle.mic_icon.setToolTip(f"{tr('island_device_short')}\n{short}")
