"""
waveform_widget.py
Custom QWidget für PyQt6, das eine animierte Audio-Wellenform zeichnet.
Visualisiert den RMS-Pegel aus dem Mikrofon flüssig und performant.
"""

import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor
from src.ui.design_tokens import IslandSize, Colors

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = [IslandSize.WAVEFORM_MIN_H] * IslandSize.WAVEFORM_BARS
        self.target_bars = [IslandSize.WAVEFORM_MIN_H] * IslandSize.WAVEFORM_BARS
        
        # Animations-Timer (ca. 40 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(25) # 25ms
        
        self.setMinimumSize(
            IslandSize.WAVEFORM_BARS * (IslandSize.WAVEFORM_BAR_W + IslandSize.WAVEFORM_BAR_GAP),
            IslandSize.WAVEFORM_MAX_H
        )

    def set_rms(self, rms: float):
        """Setzt den aktuellen RMS-Pegel (0.0 bis 1.0) und berechnet die Zielhöhen."""
        # Skaliere den Pegel auf die maximale Balkenhöhe
        base_h = IslandSize.WAVEFORM_MIN_H + rms * (IslandSize.WAVEFORM_MAX_H - IslandSize.WAVEFORM_MIN_H)
        
        # Erzeuge eine Welle durch Staffelung und leichtes Rauschen
        for i in range(IslandSize.WAVEFORM_BARS):
            # Balken in der Mitte reagieren stärker, die äußeren etwas schwächer
            factor = 1.0 - abs(i - 2) * 0.2
            noise = random.uniform(0.8, 1.2)
            target = base_h * factor * noise
            
            # Begrenzung auf Min/Max
            self.target_bars[i] = max(
                IslandSize.WAVEFORM_MIN_H,
                min(IslandSize.WAVEFORM_MAX_H, target)
            )

    def reset_waveform(self):
        """Setzt alle Balken auf die minimale Höhe zurück."""
        self.target_bars = [IslandSize.WAVEFORM_MIN_H] * IslandSize.WAVEFORM_BARS

    def _animate(self):
        """Interpoliert die aktuellen Balkenhöhen in Richtung der Zielhöhen."""
        changed = False
        for i in range(IslandSize.WAVEFORM_BARS):
            diff = self.target_bars[i] - self.bars[i]
            if abs(diff) > 0.1:
                # Dämpfung für weiche Bewegung
                self.bars[i] += diff * 0.3
                changed = True
            else:
                self.bars[i] = self.target_bars[i]
                
        if changed:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bar styling
        color = Colors.recording_red()
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Berechne Start-X, um die Balkengruppe horizontal zu zentrieren
        total_width = (IslandSize.WAVEFORM_BARS * IslandSize.WAVEFORM_BAR_W +
                       (IslandSize.WAVEFORM_BARS - 1) * IslandSize.WAVEFORM_BAR_GAP)
        start_x = (self.width() - total_width) / 2.0
        
        # Zeichne jeden Balken zentriert
        for i in range(IslandSize.WAVEFORM_BARS):
            bar_h = self.bars[i]
            x = start_x + i * (IslandSize.WAVEFORM_BAR_W + IslandSize.WAVEFORM_BAR_GAP)
            # Vertikal zentrieren
            y = (self.height() - bar_h) / 2.0
            
            rect = QRectF(x, y, IslandSize.WAVEFORM_BAR_W, bar_h)
            # Abgerundete Balken
            painter.drawRoundedRect(rect, IslandSize.WAVEFORM_BAR_W / 2.0, IslandSize.WAVEFORM_BAR_W / 2.0)
