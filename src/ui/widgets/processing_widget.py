"""
processing_widget.py
Widget für den PROCESSING-Zustand der Dynamic Island.
Zeigt ein rotierendes Text-Spinner-Symbol und den Verarbeitungsstatus an.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from src.ui.design_tokens import Colors, Typography, FluentIcons


class ProcessingWidget(QWidget):
    """Widget für den Verarbeitungs-Zustand (Processing)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.spinner_angle = 0
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon für den Spinner (blau gefärbt)
        self.proc_icon = QLabel(FluentIcons.PROCESSING, self)
        self.proc_icon.setObjectName("IconLabel")
        self.proc_icon.setStyleSheet(f"color: {Colors.PROCESSING_BLUE_HEX};")

        # Status Label
        self.proc_label = QLabel("Bereinige...", self)
        self.proc_label.setFont(Typography.get_font(Typography.SMALL, bold=True))

        lay.addWidget(self.proc_icon)
        lay.addWidget(self.proc_label)

        # Timer für die Spinner-Animation (Text-Striche rotieren)
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._rotate_spinner)

    def set_message(self, text: str) -> None:
        """Setzt die Verarbeitungsmeldung."""
        self.proc_label.setText(text)
        print(f"[Processing] {text}")

    def start_processing(self):
        """Startet den Spinner-Timer."""
        self.spinner_timer.start(150)

    def stop_processing(self):
        """Stoppt den Spinner-Timer und setzt das Icon zurück."""
        self.spinner_timer.stop()
        self.proc_icon.setText(FluentIcons.PROCESSING)
        self.proc_label.setText("Bereinige...")

    def _rotate_spinner(self):
        """Rotations-Schritt für den Text-Spinner."""
        spinners = ["|", "/", "-", "\\"]
        self.spinner_angle = (self.spinner_angle + 1) % len(spinners)
        self.proc_icon.setText(spinners[self.spinner_angle])
