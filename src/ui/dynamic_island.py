"""
dynamic_island.py
Haupt-Overlay-Fenster (Dynamic Island) in PyQt6.
Unterstützte Drag & Drop Formate: .mp3, .wav, .m4a, .mp4, .avi, .mov, .ogg, .flac
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, QRect, QPoint
from src.ui.design_tokens import IslandSize, AnimationTokens
from src.ui.island_pill import IslandPill
from src.ui.island_shimmer_indicator import IslandShimmerIndicator
from src.ui.island_states import IslandState
from src.ui.settings_panel import SettingsWindow
from src.ui.outside_click_overlay import OutsideClickOverlay
from src.services.config_service import config
from src.ui.presence_controller import PresenceController
from src.ui.dismissal_manager import DismissalManager
from src.ui.drag_drop_filter import DragDropFilter
from src.ui.input_filter import InputFilter
from src.ui.settings_manager import SettingsManager
from src.ui.state_controller import StateController
from src.ui.geometry_helper import GeometryHelper
from src.ui.win32_backdrop import remove_backdrop

class DynamicIslandWindow(QWidget):
    """Hauptfenster der Dynamic Island."""
    def __init__(self, state_machine, parent=None):
        super().__init__(parent)
        self.state_machine = state_machine
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        self.setAcceptDrops(True)
        self.file_dropped_callback = None
        self.url_dropped_callback = None
        self._user_moved = False
        self._idle_revealed = True
        self._presence_hidden_for_settings = False
        self._expanded_height = IslandSize.EXPANDED_HEIGHT
        self._backdrop_applied = False  # Verhindert mehrfaches Anwenden
        self._init_ui()
        self._outside_overlay = OutsideClickOverlay()
        self._outside_overlay.global_click.connect(self._on_outside_overlay_clicked)
        self.outside_dismiss_callback = None
        self.pill.expanded_widget.resize_requested.connect(self._on_expanded_resize)
        self.presence_controller = PresenceController(self)
        self.dismissal_manager = DismissalManager(self)
        self.drag_drop_filter = DragDropFilter(self)
        self.input_filter = InputFilter(self)
        self.settings_manager = SettingsManager(self)
        self.state_controller = StateController(self)
        self.geometry_helper = GeometryHelper(self)
        self.sync_carrier_to_pill(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
        self._setup_position()
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(AnimationTokens.FAST)
        self.setWindowOpacity(1.0)
        self.is_hovered = False
        self.state_machine.add_listener(self._on_state_changed)
        if self.state_machine.is_idle or self.state_machine.is_basics:
            if config.get_bool("enable_presence_bar", True):
                self._set_idle_revealed(False)
            else:
                self.presence_controller.check_hover()
                print("[Backdrop] opaque CSS fallback aktiv (Presence-Bar deaktiviert)")

    @property
    def _settings_dialog(self) -> SettingsWindow | None:
        return self.settings_manager.get_dialog()

    @_settings_dialog.setter
    def _settings_dialog(self, value):
        self.settings_manager._settings_dialog = value

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
        self.pill.basics_widget.mute_toggled.connect(self._on_mute_toggled)
        self.pill.basics_widget.device_cycle_requested.connect(self._on_device_cycle)
        self.pill.basics_widget.history_requested.connect(self._on_hub_history)
        self.pill.basics_widget.transcript_requested.connect(self._on_hub_transcript)
        self.pill.basics_widget.rewrite_requested.connect(self._on_hub_rewrite)
        self.mute_toggle_callback = None
        self.device_cycle_callback = None
        self.hub_history_callback = None
        self.hub_transcript_callback = None
        self.hub_rewrite_callback = None

    def _on_hub_history(self):
        if self.hub_history_callback:
            self.hub_history_callback()

    def _on_hub_transcript(self):
        if self.hub_transcript_callback:
            self.hub_transcript_callback()

    def _on_hub_rewrite(self):
        if self.hub_rewrite_callback:
            self.hub_rewrite_callback()

    def _on_mute_toggled(self):
        """Leitet Mute-Toggle an den registrierten Callback weiter."""
        if self.mute_toggle_callback:
            self.mute_toggle_callback()

    def _on_device_cycle(self):
        """Leitet Geräte-Wechsel an den registrierten Callback weiter."""
        if self.device_cycle_callback:
            self.device_cycle_callback()

    def _position_presence_bar(self):
        self.presence_bar.move((self.width() - self.presence_bar.width()) // 2, IslandSize.PRESENCE_TOP_Y)

    def sync_carrier_to_pill(self, pill_w: int | None = None, pill_h: int | None = None) -> None:
        """Passt nur die Trägergröße an – Position bleibt stabil (kein Sprung beim Klick)."""
        margin_x, margin_y = 24, 16
        w = pill_w if pill_w is not None else self.pill.width()
        h = pill_h if pill_h is not None else self.pill.height()
        if self.presence_bar.isVisible() and not self.pill.isVisible():
            carrier_w = max(IslandSize.PRESENCE_WIDTH + margin_x, w + margin_x)
            carrier_h = IslandSize.PRESENCE_TOP_Y + IslandSize.PRESENCE_HEIGHT + margin_y
        else:
            carrier_w = w + margin_x
            carrier_h = h + margin_y
            if self.state_machine.is_expanded:
                carrier_h += 12
        if carrier_w == self.width() and carrier_h == self.height():
            return
        old = self.geometry()
        center_x = old.x() + old.width() // 2
        top_y = old.y()
        self.setFixedSize(carrier_w, carrier_h)
        self._position_presence_bar()
        if self._user_moved:
            self.move(old.x(), old.y())
        else:
            self.move(center_x - carrier_w // 2, top_y)

    def _hide_idle_completely(self):
        self.pill.hide()
        self.presence_bar.stop()
        self.presence_bar.hide()
        self.setWindowOpacity(0.0)

    def _restore_idle_chrome(self) -> None:
        """Stellt Presence-Bar oder Idle-Pill nach Auto-Hide wieder her."""
        if self._idle_revealed:
            self.presence_bar.stop()
            self.presence_bar.hide()
            self.pill.show()
        else:
            self.pill.hide()
            self._position_presence_bar()
            self.presence_bar.start()
        self.sync_carrier_to_pill()
        self._fade_to(1.0)

    def _set_idle_revealed(self, revealed: bool):
        if revealed == self._idle_revealed: return
        self._idle_revealed = revealed
        if revealed:
            self.presence_bar.stop(); self.presence_bar.hide(); self.pill.show(); self._fade_to(1.0)
            self.sync_carrier_to_pill()
        else:
            self.pill.hide(); self._position_presence_bar(); self.presence_bar.start(); self.setWindowOpacity(1.0)
            self.sync_carrier_to_pill()

    def _exit_presence_mode(self):
        self.presence_bar.stop(); self.presence_bar.hide(); self.pill.show(); self._idle_revealed = True; self.setWindowOpacity(1.0)

    def _fade_to(self, target_opacity: float):
        if self.windowOpacity() == target_opacity: return
        self.opacity_anim.stop(); self.opacity_anim.setStartValue(self.windowOpacity()); self.opacity_anim.setEndValue(target_opacity); self.opacity_anim.start()

    def mark_user_positioned(self):
        self._user_moved = True

    def reset_to_start_position(self):
        self._user_moved = False; self._setup_position(force=True)

    def _setup_position(self, force: bool = False):
        self.geometry_helper.setup_position(force)

    def showEvent(self, event):
        super().showEvent(event)
        self._position_presence_bar()
        # Kein DWM-Acryl auf dem Vollflächen-Overlay (652×648) – sonst graues Rechteck.
        # Die Pill nutzt CSS-Glassmorphism; win32_backdrop bleibt für Settings verfügbar.
        if not self._backdrop_applied:
            remove_backdrop(self)
            self._backdrop_applied = True
            print("[Backdrop] transparentes Overlay – Pill-CSS aktiv (kein Vollflächen-Acryl)")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_presence_bar()

    @pyqtProperty(int)
    def pill_width(self) -> int: return self.pill.width()

    @pill_width.setter
    def pill_width(self, w: int): self.pill.setFixedWidth(w)
        
    @pyqtProperty(int)
    def pill_height(self) -> int: return self.pill.height()

    @pill_height.setter
    def pill_height(self, h: int): self.pill.setFixedHeight(max(1, h))

    def animate_to(self, target_w: int, target_h: int):
        self.geometry_helper.animate_to(target_w, target_h)

    def _on_state_changed(self, prev_state: IslandState, new_state: IslandState):
        self.state_controller.on_state_changed(prev_state, new_state)

    def _set_focus_accepting(self, accept: bool):
        self.state_controller.set_focus_accepting(accept)

    def is_dismissible_by_outside_click(self) -> bool: return self.dismissal_manager.is_dismissible_by_outside_click()
    def visible_chrome_global_rect(self) -> QRect: return self.dismissal_manager.visible_chrome_global_rect()
    def prepare_after_expanded_dismiss(self) -> None: self._outside_overlay.hide_overlay(); self.presence_controller.force_active_visit()
    def _local_point_hits_chrome(self, point) -> bool: return self.dismissal_manager._local_point_hits_chrome(point)
    def should_dismiss_for_global_click(self, global_x: int, global_y: int) -> bool: return self.dismissal_manager.should_dismiss_for_global_click(global_x, global_y)

    def _on_outside_overlay_clicked(self, x: int, y: int):
        if self.state_machine.is_expanded and not self.geometry().contains(QPoint(x, y)) and self.outside_dismiss_callback:
            self.outside_dismiss_callback()

    def _on_expanded_resize(self, delta_y: int):
        new_h = max(IslandSize.EXPANDED_MIN_HEIGHT, min(self._expanded_height + delta_y, IslandSize.EXPANDED_MAX_HEIGHT))
        if new_h != self._expanded_height:
            self._expanded_height = new_h
            self.pill.setFixedHeight(new_h)
            self.sync_carrier_to_pill(self.pill.width(), new_h)

    def collapse_from_outside_click(self):
        self.dismissal_manager.collapse_from_outside_click()

    def dragEnterEvent(self, event): self.drag_drop_filter.eventFilter(self, event)
    def dropEvent(self, event): self.drag_drop_filter.eventFilter(self, event)
    def wheelEvent(self, event): self.input_filter._handle_wheel(event)
    def mousePressEvent(self, event): self.input_filter._handle_mouse_press(event)
    def mouseDoubleClickEvent(self, event): self.input_filter._handle_mouse_double_click(event)

    def _toggle_settings(self): self.settings_manager.toggle_settings()
    def _on_settings_closed(self): self._presence_hidden_for_settings = False; self.presence_controller.check_hover()
    def _check_hover(self):
        """Kompatibilität für ältere Aufrufer (z. B. Settings-Panel)."""
        self.presence_controller.check_hover()
    def _on_open_settings(self): self._toggle_settings()
    def _on_quit_app(self): QApplication.quit()
