# -*- coding: utf-8 -*-
"""自定义控件：圆形进度环 + 无边框弹窗基类。"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from . import icons

COLOR_TRACK = QColor("#F2F3F5")
COLOR_FOCUS = QColor("#C2C7CE")
COLOR_BREAK = QColor("#52C41A")
COLOR_BREAK_TEXT = QColor("#389E0D")

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"


class TimerRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 1.0
        self._break = False
        self.setMinimumSize(120, 120)
        # 关键：允许布局拉伸，环随可用空间放大（否则永远停留在最小尺寸）
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_progress(self, p):
        self._progress = max(0.0, min(1.0, p))
        self.update()

    def set_break(self, b):
        self._break = bool(b)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        pen_width = max(4, side // 28)
        rect = self.rect().adjusted(pen_width // 2 + 2, pen_width // 2 + 2,
                                    -(pen_width // 2) - 2, -(pen_width // 2) - 2)
        side = min(rect.width(), rect.height())
        rect = rect.adjusted((rect.width() - side) // 2, (rect.height() - side) // 2,
                             -(rect.width() - side) // 2, -(rect.height() - side) // 2)

        # 底环（很浅的灰）
        pen = QPen(COLOR_TRACK, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # 剩余弧（从顶部顺时针，随倒计时收缩）
        arc_color = COLOR_BREAK if self._break else COLOR_FOCUS
        pen = QPen(arc_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        span = int(-360 * self._progress * 16)
        painter.drawArc(rect, 90 * 16, span)


class FramelessDialog(QDialog):
    """无边框弹窗基类：白底 + 顶部标题行（标题+关闭），与主界面顶部风格一致，可拖动、首次打开居中。

    业务内容加进 self.layout（基类已配置好边距）。
    说明：不用透明背景（WA_TranslucentBackground 在本机渲染不可靠，导致弹窗不显示/错位），
    白底矩形 + 淡边框与主界面视觉统一即可。
    """

    def __init__(self, title, parent=None):
        super().__init__(parent)
        # Tool：不占任务栏，跟随主窗口；Frameless：无系统标题栏，顶部样式统一
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self._drag_offset = None
        self._centered = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.body = QWidget(self)
        self.body.setObjectName("dialogBody")
        self.body.setStyleSheet(
            f"QWidget#dialogBody {{ background: #FFFFFF; border: 1px solid #E1E3E7; }}")
        bl = QVBoxLayout(self.body)
        bl.setContentsMargins(20, 10, 20, 16)
        bl.setSpacing(12)

        # 顶部标题行：左标题 + 右侧关闭（与主界面顶栏一致的简洁白底）
        tb = QHBoxLayout()
        tb.setSpacing(8)
        self.title_lbl = QLabel(title, self.body)
        f = self.title_lbl.font()
        f.setPointSize(11)
        f.setBold(True)
        self.title_lbl.setFont(f)
        tb.addWidget(self.title_lbl)
        tb.addStretch(1)
        self.close_btn = QToolButton(self.body)
        self.close_btn.setIcon(icons.close_icon())
        self.close_btn.setIconSize(QSize(18, 18))
        self.close_btn.setStyleSheet(
            "QToolButton { border: none; background: transparent; border-radius: 6px; padding: 2px; }"
            "QToolButton:hover { background: #F3F4F6; }")
        self.close_btn.clicked.connect(self.close)
        tb.addWidget(self.close_btn)
        bl.addLayout(tb)

        self.layout = bl
        outer.addWidget(self.body)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._centered:
            self._centered = True
            parent = self.parentWidget()
            if parent is not None and parent.isVisible():
                target = parent.frameGeometry()
            else:
                scr = self.screen() or QApplication.primaryScreen()
                target = scr.availableGeometry() if scr else None
            if target is not None:
                self.move(target.center().x() - self.width() // 2,
                          target.center().y() - self.height() // 2)

    # ---------- 拖动 ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (event.globalPosition().toPoint()
                                 - self.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)
