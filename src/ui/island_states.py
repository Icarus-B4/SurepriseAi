"""
island_states.py
State-Machine für die Dynamic Island UI.
Verwaltet Übergänge: idle → recording → processing → success → idle
"""

from enum import Enum, auto
from typing import Callable, Optional
import threading

from .design_tokens import AnimationTokens


class IslandState(Enum):
    """Alle möglichen Zustände der Dynamic Island."""
    IDLE       = auto()   # Ruhezustand: Pille mit Uhrzeit
    RECORDING  = auto()   # Aufnahme aktiv: Wellenform
    PROCESSING = auto()   # KI verarbeitet: Spinner
    SUCCESS    = auto()   # Ergebnis bereit: Text-Preview
    ERROR      = auto()   # Fehler: Kurze Fehlermeldung
    EXPANDED   = auto()   # Großes Transkript-Fenster
    BASICS     = auto()   # System-Steuerung (Ausschalten, Neustart, Sleep)


# Erlaubte Übergänge zwischen States
_TRANSITIONS: dict[IslandState, set[IslandState]] = {
    IslandState.IDLE:       {IslandState.RECORDING, IslandState.ERROR, IslandState.EXPANDED, IslandState.BASICS},
    IslandState.RECORDING:  {IslandState.PROCESSING, IslandState.IDLE, IslandState.ERROR, IslandState.EXPANDED},
    IslandState.PROCESSING: {IslandState.SUCCESS, IslandState.ERROR, IslandState.IDLE, IslandState.EXPANDED},
    IslandState.SUCCESS:    {IslandState.IDLE, IslandState.RECORDING, IslandState.EXPANDED, IslandState.BASICS},
    IslandState.ERROR:      {IslandState.IDLE},
    IslandState.EXPANDED:   {IslandState.IDLE, IslandState.RECORDING, IslandState.PROCESSING},
    IslandState.BASICS:     {IslandState.IDLE, IslandState.RECORDING},
}


class IslandStateMachine:
    """
    Verwaltet den aktuellen State der Dynamic Island.
    Stellt Transitions und Auto-Dismiss (für SUCCESS/ERROR) bereit.
    """

    def __init__(self) -> None:
        self._current: IslandState = IslandState.IDLE
        self._previous: Optional[IslandState] = None
        self._lock = threading.Lock()
        self._dismiss_generation = 0

        # Listener: (prev_state, new_state) → None
        self._listeners: list[Callable[[IslandState, IslandState], None]] = []

        # UI-Thread-Marshalling (von AppController mit QTimer gesetzt)
        self._is_main_thread: Optional[Callable[[], bool]] = None
        self._invoke_main: Optional[Callable[[Callable[[], None]], None]] = None
        self._schedule_delayed: Optional[Callable[[int, Callable[[], None]], None]] = None

    def configure_ui_thread(
        self,
        is_main_thread: Callable[[], bool],
        invoke_main: Callable[[Callable[[], None]], None],
        schedule_delayed: Callable[[int, Callable[[], None]], None],
    ) -> None:
        """Alle Listener und Timer laufen auf dem Qt-Hauptthread."""
        self._is_main_thread = is_main_thread
        self._invoke_main = invoke_main
        self._schedule_delayed = schedule_delayed

    def _run_on_ui_thread(self, fn: Callable[[], None]) -> None:
        if self._is_main_thread and self._invoke_main and not self._is_main_thread():
            self._invoke_main(fn)
        else:
            fn()

    # ── State-Verwaltung ──────────────────────────────────────────────────────

    def transition_to(
        self,
        new_state: IslandState,
        auto_dismiss_ms: Optional[int] = None,
    ) -> bool:
        """
        Wechselt in den neuen State, falls der Übergang erlaubt ist.

        Args:
            new_state: Ziel-State
            auto_dismiss_ms: Wenn angegeben, automatisch nach X ms zu IDLE

        Returns:
            True wenn der Übergang erfolgreich war
        """
        with self._lock:
            if new_state not in _TRANSITIONS.get(self._current, set()):
                # State direkt setzen wenn von IDLE oder ERROR aus
                if self._current not in (IslandState.IDLE, IslandState.ERROR):
                    print(
                        f"[State] Übergang {self._current.name} → "
                        f"{new_state.name} nicht erlaubt"
                    )
                    return False

            prev = self._current
            self._previous = prev
            self._current = new_state

        dismiss_ms = auto_dismiss_ms

        def complete() -> None:
            self._cancel_timer()
            for listener in self._listeners:
                try:
                    listener(prev, new_state)
                except Exception as e:
                    print(f"[State] Listener-Fehler: {e}")

            print(f"[State] {prev.name} → {new_state.name}")

            if dismiss_ms is not None:
                target = IslandState.IDLE
                self._schedule_dismiss(dismiss_ms, target)

        self._run_on_ui_thread(complete)
        return True

    def _schedule_dismiss(self, delay_ms: int, target: IslandState) -> None:
        self._dismiss_generation += 1
        generation = self._dismiss_generation

        def fire() -> None:
            if generation != self._dismiss_generation:
                return
            self.transition_to(target)

        if self._schedule_delayed:
            self._schedule_delayed(delay_ms, fire)
        else:
            threading.Timer(delay_ms / 1000.0, fire).start()

    def transition_by_name(self, state_name: str) -> bool:
        """Wechselt anhand des State-Namens (z.B. 'recording')."""
        mapping = {
            "idle":       IslandState.IDLE,
            "recording":  IslandState.RECORDING,
            "processing": IslandState.PROCESSING,
            "success":    IslandState.SUCCESS,
            "error":      IslandState.ERROR,
            "expanded":   IslandState.EXPANDED,
            "basics":     IslandState.BASICS,
        }
        state = mapping.get(state_name.lower())
        if state is None:
            print(f"[State] Unbekannter State: {state_name}")
            return False

        # Automatischen Dismiss für SUCCESS und ERROR
        auto_ms = None
        if state == IslandState.SUCCESS:
            auto_ms = AnimationTokens.SUCCESS_DISPLAY_MS
        elif state == IslandState.ERROR:
            auto_ms = 3000

        return self.transition_to(state, auto_dismiss_ms=auto_ms)

    def reset_to_idle(self) -> None:
        """Erzwingt einen Wechsel zu IDLE (ignoriert Übergangsregeln)."""
        with self._lock:
            prev = self._current
            self._current = IslandState.IDLE

        def complete() -> None:
            self._cancel_timer()
            for listener in self._listeners:
                try:
                    listener(prev, IslandState.IDLE)
                except Exception:
                    pass

        self._run_on_ui_thread(complete)

    # ── Listener ─────────────────────────────────────────────────────────────

    def add_listener(
        self, listener: Callable[[IslandState, IslandState], None]
    ) -> None:
        """Registriert einen State-Change-Listener."""
        self._listeners.append(listener)

    def remove_listener(
        self, listener: Callable[[IslandState, IslandState], None]
    ) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def _cancel_timer(self) -> None:
        self._dismiss_generation += 1

    @property
    def current(self) -> IslandState:
        return self._current

    @property
    def previous(self) -> Optional[IslandState]:
        return self._previous

    @property
    def is_idle(self) -> bool:
        return self._current == IslandState.IDLE

    @property
    def is_recording(self) -> bool:
        return self._current == IslandState.RECORDING

    @property
    def is_processing(self) -> bool:
        return self._current == IslandState.PROCESSING

    @property
    def is_success(self) -> bool:
        return self._current == IslandState.SUCCESS

    @property
    def is_expanded(self) -> bool:
        return self._current == IslandState.EXPANDED

    @property
    def is_basics(self) -> bool:
        return self._current == IslandState.BASICS
