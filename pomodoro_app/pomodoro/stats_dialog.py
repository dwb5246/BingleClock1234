# -*- coding: utf-8 -*-
"""专注统计窗口：今日/本周/累计 + 最近 7 天柱状图。简洁轻量。"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .widgets import FramelessDialog

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"

STYLE = f"""
QLabel {{ color: #1A1B1C; font-size: 12px; }}
QLabel.muted {{ color: #6B7280; }}
"""


class _BarChart(QWidget):
    """最近 7 天专注时长柱状图（无依赖自绘）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []  # [(label, minutes)]
        self.setMinimumHeight(120)

    def set_items(self, items):
        self.items = items
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = max(1, len(self.items))
        slot = w / n
        bar_w = min(34.0, slot * 0.55)
        top_margin, bottom_margin = 22, 20
        max_v = max((v for _, v in self.items), default=0) or 1
        f = QFont(FONT_FAMILY.split(",")[0], 9)
        for i, (label, v) in enumerate(self.items):
            cx = slot * i + slot / 2
            bh = (v / max_v) * (h - top_margin - bottom_margin)
            if v > 0 and bh < 4:
                bh = 4
            rect_h = h - top_margin - bottom_margin
            # 柱
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#3B82F6") if v > 0 else QColor("#F1F2F4"))
            p.drawRoundedRect(round(cx - bar_w / 2), round(rect_h + top_margin - bh),
                              round(bar_w), round(bh), 4, 4)
            # 数值
            if v > 0:
                p.setPen(QColor("#1A1B1C"))
                p.setFont(f)
                p.drawText(round(cx - bar_w), round(rect_h + top_margin - bh - 15),
                           round(bar_w * 2), 14, Qt.AlignmentFlag.AlignCenter, str(v))
            # 日期标签
            p.setPen(QColor("#9CA3AF"))
            p.setFont(f)
            p.drawText(round(cx - slot / 2), round(h - bottom_margin + 4),
                       round(slot), 14, Qt.AlignmentFlag.AlignCenter, label)


class StatsDialog(FramelessDialog):
    def __init__(self, stats, parent=None):
        super().__init__("统计", parent)
        self.stats = stats
        self.setWindowTitle("统计")
        self.setFixedSize(340, 285)
        self.setStyleSheet(STYLE)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = self.layout

        # 窗口打开期间每 5 秒自动刷新，避免"测完看不到新数据"
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self.refresh)

        # 今日 / 本周 / 累计
        summary = QHBoxLayout()
        summary.setSpacing(8)
        self.today_lbl = QLabel("今日 0 分钟", self)
        self.week_lbl = QLabel("本周 0 分钟", self)
        self.total_lbl = QLabel("累计 0 分钟", self)
        for lbl in (self.today_lbl, self.week_lbl, self.total_lbl):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"border: 1px solid #E5E7EB; border-radius: 8px; padding: 10px 4px;"
                f"font-size: 12px; color: #1A1B1C; background: #FFFFFF;")
            summary.addWidget(lbl, 1)
        root.addLayout(summary)

        # 7 天柱状图
        self.chart = _BarChart(self)
        root.addWidget(self.chart)

        root.addStretch(1)

    def refresh(self):
        self.today_lbl.setText(f"今日 {self.stats.today()} 分钟")
        self.week_lbl.setText(f"本周 {self.stats.week_total()} 分钟")
        self.total_lbl.setText(f"累计 {self.stats.total()} 分钟")

        days = self.stats.recent(7)
        labels = [d[5:] for d, _ in days]          # MM-DD
        self.chart.set_items([(lbl, v) for lbl, (_, v) in zip(labels, days)])

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self._refresh_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._refresh_timer.stop()
