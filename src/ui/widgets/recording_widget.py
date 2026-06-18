"""
recording_widget.py
Widget für den RECORDING-Zustand der Dynamic Island.
Zeigt ein rotes Mikrofon-Icon, die Aufnahmedauer und eine Wellenform-Visualisierung.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QTime
from src.ui.design_tokens import Colors, Typography, FluentIcons, IslandSize
from src.ui.waveform_widget import WaveformWidget
from src.ui.widgets.led_level_indicator import LedLevelIndicator


class RecordingWidget(QWidget):
    """Widget für den Aufnahme-Zustand (Recording)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rec_start_time = None
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Rotes Mikrofon-Icon
        self.rec_icon = QLabel(FluentIcons.MICROPHONE, self)
        self.rec_icon.setObjectName("IconLabel")
        self.rec_icon.setStyleSheet(f"color: {Colors.RECORDING_RED_HEX};")

        # Zeitanzeige (z.B. 00:00)
        self.rec_timer_label = QLabel("00:00", self)
        self.rec_timer_label.setFont(Typography.get_font(Typography.SMALL, bold=True))

        self.app_mode_label = QLabel("", self)
        self.app_mode_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.app_mode_label.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX};")
        self.app_mode_label.hide()

        # LED-Pegel – sichtbar während der Aufnahme
        self.level_indicator = LedLevelIndicator(self)

        # Wellenform-Widget (nimmt den verfügbaren Platz ein)
        self.waveform = WaveformWidget(self)
        self.waveform.setMinimumSize(
            IslandSize.WAVEFORM_WIDTH,
            IslandSize.WAVEFORM_MAX_H,
        )
        self.waveform.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        lay.addWidget(self.rec_icon)
        lay.addWidget(self.rec_timer_label)
        lay.addWidget(self.app_mode_label)
        lay.addWidget(self.level_indicator)
        lay.addWidget(self.waveform, 1)

        # Timer für die Aufnahmedauer
        self.rec_duration_timer = QTimer(self)
        self.rec_duration_timer.timeout.connect(self._update_rec_duration)

    def start_recording(self):
        """Startet die visuelle Aufnahme (Wellenform und Timer)."""
        self.waveform.reset_waveform()
        self.level_indicator.reset()
        self.rec_timer_label.setText("00:00")
        self.rec_start_time = QTime.currentTime()
        self.rec_duration_timer.start(1000)

    def stop_recording(self):
        """Stoppt den Aufnahmetimer und die Wellenform."""
        self.rec_duration_timer.stop()
        self.waveform.reset_waveform()
        self.level_indicator.reset()

    def set_level(self, level: float) -> None:
        """Aktualisiert den LED-Pegel während der Aufnahme."""
        self.level_indicator.set_level(level)

    def set_app_mode(self, app_key: str | None, style_label: str | None = None) -> None:
        """Zeigt den aktiven App-Modus während der Aufnahme."""
        if app_key and style_label:
            self.app_mode_label.setText(f"{app_key} · {style_label}")
            self.app_mode_label.show()
        else:
            self.app_mode_label.hide()

    def _update_rec_duration(self):
        """Aktualisiert die Aufnahmedauer im Label."""
        if self.rec_start_time:
            secs = int(QTime.currentTime().secsTo(self.rec_start_time)) * -1
            self.rec_timer_label.setText(f"{secs // 60:02d}:{secs % 60:02d}")
