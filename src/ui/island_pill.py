"""
island_pill.py
Die visuelle Kapsel (Pill) der Dynamic Island.
Verwaltet die Sub-Widgets für jeden Zustand (Idle, Rec, Proc, Success, Expanded, Basics).
"""

from PyQt6.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStackedWidget, QPushButton, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QTime
from src.ui.design_tokens import Colors, Typography, FluentIcons, IslandSize, AnimationTokens
from src.ui.waveform_widget import WaveformWidget
from src.ui.expanded_pill_widget import ExpandedPillWidget
from src.ui.drag_handle import DragHandleButton
from src.ui.island_states import IslandState


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
        """Erzeugt das Pill-Stylesheet – eine Quelle für Normal- und Pulse-Look.

        `border` ist die komplette CSS-border-Deklaration (z. B. '1px solid …').
        Der Hintergrund ist ein subtiler vertikaler Glas-Gradient (oben heller).
        """
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
        
        # ── 1. IDLE STATE ──
        self.idle_widget = QWidget(self)
        idle_lay = QHBoxLayout(self.idle_widget)
        idle_lay.setContentsMargins(0, 0, 0, 0)
        self.mic_icon = QLabel(FluentIcons.MICROPHONE, self.idle_widget)
        self.mic_icon.setObjectName("IconLabel")
        self.mic_icon.setFixedWidth(22)
        self.mic_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.center_col = QWidget(self.idle_widget)
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
        center_lay.addWidget(self.time_label)
        center_lay.addWidget(self.privacy_label)

        # Symmetrie: Mic links + Griff rechts (je 22 px), Titel dazwischen zentriert
        idle_lay.addWidget(self.mic_icon)
        idle_lay.addStretch(1)
        idle_lay.addWidget(self.center_col)
        idle_lay.addStretch(1)

        self.drag_handle = DragHandleButton(self.idle_widget)
        idle_lay.addWidget(self.drag_handle)
        
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)
        self._update_time()
        
        # ── 2. RECORDING STATE ──
        self.rec_widget = QWidget(self)
        rec_lay = QHBoxLayout(self.rec_widget)
        rec_lay.setContentsMargins(0, 0, 0, 0)
        rec_icon = QLabel(FluentIcons.MICROPHONE, self.rec_widget)
        rec_icon.setObjectName("IconLabel")
        rec_icon.setStyleSheet(f"color: {Colors.RECORDING_RED_HEX};")
        self.rec_timer_label = QLabel("00:00", self.rec_widget)
        self.rec_timer_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        self.waveform = WaveformWidget(self.rec_widget)
        rec_lay.addWidget(rec_icon)
        rec_lay.addWidget(self.rec_timer_label)
        rec_lay.addWidget(self.waveform)
        rec_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.rec_start_time = None
        self.rec_duration_timer = QTimer(self)
        self.rec_duration_timer.timeout.connect(self._update_rec_duration)

        # ── 3. PROCESSING STATE ──
        self.proc_widget = QWidget(self)
        proc_lay = QHBoxLayout(self.proc_widget)
        proc_lay.setContentsMargins(0, 0, 0, 0)
        self.proc_icon = QLabel(FluentIcons.PROCESSING, self.proc_widget)
        self.proc_icon.setObjectName("IconLabel")
        self.proc_icon.setStyleSheet(f"color: {Colors.PROCESSING_BLUE_HEX};")
        self.proc_label = QLabel("Bereinige...", self.proc_widget)
        self.proc_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        proc_lay.addWidget(self.proc_icon)
        proc_lay.addWidget(self.proc_label)
        proc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.spinner_angle = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._rotate_spinner)
        
        # ── 4. SUCCESS STATE ──
        self.success_widget = QWidget(self)
        succ_lay = QHBoxLayout(self.success_widget)
        succ_lay.setContentsMargins(0, 0, 0, 0)
        succ_icon = QLabel(FluentIcons.CHECKMARK, self.success_widget)
        succ_icon.setObjectName("IconLabel")
        succ_icon.setStyleSheet(f"color: {Colors.SUCCESS_GREEN_HEX};")
        self.success_label = QLabel("Kopiert!", self.success_widget)
        self.success_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        self.success_label.setStyleSheet(f"color: {Colors.SUCCESS_GREEN_HEX};")
        self.success_text_preview = QLabel("", self.success_widget)
        self.success_text_preview.setFont(Typography.get_font(Typography.TINY))
        self.success_text_preview.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        succ_lay.addWidget(succ_icon)
        succ_lay.addWidget(self.success_label)
        succ_lay.addWidget(self.success_text_preview)
        succ_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── 5. EXPANDED STATE (Ausgelagert) ──
        self.expanded_widget = ExpandedPillWidget(self)
        self.transcript_edit = self.expanded_widget.transcript_edit

        # ── 6. BASICS STATE (Control Hub) ──
        self.basics_widget = QWidget(self)
        basics_lay = QHBoxLayout(self.basics_widget)
        basics_lay.setContentsMargins(0, 0, 0, 0)
        
        self.basics_prev_btn = QPushButton("<", self.basics_widget)
        self.basics_prev_btn.setFixedSize(20, 20)
        self.basics_prev_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #8E8E93; font-weight: bold; } "
            "QPushButton:hover { color: white; }"
        )
        self.basics_prev_btn.clicked.connect(self._goto_idle)
        
        self.basics_label = QLabel("Basics", self.basics_widget)
        self.basics_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        
        self.basics_next_btn = QPushButton(">", self.basics_widget)
        self.basics_next_btn.setFixedSize(20, 20)
        self.basics_next_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #8E8E93; font-weight: bold; } "
            "QPushButton:hover { color: white; }"
        )
        self.basics_next_btn.clicked.connect(self._goto_idle)
        
        basics_lay.addWidget(self.basics_prev_btn)
        basics_lay.addSpacing(6)
        basics_lay.addWidget(self.basics_label)
        basics_lay.addSpacing(6)
        basics_lay.addWidget(self.basics_next_btn)
        basics_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Widgets hinzufügen
        self.stacked_widget.addWidget(self.idle_widget)       # 0
        self.stacked_widget.addWidget(self.rec_widget)        # 1
        self.stacked_widget.addWidget(self.proc_widget)       # 2
        self.stacked_widget.addWidget(self.success_widget)    # 3
        self.stacked_widget.addWidget(self.expanded_widget)   # 4
        self.stacked_widget.addWidget(self.basics_widget)     # 5

    def wheelEvent(self, event):
        """Erlaubt Wechsel zwischen IDLE und BASICS per Mausrad."""
        curr_state = self.parent().state_machine.current
        if curr_state in (IslandState.IDLE, IslandState.BASICS):
            delta = event.angleDelta().y()
            if delta > 0 and curr_state == IslandState.IDLE:
                self.parent().state_machine.transition_to(IslandState.BASICS)
            elif delta < 0 and curr_state == IslandState.BASICS:
                self.parent().state_machine.transition_to(IslandState.IDLE)
            event.accept()
        else:
            super().wheelEvent(event)

    def _goto_idle(self):
        self.parent().state_machine.transition_to(IslandState.IDLE)

    def _update_time(self):
        current_time = QTime.currentTime().toString("HH:mm")
        self.time_label.setText(f"SurepriseAi  |  {current_time}")

    def _update_rec_duration(self):
        if self.rec_start_time:
            secs = int(QTime.currentTime().secsTo(self.rec_start_time)) * -1
            self.rec_timer_label.setText(f"{secs // 60:02d}:{secs % 60:02d}")

    def _rotate_spinner(self):
        spinners = ["|", "/", "-", "\\"]
        self.spinner_angle = (self.spinner_angle + 1) % len(spinners)
        self.proc_icon.setText(spinners[self.spinner_angle])
        
    def start_recording(self):
        self.stacked_widget.setCurrentIndex(1)
        self.waveform.reset_waveform()
        self.rec_timer_label.setText("00:00")
        self.rec_start_time = QTime.currentTime()
        self.rec_duration_timer.start(1000)

    def stop_recording(self):
        self.rec_duration_timer.stop()
        self.waveform.reset_waveform()

    def start_processing(self):
        self.stacked_widget.setCurrentIndex(2)
        self.spinner_timer.start(150)

    def stop_processing(self):
        self.spinner_timer.stop()
        self.proc_icon.setText(FluentIcons.PROCESSING)
        self.proc_label.setText("Bereinige...")

    def show_success(self, text: str):
        self.stacked_widget.setCurrentIndex(3)
        preview = text.replace("\n", " ")
        if len(preview) > 30:
            preview = preview[:27] + "..."
        self.success_text_preview.setText(preview)
        
    def set_expanded(self, text: str):
        self.stacked_widget.setCurrentIndex(4)
        self.transcript_edit.setText(text)

    def set_idle(self):
        self.stacked_widget.setCurrentIndex(0)
        self._update_time()

    def set_privacy_badge(self, text: str | None) -> None:
        """Zeigt oder verbirgt das Privacy-Badge unter der Uhrzeit."""
        if text:
            self.privacy_label.setText(text)
            self.privacy_label.show()
        else:
            self.privacy_label.hide()

    def set_basics(self):
        self.stacked_widget.setCurrentIndex(5)
        self.basics_label.setText("Basics")

    def play_settle_pulse(self) -> None:
        """Kurzer Indigo-Glow beim Wechsel Aufnahme → Verarbeitung."""
        self.setStyleSheet(self._pill_qss(f"2px solid {Colors.ACCENT_BRIGHT_HEX}"))
        QTimer.singleShot(AnimationTokens.NORMAL, self._apply_pill_style)
