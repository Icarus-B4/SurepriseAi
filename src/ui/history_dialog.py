"""
history_dialog.py
Dialog zur Durchsicht der Diktat-Historie mit Suche und Kopieren.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QApplication, QMessageBox,
)
from PyQt6.QtCore import Qt

from src.services.dictation_history import DictationHistoryService
from src.services.style_definitions import style_label
from src.ui.history_export_dialog import export_history_entry
from src.ui.design_tokens import Colors, Typography


class HistoryDialog(QDialog):
    """Zeigt letzte Diktate mit Volltextsuche."""

    def __init__(self, history: DictationHistoryService, parent=None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("Diktat-Verlauf")
        self.setMinimumSize(520, 420)
        self._build_ui()
        self._apply_style()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("Letzte Diktate – suchen oder erneut kopieren")
        hint.setFont(Typography.get_font(Typography.SMALL))
        layout.addWidget(hint)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche im Text…")
        self.search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._copy_selected)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.export_btn = QPushButton("Exportieren…")
        self.export_btn.clicked.connect(self._export_selected)
        self.copy_btn = QPushButton("In Zwischenablage kopieren")
        self.copy_btn.clicked.connect(self._copy_selected)
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.SURFACE_HEX};
                color: {Colors.TEXT_PRIMARY_HEX};
            }}
            QLineEdit {{
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 6px;
                padding: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QListWidget {{
                background: {Colors.ISLAND_BG_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Colors.BORDER_SUBTLE_HEX};
            }}
            QListWidget::item:selected {{
                background: {Colors.SURFACE_ELEVATED};
            }}
            QPushButton {{
                background: {Colors.ACCENT_HEX};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_BRIGHT_HEX};
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
        """)

    def _refresh_list(self, query: str = "") -> None:
        self.list_widget.clear()
        entries = self.history.search(query) if query else self.history.list_all()
        for entry in entries:
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            style = style_label(entry.get("style", ""))
            preview = entry.get("polished", "").replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "…"
            label = f"{ts}  ·  {style}  ·  {preview}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.list_widget.addItem(item)

    def _on_search(self, text: str) -> None:
        self._refresh_list(text)

    def _copy_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        text = entry.get("polished", "") if isinstance(entry, dict) else str(entry)
        if text:
            QApplication.clipboard().setText(text)

    def _export_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(entry, dict) and export_history_entry(entry, self):
            QMessageBox.information(self, "Export", "Datei wurde gespeichert.")
