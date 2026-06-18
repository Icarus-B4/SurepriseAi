"""
island_pill.py
Die visuelle Kapsel (Pill) der Dynamic Island.
Verwaltet die Sub-Widgets für jeden Zustand (Idle, Rec, Proc, Success, Expanded, Basics).
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
from src.ui.design_tokens import Colors, Typography, FluentIcons, IslandSize, AnimationTokens
from src.ui.expanded_pill_widget import ExpandedPillWidget
from src.ui.island_states import IslandState

# Importiere die modularisierten Widgets
from src.ui.widgets.idle_widget import IdleWidget
from src.ui.widgets.recording_widget import RecordingWidget
from src.ui.widgets.processing_widget import ProcessingWidget
from src.ui.widgets.success_widget import SuccessWidget
from src.ui.widgets.basics_widget import BasicsWidget


class IslandPill(QFrame):
    """Haupt-Kapsel (Pill) der Dynamic Island mit State-Umschaltung."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PillContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._corner_radius = IslandSize.BORDER_RADIUS
        self._apply_pill_style()
        self._init_ui()

    def _pill_qss(self, border: str) -> str:
        """Erzeugt das Pill-Stylesheet für Normal- und Pulse-Look."""
        return f"""
            QFrame#PillContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.PILL_GRADIENT_TOP},
                    stop:1 {Colors.PILL_GRADIENT_BOTTOM}
                );
                border: {border};
                border-radius: {self._corner_radius}px;
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: {Typography.SMALL}pt;
                background: transparent;
            }}
            QLabel#IconLabel {{
                font-family: "{FluentIcons.FONT_FAMILY}";
                font-size: {Typography.BODY}pt;
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
        """

    def _apply_pill_style(self):
        self.setStyleSheet(self._pill_qss(f"1px solid {Colors.BORDER_HIGHLIGHT}"))

    def set_corner_radius(self, radius: int) -> None:
        """Passt die Ecken-Rundung an (Pill vs. Karten-Modus)."""
        self._corner_radius = radius
        self._apply_pill_style()

    def _init_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 16, 0)
        self.layout.setSpacing(8)

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.stacked_widget)

        # Widgets instanziieren
        self.idle_widget = IdleWidget(self)
        self.rec_widget = RecordingWidget(self)
        self.proc_widget = ProcessingWidget(self)
        self.success_widget = SuccessWidget(self)
        self.expanded_widget = ExpandedPillWidget(self)
        self.basics_widget = BasicsWidget(self)

        # Kompatibilität für transcript_edit behalten
        self.transcript_edit = self.expanded_widget.transcript_edit

        # StackedWidget befüllen (Reihenfolge analog zu den States)
        self.stacked_widget.addWidget(self.idle_widget)       # 0 (IDLE)
        self.stacked_widget.addWidget(self.rec_widget)        # 1 (RECORDING)
        self.stacked_widget.addWidget(self.proc_widget)       # 2 (PROCESSING)
        self.stacked_widget.addWidget(self.success_widget)    # 3 (SUCCESS)
        self.stacked_widget.addWidget(self.expanded_widget)   # 4 (EXPANDED)
        self.stacked_widget.addWidget(self.basics_widget)     # 5 (BASICS)

    @property
    def proc_label(self):
        """Kompatibilität für ältere Controller-Referenzen."""
        return self.proc_widget.proc_label

    def wheelEvent(self, event):
        """Leitet Mausrad an den zentralen InputFilter weiter."""
        window = self.parent()
        if window and hasattr(window, "input_filter"):
            window.input_filter._handle_wheel(event)
        else:
            super().wheelEvent(event)

    def start_recording(self):
        self.stacked_widget.setCurrentIndex(1)
        self.rec_widget.start_recording()

    def stop_recording(self):
        self.rec_widget.stop_recording()

    def start_processing(self):
        self.stacked_widget.setCurrentIndex(2)
        self.proc_widget.start_processing()

    def stop_processing(self):
        self.proc_widget.stop_processing()

    def show_success(self, text: str, raw: str = "") -> bool:
        self.stacked_widget.setCurrentIndex(3)
        return self.success_widget.show_success(text, raw=raw)

    def set_expanded(self, text: str):
        self.stacked_widget.setCurrentIndex(4)
        self.transcript_edit.setText(text)

    def set_idle(self):
        self.stacked_widget.setCurrentIndex(0)
        self.idle_widget.update_time()

    def set_privacy_badge(self, text: str | None) -> None:
        """Leitet Privacy-Badge an das IdleWidget weiter."""
        self.idle_widget.set_privacy_badge(text)

    def set_app_mode_badge(self, app_key: str | None, style_label: str | None = None) -> None:
        """Zeigt den App-Modus in Idle- und Recording-Widget."""
        self.idle_widget.set_app_mode(app_key, style_label)
        self.rec_widget.set_app_mode(app_key, style_label)

    def set_basics(self):
        self.stacked_widget.setCurrentIndex(5)
        self.basics_widget.show_hub()

    def play_settle_pulse(self) -> None:
        """Kurzer Indigo-Glow beim Wechsel Aufnahme → Verarbeitung."""
        self.setStyleSheet(self._pill_qss(f"2px solid {Colors.ACCENT_BRIGHT_HEX}"))
        QTimer.singleShot(AnimationTokens.NORMAL, self._apply_pill_style)
