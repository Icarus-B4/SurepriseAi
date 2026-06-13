"""
playback_waveform.py
Wellenform-Visualisierung für gespeicherte Diktat-Audios.
Zeigt eine kompakte, moderne Waveform mit Playhead an.
"""

from __future__ import annotations

from pathlib import Path
import wave

import numpy as np
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QWidget

from src.ui.design_tokens import Colors


class PlaybackWaveform(QWidget):
    """Zeichnet die Audio-Wellenform eines gespeicherten WAV-Diktats."""

    seek_requested = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._bars: list[float] = []
        self._position_ratio = 0.0
        self._duration_ms = 0
        self._audio_path = ""
        self.setMinimumHeight(58)
        self.setMaximumHeight(76)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def clear(self) -> None:
        self._bars = []
        self._position_ratio = 0.0
        self._duration_ms = 0
        self._audio_path = ""
        self.update()

    def load_audio_file(self, file_path: str | None) -> None:
        """Lädt WAV-Daten und reduziert sie auf visuelle Balken."""
        self._audio_path = file_path or ""
        self._position_ratio = 0.0
        self._duration_ms = 0
        self._bars = []

        if not file_path:
            self.update()
            return

        path = Path(file_path)
        if not path.exists():
            self.update()
            return

        try:
            with wave.open(str(path), "rb") as wf:
                sample_rate = wf.getframerate() or 16000
                frames = wf.getnframes()
                duration_s = frames / float(sample_rate) if sample_rate else 0.0
                self._duration_ms = int(duration_s * 1000)
                raw = wf.readframes(frames)
                sample_width = wf.getsampwidth()
                channels = wf.getnchannels() or 1
        except Exception:
            self.update()
            return

        if not raw:
            self.update()
            return

        if sample_width == 2:
            audio = np.frombuffer(raw, dtype="<i2").astype(np.float32)
            audio /= 32768.0
        elif sample_width == 1:
            audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            audio = (audio - 128.0) / 128.0
        else:
            self.update()
            return

        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        if audio.size == 0:
            self.update()
            return

        self._bars = self._downsample(audio, 96)
        self.update()

    def set_position_ms(self, position_ms: int) -> None:
        if self._duration_ms > 0:
            self._position_ratio = max(0.0, min(1.0, position_ms / float(self._duration_ms)))
            self.update()

    def set_position_ratio(self, ratio: float) -> None:
        self._position_ratio = max(0.0, min(1.0, ratio))
        self.update()

    def _downsample(self, audio: np.ndarray, bins: int) -> list[float]:
        audio = np.abs(np.asarray(audio, dtype=np.float32))
        if audio.size == 0:
            return []
        bins = max(24, bins)
        edges = np.linspace(0, audio.size, bins + 1, dtype=int)
        bars: list[float] = []
        for start, end in zip(edges[:-1], edges[1:]):
            chunk = audio[start:end]
            if chunk.size == 0:
                bars.append(0.0)
            else:
                bars.append(float(np.max(chunk)))
        peak = max(bars) if bars else 1.0
        if peak <= 0:
            return [0.0 for _ in bars]
        return [min(1.0, value / peak) for value in bars]

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(17, 17, 20)))
        painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
        painter.drawRoundedRect(rect, 18, 18)

        inner = rect.adjusted(12, 12, -12, -12)
        inner_h = inner.height()
        center_y = inner.center().y()

        if not self._bars:
            painter.setPen(QPen(QColor(255, 255, 255, 34), 1))
            painter.drawLine(inner.left(), center_y, inner.right(), center_y)
            painter.setPen(QPen(QColor(142, 142, 147), 1))
            painter.drawText(inner, Qt.AlignmentFlag.AlignCenter, "Keine Waveform verfügbar")
            return

        count = len(self._bars)
        gap = 3
        bar_w = max(3, int((inner.width() - (count - 1) * gap) / count))
        total_w = count * bar_w + (count - 1) * gap
        start_x = inner.left() + max(0, (inner.width() - total_w) // 2)
        play_idx = int(round(self._position_ratio * max(0, count - 1)))

        painter.setPen(QPen(QColor(255, 255, 255, 26), 1))
        painter.drawLine(inner.left(), center_y, inner.right(), center_y)

        for index, amp in enumerate(self._bars):
            bar_h = max(4, int(amp * (inner_h - 10)))
            x = start_x + index * (bar_w + gap)
            y = center_y - bar_h / 2
            color = QColor(99, 102, 241, 230) if index <= play_idx else QColor(255, 255, 255, 92)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), bar_w / 2.0, bar_w / 2.0)

        play_x = start_x + play_idx * (bar_w + gap) + bar_w / 2.0
        painter.setPen(QPen(QColor(129, 140, 248), 2))
        painter.drawLine(int(play_x), inner.top(), int(play_x), inner.bottom())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._duration_ms > 0:
            ratio = 0.0
            if self.width() > 0:
                ratio = (event.position().x() - 12) / max(1.0, self.width() - 24)
            self.set_position_ratio(ratio)
            self.seek_requested.emit(int(self._duration_ms * self._position_ratio))
            event.accept()
        else:
            super().mousePressEvent(event)
