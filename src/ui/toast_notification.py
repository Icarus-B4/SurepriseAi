"""
toast_notification.py
Status-Toast-Benachrichtigungen und Live-Transkriptions-Anzeige.
Positioniert sich unterhalb der Dynamic Island und blendet sich sanft ein/aus.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from src.ui.design_tokens import Colors, Typography


class ToastNotification(QWidget):
    """
    Schwebendes, rahmenloses Toast-Fenster.
    Unterstützt Standard-Pills (Erfolg, Fehler) und wachsende Live-Transkripte.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

        self._is_live = False
        self._init_ui()

    def _init_ui(self):
        self.container = QWidget(self)
        self.container.setObjectName("ToastContainer")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        # Titel für Live-Modus
        self.title_label = QLabel("", self)
        self.title_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        self.title_label.hide()
        layout.addWidget(self.title_label)

        # Haupttext
        self.label = QLabel("", self)
        self.label.setFont(Typography.get_font(Typography.SMALL))
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._apply_style(is_live=False)

    def _apply_style(self, is_live: bool, text_color: str = Colors.TEXT_PRIMARY_HEX):
        """Wendet QSS-Styling an. Live-Transkripte erhalten ein anderes Layout."""
        self._is_live = is_live
        
        # Kreisrunde Pille für kurze Toasts, abgerundeter Kasten für Live-Transkript
        radius = 12 if is_live else 20
        padding_v = 12 if is_live else 8
        bg_color = "rgba(13, 13, 15, 0.95)" # Edles, dunkles Schwarz

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

    def show_message(self, message: str, color_hex: str = Colors.TEXT_PRIMARY_HEX, duration_ms: int = 2000):
        """Zeigt eine Standard-Benachrichtigung an (z. B. Kopiert, Fehler)."""
        self.hide_timer.stop()
        self._is_live = False
        self.title_label.hide()
        self.label.setText(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style(is_live=False, text_color=color_hex)

        self._position_and_show()
        self.fade_animation.stop()
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

        self.hide_timer.start(duration_ms)

    def show_live_transcript(self, text: str):
        """Zeigt den transkribierten Text live an, ohne auszublenden."""
        self.hide_timer.stop()
        self.fade_animation.stop()
        self._is_live = True

        self.title_label.setText("LIVE-TRANSKRIPTION")
        self.title_label.show()
        self.label.setText(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._apply_style(is_live=True, text_color=Colors.TEXT_PRIMARY_HEX)

        self._position_and_show()
        self.setWindowOpacity(1.0)
        self.raise_()

    def end_live_mode(self):
        """Beendet den Live-Modus und blendet das Fenster aus."""
        self._is_live = False
        self.fade_out()

    def show_success(self, message: str):
        self.show_message(message, Colors.SUCCESS_GREEN_HEX, 2000)

    def show_error(self, message: str):
        self.show_message(message, Colors.RECORDING_RED_HEX, 3000)

    def fade_out(self):
        """Blendet das Toast-Fenster sanft aus."""
        if self._is_live:
            return  # Während Live-Transkription nicht ausblenden
        self.fade_animation.stop()
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()

    def _position_and_show(self):
        self.adjustSize()
        screen = self.screen()
        if screen:
            screen_geom = screen.geometry()
            x = int(screen_geom.left() + (screen_geom.width() - self.width()) / 2.0)
            y = int(screen_geom.top() + 75)  # Direkt unter der Dynamic Island
            self.move(x, y)
        self.show()
