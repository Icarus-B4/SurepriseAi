"""
waveform_widget.py
Flüssige HSL-Kurven-Waveform im Siri/Eloquent-Stil.
Zeichnet mehrere überlagernde Bezier-Kurven mit HSL-Farbverlauf,
die auf den RMS-Pegel des Mikrofons reagieren.
"""

import math
import random
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, QPointF
from PyQt6.QtGui import (
    QPainter, QPainterPath, QLinearGradient, QColor, QPen
)
from src.ui.design_tokens import IslandSize, Colors


# Konfiguration für die Wellenform
NUM_WAVES = 3           # Anzahl überlagernder Wellen
WAVE_POINTS = 32        # Stützpunkte pro Welle (mehr = glatter)
FRAME_MS = 16           # ~60 FPS
DAMPING = 0.12          # Interpolations-Stärke (sanfte Bewegung)
SPRING_DAMPING = 0.08   # Nachschwingungs-Dämpfung
IDLE_AMPLITUDE = 0.06   # Minimale Idle-Amplitude (dezente Atembewegung)

# HSL-Farbverlauf: Indigo → Violett → Magenta
WAVE_COLORS = [
    (QColor("#6366F1"), 0.78),   # Indigo
    (QColor("#8B5CF6"), 0.62),   # Violett
    (QColor("#EC4899"), 0.50),   # Pink/Magenta
]


class WaveformWidget(QWidget):
    """Flüssige, organisch fließende Wellenform mit HSL-Farbverlauf."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Aktuelle und Ziel-Amplituden pro Welle
        self._amplitudes = [IDLE_AMPLITUDE] * NUM_WAVES
        self._target_amplitudes = [IDLE_AMPLITUDE] * NUM_WAVES
        self._velocities = [0.0] * NUM_WAVES   # Für Nachschwingen

        # Phase-Offset pro Welle (unabhängige Bewegung)
        self._phases = [0.0] * NUM_WAVES
        self._phase_speeds = [
            0.035 + i * 0.012 for i in range(NUM_WAVES)
        ]

        self._rms = 0.0
        self._target_rms = 0.0

        # Animations-Timer (60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(FRAME_MS)
        print(
            f"[Waveform] Siri/Eloquent-Stil initialisiert "
            f"(timer={FRAME_MS}ms, 60fps, HSL gradient, {NUM_WAVES} curves, Antialiasing RenderHint)"
        )

        self.setMinimumSize(IslandSize.WAVEFORM_WIDTH, IslandSize.WAVEFORM_MAX_H)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_rms(self, rms: float):
        """Setzt den RMS-Pegel (0.0–1.0). API-kompatibel zum alten Widget."""
        self._target_rms = max(0.0, min(1.0, rms))
        # Ziel-Amplituden pro Welle (äußere Wellen etwas kleiner)
        for i in range(NUM_WAVES):
            scale = 1.0 - i * 0.18
            noise = random.uniform(0.85, 1.15)
            self._target_amplitudes[i] = max(
                IDLE_AMPLITUDE,
                self._target_rms * scale * noise
            )

    def reset_waveform(self):
        """Setzt alle Wellen auf die Idle-Amplitude zurück."""
        print("[Waveform] reset_waveform – Kurven auf Baseline")
        self._target_rms = 0.0
        for i in range(NUM_WAVES):
            self._target_amplitudes[i] = IDLE_AMPLITUDE
            self._velocities[i] = 0.0

    def _animate(self):
        """Interpoliert Amplituden mit Federphysik und bewegt die Phasen."""
        changed = False

        # RMS sanft interpolieren
        rms_diff = self._target_rms - self._rms
        if abs(rms_diff) > 0.001:
            self._rms += rms_diff * DAMPING * 2
            changed = True

        for i in range(NUM_WAVES):
            # Federphysik: Geschwindigkeit + Dämpfung
            diff = self._target_amplitudes[i] - self._amplitudes[i]
            self._velocities[i] += diff * DAMPING
            self._velocities[i] *= (1.0 - SPRING_DAMPING)
            self._amplitudes[i] += self._velocities[i]

            # Phase weiterdrehen (auch im Idle)
            speed = self._phase_speeds[i]
            # Bei aktiver Aufnahme schneller bewegen
            if self._rms > 0.05:
                speed *= 1.0 + self._rms * 2.0
            self._phases[i] += speed
            changed = True

        if changed:
            self.update()

    def paintEvent(self, event):
        """Zeichnet die überlagernden Bezier-Kurven mit Farbverlauf."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        center_y = h / 2.0

        # Zeichne Wellen von hinten nach vorne (größte Deckkraft zuletzt)
        for wave_idx in reversed(range(NUM_WAVES)):
            self._draw_wave(
                painter, wave_idx, w, h, center_y
            )

    def _draw_wave(
        self, painter: QPainter, idx: int,
        w: float, h: float, cy: float
    ):
        """Zeichnet eine einzelne Bezier-Welle mit Farbverlauf."""
        amplitude = self._amplitudes[idx] * h * 0.55
        phase = self._phases[idx]
        color, alpha = WAVE_COLORS[idx]

        # Erzeuge Stützpunkte für die Sinuskurve
        points: list[QPointF] = []
        for j in range(WAVE_POINTS + 1):
            t = j / WAVE_POINTS
            x = t * w

            # Mehrere Sinuswellen überlagern (natürliche Bewegung)
            freq1 = 2.0 + idx * 0.5
            freq2 = 3.5 + idx * 0.7
            y_offset = (
                math.sin(t * freq1 * math.pi + phase) * amplitude
                + math.sin(t * freq2 * math.pi + phase * 1.3) * amplitude * 0.35
            )

            # Fenster-Funktion: An den Rändern auf Null abklingen
            window = math.sin(t * math.pi) ** 1.5
            y = cy + y_offset * window
            points.append(QPointF(x, y))

        # Baue den QPainterPath als glatte Kurve
        path = QPainterPath()
        if not points:
            return
        path.moveTo(points[0])

        # Catmull-Rom zu Bezier-Konvertierung für glatte Kurven
        for j in range(1, len(points)):
            p0 = points[max(0, j - 1)]
            p1 = points[j]
            # Einfache quadratische Interpolation
            ctrl_x = (p0.x() + p1.x()) / 2.0
            path.quadTo(p0, QPointF(ctrl_x, (p0.y() + p1.y()) / 2.0))
        path.lineTo(points[-1])

        # Farbverlauf horizontal über die gesamte Breite
        gradient = QLinearGradient(0, 0, w, 0)
        c1 = QColor(color)
        c1.setAlphaF(alpha)
        c2 = QColor(WAVE_COLORS[(idx + 1) % len(WAVE_COLORS)][0])
        c2.setAlphaF(alpha * 0.8)
        gradient.setColorAt(0.0, c1)
        gradient.setColorAt(0.5, c2)
        gradient.setColorAt(1.0, c1)

        # Zeichne die Wellenform als Linie mit Verlauf
        pen = QPen()
        pen.setBrush(gradient)
        pen.setWidthF(3.5 - idx * 0.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
