"""
text_compare_slider.py
Superwhisper-artiger Slider zum Vergleich von Roh-Text und poliertem Text.
Zeigt eine visuelle Diff-Ansicht mit Hervorhebungen für Änderungen.
"""

import difflib
import html
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QTextEdit, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor

from src.ui.design_tokens import Colors, Typography


class TextCompareSlider(QWidget):
    """
    Widget mit Slider zum Vergleich von Raw-Text und Polished-Text.
    Slider links = Raw, Slider rechts = Polished, Mitte = Diff-Ansicht.
    """

    position_changed = pyqtSignal(float)  # 0.0 = raw, 1.0 = polished

    # Farben für Diff-Hervorhebung
    COLOR_DELETED = "#FFEB3B"  # Gelb für gelöschte Wörter (wie Superwhisper)
    COLOR_DELETED_BG = "rgba(255, 235, 59, 0.25)"
    COLOR_INSERTED = "#64B5F6"  # Blau für eingefügte Wörter
    COLOR_INSERTED_BG = "rgba(100, 181, 246, 0.2)"
    COLOR_EQUAL = Colors.TEXT_PRIMARY_HEX

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._raw_text = ""
        self._polished_text = ""
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header mit Labels "RAW INPUT" und "POLISHED"
        header = QHBoxLayout()
        header.setContentsMargins(8, 0, 8, 0)

        self.raw_label = QLabel("ROHTEXT", self)
        self.raw_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.raw_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")

        self.polished_label = QLabel("BEREINIGT", self)
        self.polished_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.polished_label.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX};")

        header.addWidget(self.raw_label)
        header.addStretch()
        header.addWidget(self.polished_label)
        layout.addLayout(header)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)  # Standard: Polished anzeigen
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.setStyleSheet(self._slider_style())
        layout.addWidget(self.slider)

        # Text-Anzeige
        self.text_view = QTextEdit(self)
        self.text_view.setReadOnly(True)
        self.text_view.setFont(Typography.get_font(Typography.SMALL))
        self.text_view.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {Colors.TEXT_PRIMARY_HEX};
                border: none;
                border-top: 1px solid {Colors.BORDER_SUBTLE_HEX};
                padding: 16px 10px 10px 10px;
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
                line-height: 1.6;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.CONTROL_HOVER_HEX};
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.BORDER_HIGHLIGHT};
            }}
        """)
        layout.addWidget(self.text_view, stretch=1)

    def _slider_style(self) -> str:
        return f"""
            QSlider::groove:horizontal {{
                height: 5px;
                border-radius: 2px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.BORDER_HIGHLIGHT},
                    stop:0.5 {Colors.CONTROL_HOVER_HEX},
                    stop:1 {Colors.ACCENT_BRIGHT_HEX}
                );
            }}
            QSlider::handle:horizontal {{
                background: {Colors.TEXT_PRIMARY_HEX};
                width: 17px;
                height: 17px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid {Colors.ACCENT_HEX};
            }}
            QSlider::handle:horizontal:hover {{
                background: white;
                border-color: {Colors.ACCENT_BRIGHT_HEX};
            }}
        """

    def set_texts(self, raw: str, polished: str) -> None:
        """Setzt beide Texte und aktualisiert die Anzeige."""
        self._raw_text = (raw or "").strip()
        self._polished_text = (polished or "").strip()
        self._update_display()

    def set_raw_text(self, text: str) -> None:
        """Setzt nur den Rohtext."""
        self._raw_text = (text or "").strip()
        self._update_display()

    def set_polished_text(self, text: str) -> None:
        """Setzt nur den polierten Text."""
        self._polished_text = (text or "").strip()
        self._update_display()

    def get_polished_text(self) -> str:
        """Gibt den polierten Text zurück."""
        return self._polished_text

    def get_raw_text(self) -> str:
        """Gibt den Rohtext zurück."""
        return self._raw_text

    def _on_slider_changed(self, value: int) -> None:
        ratio = value / 100.0
        self.position_changed.emit(ratio)
        self._update_display()

        # Label-Hervorhebung basierend auf Slider-Position
        if value < 33:
            self.raw_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY_HEX}; font-weight: bold;")
            self.polished_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        elif value > 66:
            self.raw_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
            self.polished_label.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX}; font-weight: bold;")
        else:
            self.raw_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
            self.polished_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")

    def _update_display(self) -> None:
        """Aktualisiert die Textanzeige basierend auf Slider-Position."""
        value = self.slider.value()

        if not self._raw_text and not self._polished_text:
            self.text_view.setPlainText("")
            return

        if value <= 10:
            # Nur Rohtext
            self.text_view.setPlainText(self._raw_text)
        elif value >= 90:
            # Nur polierter Text
            self.text_view.setPlainText(self._polished_text)
        else:
            # Diff-Ansicht
            self.text_view.setHtml(self._build_diff_html())

    def _build_diff_html(self) -> str:
        """Baut HTML mit visuellen Diff-Markierungen."""
        if not self._raw_text or not self._polished_text:
            return html.escape(self._polished_text or self._raw_text)

        if self._raw_text == self._polished_text:
            return html.escape(self._polished_text)

        raw_words = self._raw_text.split()
        pol_words = self._polished_text.split()

        matcher = difflib.SequenceMatcher(None, raw_words, pol_words)
        parts: list[str] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                text = html.escape(" ".join(raw_words[i1:i2]))
                parts.append(f'<span style="color:{self.COLOR_EQUAL};">{text}</span>')

            elif tag == "delete":
                # Gelöschte Wörter: gelb + durchgestrichen
                text = html.escape(" ".join(raw_words[i1:i2]))
                parts.append(
                    f'<span style="color:{self.COLOR_DELETED};'
                    f'background-color:{self.COLOR_DELETED_BG};'
                    f'text-decoration:line-through;'
                    f'border-radius:4px;padding:1px 4px;">{text}</span>'
                )

            elif tag == "insert":
                # Eingefügte Wörter: blau mit Hintergrund
                text = html.escape(" ".join(pol_words[j1:j2]))
                parts.append(
                    f'<span style="color:{self.COLOR_INSERTED};'
                    f'background-color:{self.COLOR_INSERTED_BG};'
                    f'border-radius:4px;padding:1px 4px;">{text}</span>'
                )

            elif tag == "replace":
                # Ersetzte Wörter: erst gelöscht, dann eingefügt
                del_text = html.escape(" ".join(raw_words[i1:i2]))
                ins_text = html.escape(" ".join(pol_words[j1:j2]))
                parts.append(
                    f'<span style="color:{self.COLOR_DELETED};'
                    f'background-color:{self.COLOR_DELETED_BG};'
                    f'text-decoration:line-through;'
                    f'border-radius:4px;padding:1px 4px;">{del_text}</span>'
                )
                parts.append(
                    f'<span style="color:{self.COLOR_INSERTED};'
                    f'background-color:{self.COLOR_INSERTED_BG};'
                    f'border-radius:4px;padding:1px 4px;">{ins_text}</span>'
                )

        body = " ".join(parts)
        return (
            f'<p style="margin:0;line-height:1.9;font-family:Segoe UI,sans-serif;'
            f'font-size:13px;">{body}</p>'
        )

    def show_diff_view(self) -> None:
        """Springt zur Diff-Ansicht (Slider in der Mitte)."""
        self.slider.setValue(50)

    def show_raw_view(self) -> None:
        """Springt zur Rohtext-Ansicht."""
        self.slider.setValue(0)

    def show_polished_view(self) -> None:
        """Springt zur Polished-Ansicht."""
        self.slider.setValue(100)


class CompactDiffView(QWidget):
    """
    Kompakte Diff-Ansicht ohne Slider für die History.
    Zeigt beide Texte untereinander mit Diff-Hervorhebung.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._raw_text = ""
        self._polished_text = ""
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Diff-Ansicht
        diff_label = QLabel("Änderungen", self)
        diff_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        diff_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        layout.addWidget(diff_label)

        self.diff_view = QTextEdit(self)
        self.diff_view.setReadOnly(True)
        self.diff_view.setMaximumHeight(120)
        self.diff_view.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.SURFACE_ELEVATED};
                color: {Colors.TEXT_PRIMARY_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 6px;
                padding: 8px;
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.diff_view)

    def set_texts(self, raw: str, polished: str) -> None:
        """Setzt beide Texte und zeigt Diff an."""
        self._raw_text = (raw or "").strip()
        self._polished_text = (polished or "").strip()
        self._update_diff()

    def _update_diff(self) -> None:
        """Aktualisiert die Diff-Anzeige."""
        if not self._raw_text or not self._polished_text:
            self.diff_view.setPlainText(self._polished_text or self._raw_text)
            return

        if self._raw_text == self._polished_text:
            self.diff_view.setPlainText("Keine Änderungen")
            return

        # Diff generieren
        raw_words = self._raw_text.split()
        pol_words = self._polished_text.split()
        matcher = difflib.SequenceMatcher(None, raw_words, pol_words)
        parts: list[str] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                text = html.escape(" ".join(raw_words[i1:i2]))
                parts.append(f'<span style="color:{Colors.TEXT_PRIMARY_HEX};">{text}</span>')
            elif tag == "delete":
                text = html.escape(" ".join(raw_words[i1:i2]))
                parts.append(
                    f'<span style="color:#FFEB3B;background:rgba(255,235,59,0.25);'
                    f'text-decoration:line-through;border-radius:3px;padding:0 2px;">{text}</span>'
                )
            elif tag == "insert":
                text = html.escape(" ".join(pol_words[j1:j2]))
                parts.append(
                    f'<span style="color:#64B5F6;background:rgba(100,181,246,0.2);'
                    f'border-radius:3px;padding:0 2px;">{text}</span>'
                )
            elif tag == "replace":
                del_text = html.escape(" ".join(raw_words[i1:i2]))
                ins_text = html.escape(" ".join(pol_words[j1:j2]))
                parts.append(
                    f'<span style="color:#FFEB3B;background:rgba(255,235,59,0.25);'
                    f'text-decoration:line-through;border-radius:3px;padding:0 2px;">{del_text}</span>'
                )
                parts.append(
                    f'<span style="color:#64B5F6;background:rgba(100,181,246,0.2);'
                    f'border-radius:3px;padding:0 2px;">{ins_text}</span>'
                )

        self.diff_view.setHtml(
            f'<p style="margin:0;line-height:1.5;font-family:Segoe UI,sans-serif;">'
            f'{" ".join(parts)}</p>'
        )
