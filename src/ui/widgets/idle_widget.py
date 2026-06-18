"""
idle_widget.py
Widget für den IDLE-Zustand der Dynamic Island.
Zeigt die Uhrzeit, ein Mikrofon-Icon und den Drag-Griff an.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QTime
from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.ui.drag_handle import DragHandleButton
from src.ui.island_tooltips import _refresh_idle_mic_tooltip


class IdleWidget(QWidget):
    """Widget für den IDLE-Zustand."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Mikrofon-Icon links
        self.mic_icon = QLabel(FluentIcons.MICROPHONE, self)
        self.mic_icon.setObjectName("IconLabel")
        self.mic_icon.setFixedWidth(22)
        self.mic_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center Column (Titel & Uhrzeit / Privacy-Badge)
        self.center_col = QWidget(self)
        center_lay = QVBoxLayout(self.center_col)
        center_lay.setContentsMargins(0, 0, 0, 0)
        center_lay.setSpacing(0)

        self.time_label = QLabel("SurepriseAi", self.center_col)
        self.time_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.privacy_label = QLabel("", self.center_col)
        self.privacy_label.setFont(Typography.get_font(Typography.TINY))
        self.privacy_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY_HEX};")
        self.privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.privacy_label.hide()

        self.app_mode_label = QLabel("", self.center_col)
        self.app_mode_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.app_mode_label.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX};")
        self.app_mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_mode_label.hide()

        center_lay.addWidget(self.time_label)
        center_lay.addWidget(self.privacy_label)
        center_lay.addWidget(self.app_mode_label)

        # Symmetrische Anordnung
        lay.addWidget(self.mic_icon)
        lay.addStretch(1)
        lay.addWidget(self.center_col)
        lay.addStretch(1)

        # Drag-Griff rechts
        self.drag_handle = DragHandleButton(self)
        lay.addWidget(self.drag_handle)

        # Timer für die Uhrzeit
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()

    def update_time(self):
        """Aktualisiert die Uhrzeit im Label."""
        current_time = QTime.currentTime().toString("HH:mm")
        self.time_label.setText(f"SurepriseAi  |  {current_time}")

    def set_privacy_badge(self, text: str | None):
        """Zeigt oder verbirgt das Privacy-Badge unter der Uhrzeit."""
        if text:
            self.privacy_label.setText(text)
            self.privacy_label.show()
        else:
            self.privacy_label.hide()

    def set_app_mode(self, app_key: str | None, style_label: str | None = None) -> None:
        """Zeigt den aktiven App-Modus unter der Uhrzeit."""
        if app_key and style_label:
            self.app_mode_label.setText(f"📱 {app_key} · {style_label}")
            self.app_mode_label.show()
        else:
            self.app_mode_label.hide()

    def set_audio_hint(self, device_name: str, muted: bool = False) -> None:
        """Zeigt Mikrofon-Status im Idle-Widget (Tooltip + Icon)."""
        if muted:
            self.mic_icon.setText(FluentIcons.MUTE)
        else:
            self.mic_icon.setText(FluentIcons.MICROPHONE)
        _refresh_idle_mic_tooltip(self, device_name)
