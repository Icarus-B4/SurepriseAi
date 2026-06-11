"""
dynamic_island.py
Haupt-Overlay-Fenster (Dynamic Island) in PyQt6.
Verwaltet das rahmenlose transparente Trägerfenster.
"""

import time

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QTimer, QRect
from src.ui.design_tokens import IslandSize, Colors, AnimationTokens
from src.ui.island_pill import IslandPill
from src.ui.island_shimmer_indicator import IslandShimmerIndicator
from src.ui.island_states import IslandState
from src.ui.settings_panel import SettingsWindow
from src.ui.quick_control_button import QuickControlButton
from src.ui.outside_click_overlay import OutsideClickOverlay
from src.services.config_service import config


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
        self.url_dropped_callback = None
        self._user_moved = False  # True sobald der Nutzer das Fenster per Drag verschoben hat
        self._idle_revealed = True  # Sentinel: erster Aufruf erzwingt kollabierte Shimmer-Bar
        self._presence_hidden_for_settings = False
        self._zone_visit_start: float | None = None
        self._zone_visit_expired = False
        self._was_in_trigger_zone = False
        
        self._init_ui()
        self._setup_position()
        self._init_quick_controls()

        self._outside_overlay = OutsideClickOverlay()
        self._outside_overlay.clicked.connect(self._on_outside_overlay_clicked)
        self.outside_dismiss_callback = None

        # Hover-Timer und Opacity Animation Setup
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._check_hover)
        self.hover_timer.start(100) # 100ms Polling
        self.is_hovered = False
        
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(AnimationTokens.FAST)
        self.setWindowOpacity(1.0)
        
        # State-Machine Listener registrieren
        self.state_machine.add_listener(self._on_state_changed)
        if self.state_machine.is_idle or self.state_machine.is_basics:
            if config.get_bool("enable_presence_bar", True):
                self._check_hover()
            else:
                self._set_idle_revealed(False)

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

        if self._presence_hidden_for_settings:
            return

        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QApplication
        pos = QCursor.pos()
        screen_rect = QApplication.primaryScreen().geometry()
        center_x = screen_rect.width() / 2
        half_w = IslandSize.PRESENCE_TRIGGER_HALF_W

        is_in_zone = (
            center_x - half_w <= pos.x() <= center_x + half_w
            and pos.y() <= IslandSize.PRESENCE_TRIGGER_MAX_Y
        )
        if self.geometry().contains(pos):
            is_in_zone = True

        self.is_hovered = is_in_zone

        # v0.1.7-Verhalten: Presence-Bar dauerhaft, volle Pill bei Hover
        if not config.get_bool("enable_presence_bar", True):
            self._set_idle_revealed(is_in_zone)
            return

        # Cinema-Modus: nur in Trigger-Zone, max. 5 s pro Besuch
        now = time.monotonic()
        just_entered = is_in_zone and not self._was_in_trigger_zone
        self._was_in_trigger_zone = is_in_zone

        if not is_in_zone:
            self._zone_visit_start = None
            self._zone_visit_expired = False
            self._hide_idle_completely()
            return

        if just_entered:
            self._zone_visit_start = now
            self._zone_visit_expired = False

        if self._zone_visit_expired:
            self._hide_idle_completely()
            return

        elapsed = now - (self._zone_visit_start or now)
        if elapsed >= IslandSize.PRESENCE_IDLE_TIMEOUT_S:
            self._zone_visit_expired = True
            self._hide_idle_completely()
            return

        self._set_idle_revealed(is_in_zone)

    def _fade_to(self, target_opacity: float):
        if self.windowOpacity() == target_opacity:
            return
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(target_opacity)
        self.opacity_anim.start()

    def _position_presence_bar(self) -> None:
        x = (self.width() - self.presence_bar.width()) // 2
        self.presence_bar.move(x, IslandSize.PRESENCE_TOP_Y)

    def _hide_idle_completely(self) -> None:
        """Idle-UI ausblenden (Cinema-Modus außerhalb der Zone / nach Timeout)."""
        self.pill.hide()
        self.presence_bar.stop()
        self.presence_bar.hide()
        self._idle_revealed = False
        self.setWindowOpacity(0.0)

    def _set_idle_revealed(self, revealed: bool) -> None:
        """Wechselt zwischen Shimmer-Bar (kollabiert) und voller Idle-Pill."""
        if revealed == self._idle_revealed:
            return
        self._idle_revealed = revealed
        if revealed:
            self.presence_bar.stop()
            self.presence_bar.hide()
            self.pill.show()
            self._fade_to(1.0)
        else:
            self.pill.hide()
            self._position_presence_bar()
            self.presence_bar.start()
            self.setWindowOpacity(1.0)

    def _exit_presence_mode(self) -> None:
        """Blendet Shimmer-Bar aus, zeigt die Pill (aktive Zustände)."""
        self.presence_bar.stop()
        self.presence_bar.hide()
        self.pill.show()
        self._idle_revealed = True
        self.setWindowOpacity(1.0)

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        self.pill = IslandPill(self)
        self.pill.setFixedSize(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
        self.layout.addWidget(self.pill)

        self.presence_bar = IslandShimmerIndicator(self)
        self.presence_bar.hide()
        self._position_presence_bar()

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
        self._position_presence_bar()
        # Kein _setup_position() hier – show() würde sonst nach jedem Klick zurückspringen

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_presence_bar()

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
        self._outside_overlay.hide_overlay()

        if new_state == IslandState.IDLE:
            self.pill.set_idle()
            self.pill.set_corner_radius(IslandSize.IDLE_HEIGHT // 2)
            self.animate_to(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
            if config.get_bool("enable_presence_bar", True):
                self._zone_visit_start = None
                self._zone_visit_expired = False
                self._was_in_trigger_zone = False
                self._check_hover()
            else:
                self._set_idle_revealed(self.is_hovered)
        elif new_state == IslandState.RECORDING:
            self._exit_presence_mode()
            self.pill.start_recording()
            self.pill.set_corner_radius(IslandSize.RECORDING_HEIGHT // 2)
            self.animate_to(IslandSize.RECORDING_WIDTH, IslandSize.RECORDING_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.PROCESSING:
            self._exit_presence_mode()
            if prev_state == IslandState.RECORDING:
                self.pill.play_settle_pulse()
            self.pill.start_processing()
            self.pill.set_corner_radius(IslandSize.PROCESSING_HEIGHT // 2)
            self.animate_to(IslandSize.PROCESSING_WIDTH, IslandSize.PROCESSING_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.SUCCESS:
            self._exit_presence_mode()
            self.pill.stop_processing()
            self.pill.set_corner_radius(IslandSize.SUCCESS_HEIGHT // 2)
            self.animate_to(IslandSize.SUCCESS_WIDTH, IslandSize.SUCCESS_HEIGHT)
            self._hide_basics_buttons()
            self._set_focus_accepting(False)
        elif new_state == IslandState.EXPANDED:
            self._exit_presence_mode()
            self.pill.set_corner_radius(IslandSize.EXPANDED_RADIUS)
            self._set_focus_accepting(True)
            self.animate_to(IslandSize.EXPANDED_WIDTH, IslandSize.EXPANDED_HEIGHT)
            self._hide_basics_buttons()
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self._outside_overlay.show_below(self)
        elif new_state == IslandState.BASICS:
            self.pill.set_basics()
            self.pill.set_corner_radius(IslandSize.IDLE_HEIGHT // 2)
            self.animate_to(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            self._show_basics_buttons()
            self._set_focus_accepting(False)
            if config.get_bool("enable_presence_bar", True):
                self._zone_visit_start = None
                self._zone_visit_expired = False
                self._was_in_trigger_zone = False
                self._check_hover()
            else:
                self._set_idle_revealed(self.is_hovered)

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

    # ── Outside-Click Dismiss ──

    def is_dismissible_by_outside_click(self) -> bool:
        if self._presence_hidden_for_settings:
            return False
        sm = self.state_machine
        if sm.is_recording or sm.is_processing:
            return False
        if sm.is_expanded:
            return True
        if sm.is_idle or sm.is_basics or sm.is_success:
            return self.windowOpacity() > 0.01
        return False

    def visible_chrome_global_rect(self) -> QRect:
        """Sichtbare Island-Teile in Bildschirmkoordinaten."""
        if self.windowOpacity() < 0.01:
            return QRect()

        local_rects: list[QRect] = []
        if self.presence_bar.isVisible():
            local_rects.append(self.presence_bar.geometry())
        if self.pill.isVisible():
            local_rects.append(self.pill.geometry())
        for btn in (self.btn_power, self.btn_restart, self.btn_sleep):
            if btn.isVisible():
                local_rects.append(btn.geometry())

        if not local_rects:
            return QRect()

        united = local_rects[0]
        for rect in local_rects[1:]:
            united = united.united(rect)

        top_left = self.mapToGlobal(united.topLeft())
        return QRect(top_left, united.size())

    def prepare_after_expanded_dismiss(self) -> None:
        """Nach Schließen der Expanded-Ansicht: Zone-Timer zurücksetzen."""
        self._outside_overlay.hide_overlay()
        self._zone_visit_start = time.monotonic()
        self._zone_visit_expired = False
        self._was_in_trigger_zone = True

    def _local_point_hits_chrome(self, point: QPoint) -> bool:
        if self.presence_bar.isVisible() and self.presence_bar.geometry().contains(point):
            return True
        if self.pill.isVisible() and self.pill.geometry().contains(point):
            return True
        for btn in (self.btn_power, self.btn_restart, self.btn_sleep):
            if btn.isVisible() and btn.geometry().contains(point):
                return True
        return False

    def should_dismiss_for_global_click(self, global_x: int, global_y: int) -> bool:
        if not self.is_dismissible_by_outside_click():
            return False
        if not self.isVisible() or self.windowOpacity() < 0.01:
            return False
        if not self.geometry().contains(global_x, global_y):
            return True
        local = self.mapFromGlobal(QPoint(global_x, global_y))
        return not self._local_point_hits_chrome(local)

    def _on_outside_overlay_clicked(self) -> None:
        if not self.state_machine.is_expanded:
            return
        if self.outside_dismiss_callback:
            self.outside_dismiss_callback()

    def collapse_from_outside_click(self) -> None:
        """Blendet Idle/Basics/Success-UI aus."""
        self._was_in_trigger_zone = False
        self._zone_visit_start = None
        self._zone_visit_expired = True
        self._idle_revealed = False
        self._hide_idle_completely()

    # ── Mouse Events ──

    def mousePressEvent(self, event):
        point = event.position().toPoint()

        if self.state_machine.is_expanded and event.button() == Qt.MouseButton.LeftButton:
            if not self._local_point_hits_chrome(point):
                if self.outside_dismiss_callback:
                    self.outside_dismiss_callback()
                event.accept()
                return

        if self.presence_bar.isVisible() and self.presence_bar.geometry().contains(point):
            if event.button() == Qt.MouseButton.LeftButton:
                self._set_idle_revealed(True)
                if self.state_machine.is_idle or self.state_machine.is_success:
                    self.state_machine.transition_by_name("expanded")
            event.accept()
            return

        pill_rect = self.pill.geometry()
        if pill_rect.contains(point):
            if event.button() == Qt.MouseButton.RightButton:
                # Stilwahl nur über Direkt-Chips im EXPANDED-Modus
                if self.state_machine.is_idle or self.state_machine.is_success:
                    self.state_machine.transition_by_name("expanded")
                event.accept()
            elif event.button() == Qt.MouseButton.LeftButton:
                if self.state_machine.is_idle or self.state_machine.is_success:
                    self.state_machine.transition_by_name("expanded")
                # EXPANDED: Klick auf Pill-Inhalt schließt nicht (nur außerhalb / ✕)
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
        on_history = getattr(self, "open_history_callback", None)
        dialog = SettingsWindow(self, on_open_history=on_history)
        cb = getattr(self, "settings_changed_callback", None)
        if cb:
            dialog.setting_changed.connect(cb)
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
            from src.services.media_url_service import is_media_url
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile().lower()
                    if path.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                        event.acceptProposedAction()
                        return
                elif is_media_url(url.toString()):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        from src.services.media_url_service import is_media_url
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                path_lower = file_path.lower()
                if path_lower.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                    if self.file_dropped_callback:
                        self.file_dropped_callback(file_path)
                    break
            else:
                remote = url.toString()
                if is_media_url(remote) and self.url_dropped_callback:
                    self.url_dropped_callback(remote)
                    break
        event.acceptProposedAction()
