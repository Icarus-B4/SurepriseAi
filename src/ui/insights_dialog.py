"""
insights_dialog.py
Lokales Insights-Dashboard: WPM, Streak, Top-Apps und 7-Tage-Verlauf.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from src.services.usage_stats import UsageStatsService
from src.ui.design_tokens import Colors, FluentIcons, Typography
from src.utils.translation import tr


class InsightsDialog(QDialog):
    """Zeigt Nutzungs-Insights aus lokal persistierten Stats."""

    def __init__(
        self,
        stats: UsageStatsService,
        parent=None,
        embedded: bool = False,
    ):
        super().__init__(parent)
        self.stats = stats
        self._embedded = embedded
        if embedded:
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
        self._metric_labels: dict[str, QLabel] = {}
        self._metric_captions: dict[str, QLabel] = {}
        self._apps_container: QVBoxLayout | None = None
        self._chart_container: QHBoxLayout | None = None
        self._build_ui()
        self._apply_style()
        self.retranslate_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.header_title = QLabel()
        self.header_title.setFont(Typography.get_font(Typography.MEDIUM, bold=True))
        self.header_subtitle = QLabel()
        self.header_subtitle.setFont(Typography.get_font(Typography.TINY))
        title_box.addWidget(self.header_title)
        title_box.addWidget(self.header_subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.header_close_btn = QPushButton(FluentIcons.CLOSE)
        self.header_close_btn.setObjectName("CloseButton")
        self.header_close_btn.setFixedSize(34, 34)
        self.header_close_btn.clicked.connect(self.accept)
        header.addWidget(self.header_close_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(14)
        body_layout.setContentsMargins(0, 0, 0, 0)

        grid = QGridLayout()
        grid.setSpacing(10)
        for idx, key in enumerate(
            ("today_words", "today_wpm", "streak", "week_words")
        ):
            card = self._make_metric_card(key)
            grid.addWidget(card, idx // 2, idx % 2)
        body_layout.addLayout(grid)

        self.week_title = QLabel()
        self.week_title.setFont(Typography.get_font(Typography.SMALL, bold=True))
        body_layout.addWidget(self.week_title)

        chart_row = QWidget()
        self._chart_container = QHBoxLayout(chart_row)
        self._chart_container.setSpacing(8)
        self._chart_container.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(chart_row)

        self.apps_title = QLabel()
        self.apps_title.setFont(Typography.get_font(Typography.SMALL, bold=True))
        body_layout.addWidget(self.apps_title)

        apps_box = QWidget()
        self._apps_container = QVBoxLayout(apps_box)
        self._apps_container.setSpacing(8)
        self._apps_container.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(apps_box)
        body_layout.addStretch(1)

        scroll.setWidget(body)
        layout.addWidget(scroll, stretch=1)

    def _make_metric_card(self, key: str) -> QFrame:
        card = QFrame()
        card.setObjectName("InsightsMetricCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)

        value = QLabel("0")
        value.setObjectName("InsightsMetricValue")
        value.setFont(Typography.get_font(Typography.TITLE, bold=True))

        caption = QLabel()
        caption.setObjectName("InsightsMetricCaption")
        caption.setFont(Typography.get_font(Typography.TINY))
        self._metric_captions[key] = caption

        lay.addWidget(value)
        lay.addWidget(caption)
        self._metric_labels[key] = value
        return card

    def refresh(self) -> None:
        data = self.stats.get_insights()
        self._metric_labels["today_words"].setText(str(data["today_words"]))
        self._metric_labels["today_wpm"].setText(str(data["today_avg_wpm"]))
        self._metric_labels["streak"].setText(str(data["streak_days"]))
        self._metric_labels["week_words"].setText(str(data["week_words"]))

        self._render_week_chart(data["daily_series"])
        self._render_top_apps(data["top_apps"])

    def _render_week_chart(self, series: list[dict]) -> None:
        if not self._chart_container:
            return
        while self._chart_container.count():
            item = self._chart_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_words = max((d["words"] for d in series), default=1) or 1
        for day in series:
            col = QWidget()
            col_lay = QVBoxLayout(col)
            col_lay.setContentsMargins(0, 0, 0, 0)
            col_lay.setSpacing(4)
            col_lay.setAlignment(Qt.AlignmentFlag.AlignBottom)

            bar = QFrame()
            bar.setObjectName("InsightsBar")
            height = max(8, int(72 * day["words"] / max_words))
            bar.setFixedSize(28, height)

            lbl = QLabel(day["label"])
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(Typography.get_font(Typography.TINY))
            lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")

            val = QLabel(str(day["words"]))
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setFont(Typography.get_font(Typography.TINY, bold=True))

            col_lay.addWidget(val, alignment=Qt.AlignmentFlag.AlignCenter)
            col_lay.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            col_lay.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            self._chart_container.addWidget(col, stretch=1)

    def _render_top_apps(self, top_apps: list[tuple[str, int]]) -> None:
        if not self._apps_container:
            return
        while self._apps_container.count():
            item = self._apps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not top_apps:
            empty = QLabel(tr("insights_no_apps"))
            empty.setFont(Typography.get_font(Typography.SMALL))
            empty.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
            self._apps_container.addWidget(empty)
            return

        max_count = top_apps[0][1] or 1
        for app_key, count in top_apps:
            row = QWidget()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(10)

            name = QLabel(app_key)
            name.setFont(Typography.get_font(Typography.SMALL, bold=True))
            name.setMinimumWidth(100)

            bar = QFrame()
            bar.setObjectName("InsightsAppBar")
            bar.setFixedHeight(10)
            bar.setMinimumWidth(max(24, int(220 * count / max_count)))

            count_lbl = QLabel(str(count))
            count_lbl.setFont(Typography.get_font(Typography.TINY))
            count_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")

            row_lay.addWidget(name)
            row_lay.addWidget(bar, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)
            row_lay.addWidget(count_lbl)
            self._apps_container.addWidget(row)

    def retranslate_ui(self) -> None:
        self.header_title.setText(tr("insights_title"))
        self.header_subtitle.setText(tr("insights_subtitle"))
        self.week_title.setText(tr("insights_week_chart"))
        self.apps_title.setText(tr("insights_top_apps"))

        captions = {
            "today_words": tr("insights_today_words"),
            "today_wpm": tr("insights_today_wpm"),
            "streak": tr("insights_streak"),
            "week_words": tr("insights_week_words"),
        }
        for key, text in captions.items():
            if key in self._metric_captions:
                self._metric_captions[key].setText(text)

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.SURFACE_ELEVATED};
                color: {Colors.TEXT_PRIMARY_HEX};
            }}
            QFrame#InsightsMetricCard {{
                background: {Colors.CONTROL_FILL_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 12px;
            }}
            QLabel#InsightsMetricValue {{
                color: {Colors.ACCENT_BRIGHT_HEX};
            }}
            QLabel#InsightsMetricCaption {{
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
            QFrame#InsightsBar {{
                background: {Colors.ACCENT_HEX};
                border-radius: 6px;
            }}
            QFrame#InsightsAppBar {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_HEX},
                    stop:1 {Colors.ACCENT_BRIGHT_HEX}
                );
                border-radius: 5px;
            }}
            QPushButton#CloseButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 17px;
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
            QPushButton#CloseButton:hover {{
                color: {Colors.TEXT_PRIMARY_HEX};
                border-color: {Colors.ACCENT_BRIGHT_HEX};
            }}
        """)
