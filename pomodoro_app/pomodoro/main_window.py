# -*- coding: utf-8 -*-
"""主窗口：无边框圆角+淡边框；页签 + 大号浅灰进度环 + 可编辑倒计时 + 右侧加减 + 三圆形操作按钮 + 顶栏工具。"""
from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QIntValidator, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QToolButton, QVBoxLayout, QWidget,
)

from . import icons
from .config import Config
from .state import MODE_BREAK, MODE_FOCUS, STATE_IDLE, STATE_PAUSED, STATE_RUNNING, TimerState
from .widgets import TimerRing

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"

RESIZE_MARGIN = 20

TAB_STYLE = """
QPushButton {{
    border: none; background: transparent;
    padding: 6px 22px; font-size: 14px; color: #9CA3AF;
    border-bottom: 2px solid transparent; font-family: {font};
}}
QPushButton:checked {{ color: #1A1B1C; font-weight: 600; }}
QPushButton:focus {{ outline: none; }}
"""

TOOL_STYLE = """
QToolButton {{
    border: none; background: transparent;
    border-radius: 6px; padding: 4px;
}}
QToolButton:hover {{ background: #F3F4F6; }}
QToolButton:checked {{ background: #1A1B1C; border-radius: 6px; }}
QToolButton:focus {{ outline: none; }}
"""

TIME_EDIT_STYLE = """
QLineEdit {{
    border: none; background: transparent; color: #1A1B1C;
    font-family: {font};
    selection-background-color: #E5E7EB;
}}
QLineEdit:focus {{ border: 1px solid #E5E7EB; border-radius: 10px; }}
"""

STEP_BTN = """
QPushButton {{
    border: 1px solid #E5E7EB; border-radius: 17px; background: #FFFFFF;
    font-size: 18px; color: #1A1B1C; font-family: {font};
}}
QPushButton:hover {{ background: #F6F7F8; }}
"""

OP_LINE_BTN = """
QPushButton {{
    border: 1.2px solid #D8DCE2; border-radius: {r}px;
    background: transparent; font-family: {font};
}}
QPushButton:hover {{ background: #F6F7F8; }}
"""

# 主按钮实心填充样式（专注=蓝、休息=绿），白色图标
FILLED_BTN = """
QPushButton {{
    border: none; border-radius: {r}px;
    background: {bg}; font-family: {font};
}}
QPushButton:hover {{ background: {bg_h}; }}
QPushButton:pressed {{ background: {bg_p}; }}
"""


class MainWindow(QWidget):
    request_mini = Signal()
    request_popup = Signal()
    request_stats = Signal()

    def __init__(self, config: Config, state: TimerState, sounds, parent=None):
        super().__init__(parent)
        self.config = config
        self.state = state
        self.sounds = sounds
        self.mini_window = None
        self.popup = None
        self.settings_dialog = None
        self._drag_offset = None
        self._resizing = False
        self._start_state = STATE_IDLE

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(480, 480)
        self.resize(760, 760)
        self._build_ui()
        self._connect_signals()
        self._apply_config_initial()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶栏（无边框窗口，不放名称；左侧设置，右侧小窗/置顶/全屏/最小化/关闭）
        top = QHBoxLayout()
        top.setContentsMargins(12, 4, 12, 0)
        self.gear_btn = QToolButton(self)
        self.gear_btn.setIcon(icons.gear_icon())
        self.gear_btn.setIconSize(QSize(20, 20))
        self.gear_btn.setToolTip("设置")
        top.addWidget(self.gear_btn)

        self.stats_btn = QToolButton(self)
        self.stats_btn.setIcon(icons.stats_icon())
        self.stats_btn.setIconSize(QSize(20, 20))
        self.stats_btn.setToolTip("统计")
        top.addWidget(self.stats_btn)

        top.addStretch(1)

        self.mini_btn = QToolButton(self)
        self.mini_btn.setIcon(icons.mini_icon())
        self.mini_btn.setIconSize(QSize(20, 20))
        self.mini_btn.setToolTip("缩小为置顶小窗")
        top.addWidget(self.mini_btn)

        self.pin_btn = QToolButton(self)
        self.pin_btn.setIcon(icons.pin_icon())
        self.pin_btn.setIconSize(QSize(20, 20))
        self.pin_btn.setCheckable(True)
        self.pin_btn.setToolTip("置顶")
        top.addWidget(self.pin_btn)

        self.fullscreen_btn = QToolButton(self)
        self.fullscreen_btn.setIcon(icons.fullscreen_icon())
        self.fullscreen_btn.setIconSize(QSize(20, 20))
        self.fullscreen_btn.setCheckable(True)
        self.fullscreen_btn.setToolTip("全屏")
        top.addWidget(self.fullscreen_btn)

        self.minimize_btn = QToolButton(self)
        self.minimize_btn.setIcon(icons.minimize_icon())
        self.minimize_btn.setIconSize(QSize(20, 20))
        self.minimize_btn.setToolTip("最小化")
        top.addWidget(self.minimize_btn)

        self.close_btn = QToolButton(self)
        self.close_btn.setIcon(icons.close_icon())
        self.close_btn.setIconSize(QSize(18, 18))
        self.close_btn.setToolTip("关闭")
        top.addWidget(self.close_btn)
        root.addLayout(top)

        # 页签
        tabs = QHBoxLayout()
        tabs.setContentsMargins(0, 4, 0, 0)
        tabs.setSpacing(0)
        tabs.addStretch(1)
        self.focus_tab = QPushButton("专注", self)
        self.break_tab = QPushButton("休息", self)
        self.focus_tab.setCheckable(True)
        self.break_tab.setCheckable(True)
        for b in (self.focus_tab, self.break_tab):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(TAB_STYLE.format(font=FONT_FAMILY))
            tabs.addWidget(b)
        tabs.addStretch(1)
        root.addLayout(tabs)

        # 计时区：大环（占满弹性空间，随窗口缩放）+ 右侧竖排加减（手动贴环、整体居中）
        # 左右各 20%、中间 60%：环天然占窗口宽 60%，随窗口等比缩放
        mid = QHBoxLayout()
        mid.setContentsMargins(0, 35, 0, 4)
        mid.setSpacing(0)
        mid.addStretch(2)
        grid = QGridLayout()
        grid.setSpacing(0)
        self.ring = TimerRing(self)
        self.ring.setMinimumSize(320, 320)
        grid.addWidget(self.ring, 0, 0)

        # 环中心：倒计时 + 下方小字实时时间
        center_col = QVBoxLayout()
        center_col.setSpacing(4)
        self.time_edit = QLineEdit(self)
        self.time_edit.setStyleSheet(TIME_EDIT_STYLE.format(font=FONT_FAMILY))
        self.time_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_edit.setValidator(QIntValidator(1, 180, self))
        self.time_edit.setFrame(False)
        center_col.addWidget(self.time_edit, 0, Qt.AlignmentFlag.AlignHCenter)

        clock_row = QHBoxLayout()
        clock_row.setSpacing(7)
        clock_row.addStretch(1)
        self.clock_icon_lbl = QLabel(self)
        self.clock_icon_lbl.setPixmap(icons.bell_icon(color="#9CA3AF", size=18).pixmap(18, 18))
        clock_row.addWidget(self.clock_icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.clock_label = QLabel("", self)
        self.clock_label.setStyleSheet(
            f"font-size: 17px; color: #9CA3AF; font-family: {FONT_FAMILY};")
        clock_row.addWidget(self.clock_label, 0, Qt.AlignmentFlag.AlignVCenter)
        clock_row.addStretch(1)
        center_col.addLayout(clock_row)

        grid.addLayout(center_col, 0, 0, Qt.AlignmentFlag.AlignCenter)
        mid.addLayout(grid, 6)
        mid.addStretch(2)

        # 右侧加减（+ 上 - 下）：手动定位，始终紧贴环右缘、随环垂直居中
        self.plus_btn = QPushButton("＋", self)
        self.minus_btn = QPushButton("−", self)
        for b in (self.plus_btn, self.minus_btn):
            b.setFixedSize(40, 40)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(STEP_BTN.format(font=FONT_FAMILY))
        root.addLayout(mid, 1)

        # 操作区：重置 / 播放暂停 / 跳过（三个圆形框按钮，随时可点）
        ops = QHBoxLayout()
        ops.setContentsMargins(0, 0, 0, 46)
        ops.setSpacing(32)
        ops.addStretch(1)
        self.reset_btn = QPushButton(self)
        self.reset_btn.setIcon(icons.reset_icon())
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ops.addWidget(self.reset_btn)

        self.start_btn = QPushButton(self)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ops.addWidget(self.start_btn)

        self.skip_btn = QPushButton(self)
        self.skip_btn.setIcon(icons.skip_icon())
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ops.addWidget(self.skip_btn)
        ops.addStretch(1)
        root.addLayout(ops)

        for b in (self.pin_btn, self.mini_btn, self.fullscreen_btn, self.gear_btn, self.stats_btn, self.close_btn, self.minimize_btn):
            b.setStyleSheet(TOOL_STYLE)

    # ---------- 信号 ----------
    def _connect_signals(self):
        self.focus_tab.clicked.connect(lambda: self.state.switch_mode(MODE_FOCUS))
        self.break_tab.clicked.connect(lambda: self.state.switch_mode(MODE_BREAK))
        self.minus_btn.clicked.connect(lambda: self.state.nudge_minutes(-5))
        self.plus_btn.clicked.connect(lambda: self.state.nudge_minutes(5))
        self.time_edit.editingFinished.connect(self._on_minutes_edited)
        self.time_edit.returnPressed.connect(self._on_return_pressed)
        self.time_edit.installEventFilter(self)
        self.start_btn.clicked.connect(self.state.toggle_start)
        self.skip_btn.clicked.connect(self.state.skip)
        self.reset_btn.clicked.connect(self.state.reset)

        self.pin_btn.toggled.connect(self._on_pin_toggled)
        self.mini_btn.clicked.connect(self._on_mini_clicked)
        self.fullscreen_btn.toggled.connect(self._on_fullscreen_toggled)
        self.gear_btn.clicked.connect(self._on_gear_clicked)
        self.stats_btn.clicked.connect(self.request_stats.emit)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.close_btn.clicked.connect(self.close)

        self.state.tick.connect(self._on_tick)
        self.state.mode_changed.connect(self._on_mode_changed)
        self.state.state_changed.connect(self._on_state_changed)
        self.state.finished.connect(self._on_finished)

        # 实时时钟：每秒刷新环下方小字时间
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()
        self._update_clock()

    def _update_clock(self):
        from datetime import datetime
        self.clock_label.setText(datetime.now().strftime("%H:%M"))

    def _apply_config_initial(self):
        if self.config.get("always_on_top"):
            self.pin_btn.setChecked(True)
        # 初始状态刷新
        self._on_mode_changed(self.state.mode)
        self._on_state_changed(self.state.mode, self.state.state)

    # ---------- 状态刷新 ----------
    def _fmt_idle(self):
        return f"{self.state.minutes()}"

    def _fmt_clock(self):
        m, s = divmod(max(0, self.state.remaining), 60)
        return f"{m:02d}:{s:02d}"

    def _on_tick(self, secs):
        if self.state.state == STATE_IDLE and self.state.remaining >= self.state.total:
            self.time_edit.setText(self._fmt_idle())
        else:
            self.time_edit.setText(self._fmt_clock())
        self.ring.set_progress(self.state.progress())

    def _on_mode_changed(self, mode):
        is_break = mode == MODE_BREAK
        self.focus_tab.setChecked(not is_break)
        self.break_tab.setChecked(is_break)
        self.ring.set_break(is_break)
        self.time_edit.setText(self._fmt_idle())
        self.ring.set_progress(1.0)
        self._update_op_buttons()

    def _on_state_changed(self, mode, state):
        # 跳过 / 重置随时可点，不做禁用控制
        self.time_edit.setReadOnly(state != STATE_IDLE)
        if state != STATE_IDLE:
            # 倒计时开始后移走输入焦点，去掉聚焦边框
            self.time_edit.clearFocus()
        if state == STATE_IDLE:
            self.time_edit.setText(self._fmt_idle())
        self._update_op_buttons()

    def _update_op_buttons(self):
        st = self.state.state
        self._start_state = st
        is_break = self.state.mode == MODE_BREAK
        # 主按钮：实心填充（专注=蓝、休息=绿），白色图标
        if is_break:
            bg, bh, bp = "#52C41A", "#46A815", "#3D9412"
        else:
            bg, bh, bp = "#3B82F6", "#2F6FE0", "#2A63C8"
        if st == STATE_RUNNING:
            self.start_btn.setIcon(icons.pause_icon(color="#FFFFFF"))
        else:
            self.start_btn.setIcon(icons.play_icon(color="#FFFFFF"))
        self.start_btn.setIconSize(QSize(30, 30))
        self.start_btn.setFixedSize(64, 64)
        self.start_btn.setStyleSheet(FILLED_BTN.format(r=32, bg=bg, bg_h=bh, bg_p=bp, font=FONT_FAMILY))
        # 重置 / 跳过：圆形框样式，图标同步放大
        for b in (self.reset_btn, self.skip_btn):
            b.setStyleSheet(OP_LINE_BTN.format(r=32, font=FONT_FAMILY))
            b.setIconSize(QSize(28, 28))
            b.setFixedSize(64, 64)

    # ---------- 交互 ----------
    def eventFilter(self, obj, event):
        # 点击时间数字：聚焦即全选当前时长，直接输入即可覆盖
        if obj is self.time_edit and event.type() == QEvent.Type.FocusIn:
            QTimer.singleShot(0, self.time_edit.selectAll)
        return super().eventFilter(obj, event)

    def _on_minutes_edited(self):
        text = self.time_edit.text().strip()
        if not text:
            self.time_edit.setText(self._fmt_idle())
            return
        try:
            m = int(text)
        except ValueError:
            self.time_edit.setText(self._fmt_idle())
            return
        if 1 <= m <= 180 and m != self.state.minutes():
            self.state.set_minutes(m)
        else:
            self.time_edit.setText(self._fmt_idle())

    def _on_return_pressed(self):
        """回车：确认输入并直接开始倒计时。"""
        self._on_minutes_edited()
        self.state.start()

    def _on_pin_toggled(self, on):
        self.config.set("always_on_top", on)
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)
        # 更新图标反白（置顶激活时黑底白图标，避免白底看不见）
        if on:
            self.pin_btn.setIcon(icons.pin_icon(color="#FFFFFF"))
        else:
            self.pin_btn.setIcon(icons.pin_icon())
        if visible:
            # setWindowFlag 会隐式隐藏窗口，延迟一帧重新显示
            QTimer.singleShot(0, self.show)

    def _on_mini_clicked(self):
        if self.mini_window is not None:
            self._place_mini_top_right()
            self.hide()
            self.mini_window.refresh()
            self.mini_window.show()

    def _place_mini_top_right(self):
        """缩小小窗时定位到当前屏幕右上角（工作区，避开任务栏），不再需要手动拖。"""
        mw = self.mini_window
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        mw.move(geo.right() - mw.width() - 24, geo.top() + 24)

    def _on_fullscreen_toggled(self, on):
        if on:
            self.showFullScreen()
            self.fullscreen_btn.setIcon(icons.restore_icon(color="#FFFFFF"))
            self.fullscreen_btn.setToolTip("还原窗口")
        else:
            self.showNormal()
            self.fullscreen_btn.setIcon(icons.fullscreen_icon())
            self.fullscreen_btn.setToolTip("全屏")

    def _on_gear_clicked(self):
        if self.settings_dialog is not None:
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def _on_finished(self, mode):
        if mode == MODE_FOCUS:
            self.sounds.play_focus()
        else:
            self.sounds.play_break()
        if self.popup is not None:
            self.popup.show_popup(mode, self.state.minutes())

    # ---------- 窗口 ----------
    def _ensure_on_screen(self):
        """首次显示前：若窗口不在任何屏幕可见区内（多显示器/虚拟桌面），移到主屏中心。"""
        from PySide6.QtGui import QGuiApplication

        screens = QGuiApplication.screens()
        if not screens:
            return
        geo = self.geometry()
        for sc in screens:
            if sc.availableGeometry().intersects(geo):
                return
        center = screens[0].availableGeometry().center()
        self.move(center - self.rect().center())

    def _in_resize_zone(self, pos):
        return (pos.x() >= self.width() - RESIZE_MARGIN
                and pos.y() >= self.height() - RESIZE_MARGIN)

    def mousePressEvent(self, event):
        if self.isFullScreen():
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._in_resize_zone(event.position().toPoint()):
                self._resizing = True
            else:
                self._resizing = False
                self._drag_offset = (event.globalPosition().toPoint()
                                     - self.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isFullScreen():
            super().mouseMoveEvent(event)
            return
        if self._resizing:
            gpos = event.globalPosition().toPoint()
            self.resize(max(self.minimumWidth(), gpos.x() - self.frameGeometry().left()),
                        max(self.minimumHeight(), gpos.y() - self.frameGeometry().top()))
            return
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self._resizing = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isFullScreen():
            p.setPen(QPen(QColor(0, 0, 0, 0), 0))
            p.setBrush(QColor(255, 255, 255))
            p.drawRect(self.rect())
        else:
            p.setPen(QPen(QColor("#E1E3E7"), 1.2))
            p.setBrush(QColor(255, 255, 255))
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 18, 18)

    def _place_step_btns(self):
        """± 按钮贴环右缘 40px、垂直居中于环；先强制完成布局保证环几何最新。"""
        self.layout().activate()
        r = self.ring.geometry()
        if r.width() <= 0:
            return
        sx = r.x() + r.width() + 40
        cy = r.y() + r.height() // 2
        self.plus_btn.move(sx, cy - 47)
        self.minus_btn.move(sx, cy + 7)
        self.plus_btn.raise_()
        self.minus_btn.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        self._place_step_btns()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        side = min(self.ring.width(), self.ring.height())
        font_size = max(26, int(side * 0.20))
        font = QFont(FONT_FAMILY.split(",")[0], font_size)
        font.setWeight(QFont.Weight.Light)
        self.time_edit.setFont(font)
        w = int(side * 0.62)
        self.time_edit.setFixedWidth(max(140, w))
        self._place_step_btns()

    def closeEvent(self, event):
        if self.mini_window is not None:
            self.mini_window.close()
        event.accept()
