# -*- coding: utf-8 -*-
"""时间到弹窗：无边框置顶，标题 + 文案 + 主/次按钮，播放提示音由主窗口负责。"""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from . import icons
from .state import MODE_BREAK, MODE_FOCUS

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"

POPUP_STYLE = """
QWidget {{ background: transparent; font-family: {font}; }}
"""
TITLE_STYLE = """
QLabel {{ font-size: 14px; font-weight: 700; color: #1A1B1C; font-family: {font}; }}
"""
BODY_STYLE = """
QLabel {{ font-size: 12px; color: #6B7280; font-family: {font}; }}
"""
BTN_PRIMARY_GREEN = """
QPushButton {{
    border: none; border-radius: 6px; padding: 7px 16px;
    font-size: 12px; font-weight: 600; color: #FFFFFF;
    background: #52C41A; font-family: {font};
}}
QPushButton:hover {{ background: #73D13D; }}
"""
BTN_PRIMARY_BLACK = """
QPushButton {{
    border: none; border-radius: 6px; padding: 7px 16px;
    font-size: 12px; font-weight: 600; color: #FFFFFF;
    background: #1A1B1C; font-family: {font};
}}
QPushButton:hover {{ background: #374151; }}
"""
BTN_SECONDARY = """
QPushButton {{
    border: 1px solid #E5E7EB; border-radius: 6px; padding: 7px 16px;
    font-size: 12px; color: #6B7280; background: #FFFFFF; font-family: {font};
}}
QPushButton:hover {{ background: #F9FAFB; }}
"""
CLOSE_STYLE = """
QToolButton {{
    border: none; border-radius: 15px; background: transparent;
    font-family: {font};
}}
QToolButton:hover {{ background: #F3F4F6; }}
"""


class PopupWindow(QWidget):
    primary_clicked = Signal(str)      # 主按钮（开始休息 / 继续专注）
    secondary_clicked = Signal(str)    # 稍后
    tertiary_clicked = Signal(str)     # 再休息一会（仅休息结束弹窗）
    dismissed = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._mode = MODE_FOCUS

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(340, 168)
        self.setStyleSheet(POPUP_STYLE.format(font=FONT_FAMILY))
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 16)
        root.setSpacing(6)

        # 顶行：标题居中 + 关闭（右上角）
        head = QGridLayout()
        head.setSpacing(0)
        self.title_label = QLabel("专注时间到", self)
        self.title_label.setStyleSheet(TITLE_STYLE.format(font=FONT_FAMILY))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(self.title_label, 0, 1)
        self.close_btn = QToolButton(self)
        self.close_btn.setIcon(icons.close_icon())
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setStyleSheet(CLOSE_STYLE.format(font=FONT_FAMILY))
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        head.addWidget(self.close_btn, 0, 2, Qt.AlignmentFlag.AlignRight)
        head.setColumnStretch(0, 1)
        head.setColumnStretch(1, 1)
        head.setColumnStretch(2, 1)
        root.addLayout(head)

        self.body_label = QLabel("", self)
        self.body_label.setStyleSheet(BODY_STYLE.format(font=FONT_FAMILY))
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.body_label)
        root.addStretch(1)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addStretch(1)
        self.tertiary_btn = QPushButton("再休息一会", self)
        self.tertiary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tertiary_btn.setStyleSheet(BTN_SECONDARY.format(font=FONT_FAMILY))
        self.tertiary_btn.setFixedHeight(32)
        self.tertiary_btn.hide()
        btns.addWidget(self.tertiary_btn)
        self.primary_btn = QPushButton(self)
        self.primary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary_btn.setFixedHeight(32)
        btns.addWidget(self.primary_btn)
        self.secondary_btn = QPushButton("稍后", self)
        self.secondary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.secondary_btn.setStyleSheet(BTN_SECONDARY.format(font=FONT_FAMILY))
        self.secondary_btn.setFixedHeight(32)
        btns.addWidget(self.secondary_btn)
        btns.addStretch(1)
        root.addLayout(btns)

        self.close_btn.clicked.connect(self._on_close)
        self.primary_btn.clicked.connect(self._on_primary)
        self.secondary_btn.clicked.connect(self._on_secondary)
        self.tertiary_btn.clicked.connect(self._on_tertiary)

    def _on_close(self):
        self.hide()
        self.dismissed.emit()

    def _on_primary(self):
        self.hide()
        self.primary_clicked.emit(self._mode)

    def _on_secondary(self):
        self.hide()
        self.secondary_clicked.emit(self._mode)

    def _on_tertiary(self):
        self.hide()
        self.tertiary_clicked.emit(self._mode)

    def show_popup(self, mode, minutes):
        self._mode = mode
        if mode == MODE_FOCUS:
            self.title_label.setText("专注时间到")
            self.body_label.setText(f"已专注 {minutes} 分钟，休息一下吧")
            self.primary_btn.setText("开始休息")
            self.primary_btn.setStyleSheet(BTN_PRIMARY_GREEN.format(font=FONT_FAMILY))
            self.tertiary_btn.hide()
        else:
            self.title_label.setText("休息时间到")
            self.body_label.setText("休息结束，继续专注吧")
            self.primary_btn.setText("继续专注")
            self.primary_btn.setStyleSheet(BTN_PRIMARY_BLACK.format(font=FONT_FAMILY))
            self.tertiary_btn.show()
        self.primary_btn.setMinimumWidth(88)
        self.secondary_btn.setMinimumWidth(88)
        self.tertiary_btn.setMinimumWidth(88)
        self.adjustSize()
        self._place_bottom_right()
        self.show()
        self.raise_()
        self.activateWindow()

    def _place_bottom_right(self):
        screen = self.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.width() - 24, geo.bottom() - self.height() - 24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#E1E3E7"), 1.2))
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
