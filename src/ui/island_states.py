"""
island_states.py
State-Machine für die Dynamic Island UI.
Verwaltet Übergänge: idle → recording → processing → success → idle
"""

from enum import Enum, auto
from typing import Callable, Optional
import threading
import time

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
    IslandState.RECORDING:  {IslandState.PROCESSING, IslandState.IDLE, IslandState.ERROR},
    IslandState.PROCESSING: {IslandState.SUCCESS, IslandState.ERROR, IslandState.IDLE, IslandState.EXPANDED},
    IslandState.SUCCESS:    {IslandState.IDLE, IslandState.RECORDING, IslandState.EXPANDED, IslandState.BASICS},
    IslandState.ERROR:      {IslandState.IDLE},
    IslandState.EXPANDED:   {IslandState.IDLE, IslandState.RECORDING},
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
        self._dismiss_timer: Optional[threading.Timer] = None

        # Listener: (prev_state, new_state) → None
        self._listeners: list[Callable[[IslandState, IslandState], None]] = []

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

        # Bestehenden Auto-Dismiss-Timer abbrechen
        self._cancel_timer()

        # Listener benachrichtigen
        for listener in self._listeners:
            try:
                listener(prev, new_state)
            except Exception as e:
                print(f"[State] Listener-Fehler: {e}")

        print(f"[State] {prev.name} → {new_state.name}")

        # Auto-Dismiss nach Timeout
        if auto_dismiss_ms is not None:
            target = IslandState.EXPANDED if new_state == IslandState.SUCCESS else IslandState.IDLE
            self._dismiss_timer = threading.Timer(
                auto_dismiss_ms / 1000.0,
                lambda: self.transition_to(target),
            )
            self._dismiss_timer.daemon = True
            self._dismiss_timer.start()

        return True

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
        self._cancel_timer()
        with self._lock:
            prev = self._current
            self._current = IslandState.IDLE
        for listener in self._listeners:
            try:
                listener(prev, IslandState.IDLE)
            except Exception:
                pass

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
        if self._dismiss_timer and self._dismiss_timer.is_alive():
            self._dismiss_timer.cancel()
            self._dismiss_timer = None

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
