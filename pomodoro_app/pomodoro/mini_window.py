# -*- coding: utf-8 -*-
"""置顶小窗：无边框圆角、环形进度、可拖拽、右下角缩放、双击展开；播放/暂停 + 重置。"""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from . import icons
from .state import MODE_BREAK, STATE_RUNNING
from .widgets import TimerRing

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"

RESIZE_MARGIN = 20
MIN_W, MIN_H = 180, 140
MAX_W, MAX_H = 420, 320

MODE_STYLE = """
QLabel {{ color: #6B7280; font-size: 13px; font-family: {font}; }}
"""
TIME_STYLE = """
QLabel {{ color: #1A1B1C; font-family: {font}; }}
"""
CLOSE_STYLE = """
QToolButton {{
    border: none; border-radius: 15px; background: transparent;
    font-family: {font};
}}
QToolButton:hover {{ background: #F3F4F6; }}
"""
ROUND_BTN = """
QPushButton {{
    border: none; border-radius: {r}px; background: {bg};
    font-family: {font};
}}
QPushButton:hover {{ background: {bg_hover}; }}
"""
ROUND_BTN_LINE = """
QPushButton {{
    border: 1.2px solid rgba(0,0,0,0.2); border-radius: {r}px;
    background: transparent; font-family: {font};
}}
QPushButton:hover {{ background: #F3F4F6; }}
"""
DOT_STYLE = """
QLabel {{ background: {color}; border-radius: 4px; }}
"""


class MiniWindow(QWidget):
    expand_requested = Signal()

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._drag_offset = None
        self._resizing = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(MIN_W, MIN_H)
        self.setMaximumSize(MAX_W, MAX_H)
        self.resize(240, 190)

        self._build_ui()
        self._connect()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 6, 12, 10)
        root.setSpacing(4)

        # 顶行：模式名严格居中 + 放大按钮（右上）
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(0)
        top.addSpacing(30)  # 补偿右侧放大按钮宽度，保证模式名真正居中
        top.addStretch(1)
        center = QHBoxLayout()
        center.setSpacing(5)
        self.dot = QLabel(self)
        self.dot.setFixedSize(8, 8)
        center.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignVCenter)
        self.mode_label = QLabel("专注", self)
        self.mode_label.setStyleSheet(MODE_STYLE.format(font=FONT_FAMILY))
        center.addWidget(self.mode_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addLayout(center)
        top.addStretch(1)
        self.expand_btn = QToolButton(self)
        self.expand_btn.setIcon(icons.fullscreen_icon(color="#9CA3AF"))
        self.expand_btn.setIconSize(QSize(16, 16))
        self.expand_btn.setStyleSheet(CLOSE_STYLE.format(font=FONT_FAMILY))
        self.expand_btn.setFixedSize(30, 30)
        self.expand_btn.setToolTip("放大回主窗口")
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top.addWidget(self.expand_btn, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(top)

        # 环形进度 + 时间叠加
        grid = QGridLayout()
        grid.setContentsMargins(0, 2, 0, 2)
        grid.setSpacing(0)
        self.ring = TimerRing(self)
        self.ring.setMinimumSize(100, 100)
        grid.addWidget(self.ring, 0, 0)

        self.time_label = QLabel("25:00", self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(TIME_STYLE.format(font=FONT_FAMILY))
        grid.addWidget(self.time_label, 0, 0, Qt.AlignmentFlag.AlignCenter)
        root.addLayout(grid, 1)

        # 底部按钮：重置 + 播放 + 跳过（居中）
        btns = QHBoxLayout()
        btns.setSpacing(18)
        btns.addStretch(1)
        self.reset_btn = QPushButton(self)
        self.reset_btn.setIcon(icons.reset_icon())
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.addWidget(self.reset_btn)
        self.play_btn = QPushButton(self)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.addWidget(self.play_btn)
        self.skip_btn = QPushButton(self)
        self.skip_btn.setIcon(icons.skip_icon())
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.addWidget(self.skip_btn)
        btns.addStretch(1)
        root.addLayout(btns)

    def _connect(self):
        self.expand_btn.clicked.connect(self.expand_requested)
        self.play_btn.clicked.connect(self.state.toggle_start)
        self.reset_btn.clicked.connect(self.state.reset)
        self.skip_btn.clicked.connect(self.state.skip)
        self.state.tick.connect(self.refresh)
        self.state.mode_changed.connect(self.refresh)
        self.state.state_changed.connect(self._on_state_changed)

    def refresh(self, *args):
        is_break = self.state.mode == MODE_BREAK
        self.mode_label.setText("休息" if is_break else "专注")
        self.dot.setStyleSheet(DOT_STYLE.format(color="#52C41A" if is_break else "#9CA3AF"))
        self.ring.set_break(is_break)
        self.ring.set_progress(self.state.progress())
        m, s = divmod(max(0, self.state.remaining), 60)
        self.time_label.setText(f"{m:02d}:{s:02d}")
        self._update_play_btn()

    def _on_state_changed(self, mode, state):
        self.refresh()

    def _update_play_btn(self):
        st = self.state.state
        # 参考主界面配色但调淡：专注=淡蓝、休息=淡绿
        if self.state.mode == MODE_BREAK:
            bg, hover = "#73D13D", "#63C22F"
        else:
            bg, hover = "#6E9EF5", "#5A8EF0"
        if st == STATE_RUNNING:
            self.play_btn.setIcon(icons.pause_icon())
        else:
            self.play_btn.setIcon(icons.play_icon())
        self.play_btn.setStyleSheet(ROUND_BTN.format(r=16, bg=bg, bg_hover=hover,
                                                     font=FONT_FAMILY))
        self.play_btn.setIconSize(QSize(12, 12))
        self.play_btn.setFixedSize(32, 32)
        self.reset_btn.setStyleSheet(ROUND_BTN_LINE.format(r=16, font=FONT_FAMILY))
        self.reset_btn.setIconSize(QSize(12, 12))
        self.reset_btn.setFixedSize(32, 32)
        self.skip_btn.setStyleSheet(ROUND_BTN_LINE.format(r=16, font=FONT_FAMILY))
        self.skip_btn.setIconSize(QSize(12, 12))
        self.skip_btn.setFixedSize(32, 32)

    # ---------- 绘制背景 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#E1E3E7"), 1.2))
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 16, 16)

    # ---------- 拖拽 / 缩放 ----------
    def _in_resize_zone(self, pos):
        return (pos.x() >= self.width() - RESIZE_MARGIN
                and pos.y() >= self.height() - RESIZE_MARGIN)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._in_resize_zone(event.position().toPoint()):
                self._resizing = True
            else:
                self._resizing = False
                self._drag_offset = (event.globalPosition().toPoint()
                                     - self.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            gpos = event.globalPosition().toPoint()
            self.resize(max(MIN_W, gpos.x() - self.frameGeometry().left()),
                        max(MIN_H, gpos.y() - self.frameGeometry().top()))
            return
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self._resizing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._in_resize_zone(
                event.position().toPoint()):
            self.expand_requested.emit()
        super().mouseDoubleClickEvent(event)

    # ---------- 字号自适应 ----------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        side = min(self.ring.width(), self.ring.height())
        # 时间是小窗最重要的信息：字号加大、加深
        font_size = max(20, min(42, int(side * 0.24)))
        font = QFont(FONT_FAMILY.split(",")[0], font_size)
        font.setWeight(QFont.Weight.Light)
        self.time_label.setFont(font)
