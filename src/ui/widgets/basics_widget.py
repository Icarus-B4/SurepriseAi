"""
basics_widget.py
SurepriseAI Control Hub – Audio links, Marken-Titel mit Typewriter, App-Aktionen rechts.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.ui.quick_control_button import QuickControlButton
from src.ui.widgets.typewriter_label import TypewriterLabel

BRAND_TEXT = "SurepriseAI"


class BasicsWidget(QWidget):
    """Control Hub: Mikrofon-Steuerung + drei Kernfunktionen der App."""

    mute_toggled = pyqtSignal()
    device_cycle_requested = pyqtSignal()
    history_requested = pyqtSignal()
    transcript_requested = pyqtSignal()
    rewrite_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_muted = False
        self._device_name = ""
        self._status_restore_timer = QTimer(self)
        self._status_restore_timer.setSingleShot(True)
        self._status_restore_timer.timeout.connect(self._restore_brand_title)
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(10)

        # ── Audio-Steuerung ──
        self.left_wing = QWidget(self)
        left_lay = QHBoxLayout(self.left_wing)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(5)
        left_lay.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.btn_mute = QuickControlButton(
            FluentIcons.MICROPHONE, Colors.ACCENT_HEX, self.left_wing
        )
        self.btn_device = QuickControlButton(
            FluentIcons.DEVICE_CYCLE, Colors.TEXT_SECONDARY_HEX, self.left_wing
        )

        left_lay.addWidget(self.btn_mute)
        left_lay.addWidget(self.btn_device)

        self._sep_left = self._make_separator()

        # ── Marken-Titel (Typewriter) ──
        self.title_label = TypewriterLabel(BRAND_TEXT, self, ms_per_char=48)
        self.title_label.setFont(
            Typography.get_font(
                Typography.SMALL,
                weight=Typography.WEIGHT_SEMIBOLD,
                letter_spacing=-2.0,
            )
        )
        self.title_label.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY_HEX}; background: transparent; "
            f"letter-spacing: 0.5px;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setMinimumWidth(108)

        self._sep_right = self._make_separator()

        # ── App-Aktionen (statt PC Power) ──
        self.right_wing = QWidget(self)
        right_lay = QHBoxLayout(self.right_wing)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(5)
        right_lay.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.btn_history = QuickControlButton(
            FluentIcons.HISTORY, Colors.ACCENT_BRIGHT_HEX, self.right_wing
        )
        self.btn_transcript = QuickControlButton(
            FluentIcons.TRANSCRIPT, Colors.SUCCESS_GREEN_HEX, self.right_wing
        )
        self.btn_rewrite = QuickControlButton(
            FluentIcons.REWRITE, Colors.PROCESSING_BLUE_HEX, self.right_wing
        )

        right_lay.addWidget(self.btn_history)
        right_lay.addWidget(self.btn_transcript)
        right_lay.addWidget(self.btn_rewrite)

        lay.addWidget(self.left_wing)
        lay.addWidget(self._sep_left)
        lay.addStretch(1)
        lay.addWidget(self.title_label)
        lay.addStretch(1)
        lay.addWidget(self._sep_right)
        lay.addWidget(self.right_wing)

        self.btn_mute.clicked.connect(self.mute_toggled.emit)
        self.btn_device.clicked.connect(self.device_cycle_requested.emit)
        self.btn_history.clicked.connect(self.history_requested.emit)
        self.btn_transcript.clicked.connect(self.transcript_requested.emit)
        self.btn_rewrite.clicked.connect(self.rewrite_requested.emit)

    @staticmethod
    def _make_separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setStyleSheet(
            f"background: {Colors.BORDER_HEX}; border: none; max-width: 1px;"
        )
        return line

    def show_hub(self) -> None:
        """Wird beim Wechsel in den Hub-Modus aufgerufen."""
        self._status_restore_timer.stop()
        self.title_label.set_brand_text(BRAND_TEXT, restart=True)

    def _handle_mute_click(self):
        self.mute_toggled.emit()

    def set_mute_state(self, muted: bool):
        self._is_muted = muted
        self._update_mute_visual()

    def _update_mute_visual(self):
        if self._is_muted:
            self.btn_mute.setText(FluentIcons.MUTE)
            self.btn_mute.setStyleSheet(self._mute_style(Colors.RECORDING_RED_HEX))
        else:
            self.btn_mute.setText(FluentIcons.MICROPHONE)
            self.btn_mute.setStyleSheet(self._mute_style(Colors.ACCENT_HEX))

    @staticmethod
    def _mute_style(color: str) -> str:
        return (
            f"QPushButton {{ background: rgba(99, 102, 241, 0.12); "
            f"border: 1px solid {color}; border-radius: 16px; "
            f"color: {color}; font-size: 14px; }}"
        )

    def set_active_device(self, name: str) -> None:
        self._device_name = name

    def set_device_name(self, name: str):
        """Kurze Statusmeldung im Titel, danach Typewriter neu."""
        self.set_active_device(name)
        short = name[:18] + "…" if len(name) > 18 else name
        self.title_label.pause()
        self.title_label.setText(short)
        self._status_restore_timer.start(2200)

    def _restore_brand_title(self):
        self.title_label.set_brand_text(BRAND_TEXT, restart=True)

    def reset_confirm_state(self):
        """Kompatibilität – kein Bestätigungsmodus mehr."""
        self._status_restore_timer.stop()
        self.show_hub()
