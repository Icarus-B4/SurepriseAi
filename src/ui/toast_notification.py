"""
toast_notification.py
Status-Toast-Benachrichtigungen und Live-Transkriptions-Anzeige.
Positioniert sich unterhalb der Dynamic Island und blendet sich sanft ein/aus.
"""

import html
import re

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from src.ui.design_tokens import Colors, Typography

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


class ToastNotification(QWidget):
    """Schwebendes Toast-Fenster für Status, Fehler und Live-Transkripte."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

        self._is_live = False
        self._live_plain = ""
        self._init_ui()

    def _init_ui(self):
        self.container = QWidget(self)
        self.container.setObjectName("ToastContainer")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        self.title_label = QLabel("", self)
        self.title_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        self.title_label.hide()
        layout.addWidget(self.title_label)

        self.label = QLabel("", self)
        self.label.setFont(Typography.get_font(Typography.SMALL))
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.label)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._apply_style(is_live=False)

    def _apply_style(self, is_live: bool, text_color: str = Colors.TEXT_PRIMARY_HEX):
        self._is_live = is_live
        radius = 12 if is_live else 20
        padding_v = 12 if is_live else 8
        bg_color = "rgba(13, 13, 15, 0.95)"

        self.container.setStyleSheet(f"""
            QWidget#ToastContainer {{
                background-color: {bg_color};
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: {radius}px;
                padding: {padding_v}px 16px;
            }}
            QLabel {{
                color: {text_color};
                font-family: "{Typography.FONT_FAMILY}";
                background: transparent;
            }}
        """)

    def show_message(
        self,
        message: str,
        color_hex: str = Colors.TEXT_PRIMARY_HEX,
        duration_ms: int = 2000,
        *,
        sticky: bool = False,
    ):
        """Zeigt eine Benachrichtigung. sticky=True hält den Toast bis zum nächsten Aufruf."""
        self.hide_timer.stop()
        self._is_live = False
        self._live_plain = ""
        self.title_label.hide()
        self.label.setText(html.escape(message))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style(is_live=False, text_color=color_hex)

        self._position_and_show()
        self.fade_animation.stop()
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

        if not sticky:
            self.hide_timer.start(duration_ms)

    def show_live_transcript(self, text: str):
        self.hide_timer.stop()
        self.fade_animation.stop()
        self._is_live = True
        self._live_plain = text.strip()

        self.title_label.setText("LIVE-TRANSKRIPTION")
        self.title_label.show()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._render_live_html(self._live_plain, settled=False)
        self._apply_style(is_live=True)

        self._position_and_show()
        self.setWindowOpacity(1.0)
        self.raise_()

    def settle_live_transcript(self, text: str | None = None) -> None:
        if not self._is_live:
            return
        final = (text or self._live_plain).strip()
        self._live_plain = final
        self.title_label.setText("TRANSKRIPT")
        self._render_live_html(final, settled=True)
        self._position_and_show()

    def _render_live_html(self, text: str, settled: bool) -> None:
        if not text or text == "Höre zu…":
            self.label.setText(
                f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
                f'font-style:italic;">{html.escape(text or "Höre zu…")}</span>'
            )
            return

        if settled:
            self.label.setText(
                f'<span style="color:{Colors.TEXT_PRIMARY_HEX};">'
                f"{html.escape(text)}</span>"
            )
            return

        parts = _SENTENCE_SPLIT.split(text.strip())
        if len(parts) == 1 and not re.search(r"[.!?…]$", text.strip()):
            self.label.setText(
                f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
                f'font-style:italic;">{html.escape(text.strip())}</span>'
            )
            return

        if re.search(r"[.!?…]$", text.strip()):
            final_part, partial_part = text.strip(), ""
        else:
            final_part = " ".join(parts[:-1]).strip()
            partial_part = parts[-1].strip()

        chunks: list[str] = []
        if final_part:
            chunks.append(
                f'<span style="color:{Colors.TEXT_PRIMARY_HEX};">'
                f"{html.escape(final_part)}</span>"
            )
        if partial_part:
            chunks.append(
                f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
                f'font-style:italic;">{html.escape(partial_part)}</span>'
            )
        self.label.setText(" ".join(chunks) if chunks else html.escape(text))

    def end_live_mode(self):
        self._is_live = False
        self.fade_out()

    def show_success(self, message: str, duration_ms: int = 3500):
        self.show_message(message, Colors.SUCCESS_GREEN_HEX, duration_ms)

    def show_error(self, message: str, duration_ms: int = 6000):
        self.show_message(message, Colors.RECORDING_RED_HEX, duration_ms)

    def show_update(self, message: str):
        """Länger sichtbarer Toast für Update-Hinweise."""
        self.show_message(message, Colors.SUCCESS_GREEN_HEX, duration_ms=10_000, sticky=True)

    def fade_out(self):
        if self._is_live:
            return
        self.fade_animation.stop()
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        try:
            self.fade_animation.finished.disconnect(self.hide)
        except TypeError:
            pass
        self.fade_animation.finished.connect(
            self.hide,
            Qt.ConnectionType.SingleShotConnection,
        )
        self.fade_animation.start()

    def _position_and_show(self):
        self.adjustSize()
        screen = self.screen()
        if screen:
            screen_geom = screen.geometry()
            x = int(screen_geom.left() + (screen_geom.width() - self.width()) / 2.0)
            y = int(screen_geom.top() + 75)
            self.move(x, y)
        self.show()
        self.raise_()
