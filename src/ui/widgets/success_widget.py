"""
success_widget.py
Widget für den SUCCESS-Zustand der Dynamic Island.
Zeigt Erfolgsmeldung, Diff-Hinweis und eine kurze Textvorschau.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.utils.diff_helper import count_text_changes, texts_differ


class SuccessWidget(QWidget):
    """Widget für den Erfolgs-Zustand (Success)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.succ_icon = QLabel(FluentIcons.CHECKMARK, self)
        self.succ_icon.setObjectName("IconLabel")
        self.succ_icon.setStyleSheet(f"color: {Colors.SUCCESS_GREEN_HEX};")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(0)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        self.success_label = QLabel("Kopiert!", self)
        self.success_label.setFont(Typography.get_font(Typography.SMALL, bold=True))
        self.success_label.setStyleSheet(f"color: {Colors.SUCCESS_GREEN_HEX};")

        self.diff_badge = QLabel("", self)
        self.diff_badge.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.diff_badge.setStyleSheet(
            f"color: {Colors.ACCENT_BRIGHT_HEX}; background: transparent;"
        )
        self.diff_badge.hide()

        title_row.addWidget(self.success_label)
        title_row.addWidget(self.diff_badge)
        title_row.addStretch()

        self.success_text_preview = QLabel("", self)
        self.success_text_preview.setFont(Typography.get_font(Typography.TINY))
        self.success_text_preview.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")

        self.diff_hint = QLabel("", self)
        self.diff_hint.setFont(Typography.get_font(Typography.TINY))
        self.diff_hint.setStyleSheet(f"color: {Colors.TEXT_TERTIARY_HEX};")
        self.diff_hint.hide()

        text_col.addLayout(title_row)
        text_col.addWidget(self.success_text_preview)
        text_col.addWidget(self.diff_hint)

        lay.addWidget(self.succ_icon)
        lay.addLayout(text_col, stretch=1)

    def show_success(self, text: str, raw: str = "") -> bool:
        """
        Bereitet Textvorschau und Diff-Hinweis auf.
        Returns True wenn ein sinnvoller Diff vorliegt.
        """
        preview = text.replace("\n", " ")
        if len(preview) > 36:
            preview = preview[:33] + "..."
        self.success_text_preview.setText(preview)

        has_diff = texts_differ(raw, text)
        if has_diff:
            changes = count_text_changes(raw, text)
            self.success_label.setText("Bereinigt!")
            self.diff_badge.setText(f"{changes} Änd.")
            self.diff_badge.show()
            self.diff_hint.setText("Klick öffnet Vorher/Nachher-Diff")
            self.diff_hint.show()
        else:
            self.success_label.setText("Kopiert!")
            self.diff_badge.hide()
            self.diff_hint.hide()
        return has_diff
