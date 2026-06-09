"""
dynamic_island.py
Haupt-Overlay-Fenster (Dynamic Island) in PyQt6.
Verwaltet das rahmenlose transparente Trägerfenster.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QTimer
from src.ui.design_tokens import IslandSize, Colors, AnimationTokens
from src.ui.island_pill import IslandPill
from src.ui.island_states import IslandState
from src.ui.settings_panel import SettingsWindow
from src.ui.quick_control_button import QuickControlButton


class DynamicIslandWindow(QWidget):
    def __init__(self, state_machine, parent=None):
        super().__init__(parent)
        self.state_machine = state_machine
        
        # Windows-Overlay-Konfiguration (Trägerfenster)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(IslandSize.WINDOW_WIDTH, IslandSize.WINDOW_HEIGHT)
        self.setAcceptDrops(True)
        self.file_dropped_callback = None
        self._user_moved = False  # True sobald der Nutzer das Fenster per Drag verschoben hat
        
        self._init_ui()
        self._setup_position()
        self._init_quick_controls()
        
        # Hover-Timer und Opacity Animation Setup
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._check_hover)
        self.hover_timer.start(100) # 100ms Polling
        self.is_hovered = False
        
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(AnimationTokens.FAST)
        self.setWindowOpacity(0.0) # Start unsichtbar im Idle
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # State-Machine Listener registrieren
        self.state_machine.add_listener(self._on_state_changed)

    def _init_quick_controls(self):
        self.btn_power = QuickControlButton("⏻", Colors.RECORDING_RED_HEX, self)
        self.btn_restart = QuickControlButton("↻", Colors.PROCESSING_BLUE_HEX, self)
        self.btn_sleep = QuickControlButton("💤", Colors.ACCENT_HEX, self)
        
        self.btn_power.hide()
        self.btn_restart.hide()
        self.btn_sleep.hide()
        
        self.btn_power.clicked.connect(self._handle_power_click)
        self.btn_restart.clicked.connect(self._handle_restart_click)
        self.btn_sleep.clicked.connect(self._handle_sleep_click)
        
        self._confirm_state = None  # "power" / "restart" / None
        self._confirm_timer = QTimer(self)
        self._confirm_timer.setSingleShot(True)
        self._confirm_timer.timeout.connect(self._reset_confirm_state)

    def _check_hover(self):
        # Nur relevant im IDLE- und BASICS-Zustand (ansonsten immer sichtbar)
        if not (self.state_machine.is_idle or self.state_machine.is_basics):
            if self.windowOpacity() < 1.0:
                self._fade_to(1.0)
            return

        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QApplication
        pos = QCursor.pos()
        screen_rect = QApplication.primaryScreen().geometry()
        center_x = screen_rect.width() / 2
        
        # Hover-Zone: 250px links/rechts von der Mitte (etwas breiter wegen Quick Controls), obere 120px
        is_in_zone = (center_x - 250 <= pos.x() <= center_x + 250) and (pos.y() <= 120)
        
        if self.windowOpacity() > 0:
            if self.geometry().contains(pos):
                is_in_zone = True

        if is_in_zone:
            self.is_hovered = True
            self._fade_to(1.0)
        else:
            self.is_hovered = False
            self._fade_to(0.0)

    def _fade_to(self, target_opacity: float):
        if self.windowOpacity() == target_opacity: return
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(target_opacity)
        self.opacity_anim.start()
        
        # Klick-Durchlässigkeit anpassen
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, target_opacity == 0.0)

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        self.pill = IslandPill(self)
        self.pill.setFixedSize(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
        self.layout.addWidget(self.pill)

    def mark_user_positioned(self) -> None:
        """Merkt sich, dass der Nutzer die Position manuell gesetzt hat."""
        self._user_moved = True

    def reset_to_start_position(self) -> None:
        """Setzt die Island zurück nach oben mittig (Startposition)."""
        self._user_moved = False
        self._setup_position(force=True)

    def _setup_position(self, force: bool = False) -> None:
        """Zentriert oben – nur beim Start, nicht nach manuellem Verschieben."""
        if self._user_moved and not force:
            return
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = int(geom.left() + (geom.width() - self.width()) / 2.0)
            y = int(geom.top() + 10)
            self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        # Kein _setup_position() hier – show() würde sonst nach jedem Klick zurückspringen

    # ── Animierbare Properties ──

    def _get_pill_width(self) -> int:
        return self.pill.width()

    def _set_pill_width(self, w: int):
        self.pill.setFixedWidth(w)
        # Wenn im Basics Modus, müssen wir die Buttons mitverschieben
        if self.state_machine.is_basics:
            self._show_basics_buttons()
        
    pill_width = pyqtProperty(int, fget=_get_pill_width, fset=_set_pill_width)

    def _get_pill_height(self) -> int:
        return self.pill.height()

    def _set_pill_height(self, h: int):
        self.pill.setFixedHeight(h)
        
    pill_height = pyqtProperty(int, fget=_get_pill_height, fset=_set_pill_height)

    def animate_to(self, target_w: int, target_h: int):
        self.anim_w = QPropertyAnimation(self, b"pill_width")
        self.anim_w.setDuration(AnimationTokens.NORMAL)
        self.anim_w.setStartValue(self.pill.width())
        self.anim_w.setEndValue(target_w)
        self.anim_w.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.anim_h = QPropertyAnimation(self, b"pill_height")
        self.anim_h.setDuration(AnimationTokens.NORMAL)
        self.anim_h.setStartValue(self.pill.height())
        self.anim_h.setEndValue(target_h)
        self.anim_h.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.anim_w.start()
        self.anim_h.start()

    # ── State Machine Callbacks ──

    def _on_state_changed(self, prev_state: IslandState, new_state: IslandState):
        if new_state == IslandState.IDLE:
            self.pill.set_idle()
            self.pill.set_corner_radius(IslandSize.IDLE_HEIGHT // 2)
            self.animate_to(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.RECORDING:
            self.pill.start_recording()
            self.pill.set_corner_radius(IslandSize.RECORDING_HEIGHT // 2)
            self.animate_to(IslandSize.RECORDING_WIDTH, IslandSize.RECORDING_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.PROCESSING:
            self.pill.start_processing()
            self.pill.set_corner_radius(IslandSize.PROCESSING_HEIGHT // 2)
            self.animate_to(IslandSize.PROCESSING_WIDTH, IslandSize.PROCESSING_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.SUCCESS:
            self.pill.stop_processing()
            self.pill.set_corner_radius(IslandSize.SUCCESS_HEIGHT // 2)
            self.animate_to(IslandSize.SUCCESS_WIDTH, IslandSize.SUCCESS_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.EXPANDED:
            self.pill.set_corner_radius(IslandSize.EXPANDED_RADIUS)
            self._set_focus_accepting(True)
            self.animate_to(IslandSize.EXPANDED_WIDTH, IslandSize.EXPANDED_HEIGHT)
            self._hide_basics_buttons()
        elif new_state == IslandState.BASICS:
            self.pill.set_basics()
            self.pill.set_corner_radius(IslandSize.IDLE_HEIGHT // 2)
            self.animate_to(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            self._show_basics_buttons()
            self._set_focus_accepting(False)

    def _set_focus_accepting(self, accept: bool):
        flags = self.windowFlags()
        has_focus_block = bool(flags & Qt.WindowType.WindowDoesNotAcceptFocus)
        
        if accept and has_focus_block:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowDoesNotAcceptFocus)
            self.show()
        elif not accept and not has_focus_block:
            self.setWindowFlags(flags | Qt.WindowType.WindowDoesNotAcceptFocus)
            self.show()

    # ── Quick Controls Handler ──

    def _show_basics_buttons(self):
        pill_geom = self.pill.geometry()
        right = pill_geom.right()
        center_y = pill_geom.top() + pill_geom.height() / 2
        
        # Bogen-Platzierung rechts neben der Pill
        self.btn_power.move(int(right + 12), int(center_y - 16))
        self.btn_restart.move(int(right + 36), int(center_y + 12))
        self.btn_sleep.move(int(right + 48), int(center_y + 46))
        
        self.btn_power.show()
        self.btn_restart.show()
        self.btn_sleep.show()

    def _hide_basics_buttons(self):
        self.btn_power.hide()
        self.btn_restart.hide()
        self.btn_sleep.hide()
        self._reset_confirm_state()

    def _handle_power_click(self):
        if self._confirm_state == "power":
            import os
            os.system("shutdown /s /t 0")
        else:
            self._confirm_state = "power"
            self.pill.basics_label.setText("Sicher? (Power)")
            self._confirm_timer.start(3000)

    def _handle_restart_click(self):
        if self._confirm_state == "restart":
            import os
            os.system("shutdown /r /t 0")
        else:
            self._confirm_state = "restart"
            self.pill.basics_label.setText("Sicher? (Restart)")
            self._confirm_timer.start(3000)

    def _handle_sleep_click(self):
        import os
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def _reset_confirm_state(self):
        self._confirm_state = None
        if self.state_machine.is_basics:
            self.pill.basics_label.setText("Basics")

    # ── Mouse Events ──

    def mousePressEvent(self, event):
        pill_rect = self.pill.geometry()
        if pill_rect.contains(event.position().toPoint()):
            if event.button() == Qt.MouseButton.RightButton:
                # Stilwahl nur über Direkt-Chips im EXPANDED-Modus
                if self.state_machine.is_idle or self.state_machine.is_success:
                    self.state_machine.transition_by_name("expanded")
                event.accept()
            elif event.button() == Qt.MouseButton.LeftButton:
                if self.state_machine.is_idle or self.state_machine.is_success:
                    self.state_machine.transition_by_name("expanded")
                # EXPANDED: nicht per Klick schließen – nur über ✕-Button
                event.accept()

    def mouseDoubleClickEvent(self, event):
        pill_rect = self.pill.geometry()
        if pill_rect.contains(event.position().toPoint()):
            if event.button() == Qt.MouseButton.LeftButton:
                self._on_open_settings()
                event.accept()

    def _on_style_selected(self, style_key: str):
        pass

    def _on_open_settings(self):
        dialog = SettingsWindow(self)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = int(screen.left() + (screen.width() - dialog.width()) / 2.0)
        y = int(screen.top() + (screen.height() - dialog.height()) / 2.0)
        dialog.move(x, y)
        dialog.show()

    def _on_quit_app(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile().lower()
                if path.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            path_lower = file_path.lower()
            if path_lower.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                if self.file_dropped_callback:
                    self.file_dropped_callback(file_path)
                break
        event.acceptProposedAction()
