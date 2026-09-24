# -*- coding: utf-8 -*-
"""计时状态机：mode(专注/休息) × state(待开始/计时中/已暂停)。

计时基于系统单调时钟（time.monotonic），UI 定时器只负责刷新显示，
卡顿、窗口切换、系统休眠唤醒都不会导致时间漂移。
"""
import math
import time

from PySide6.QtCore import QObject, QTimer, Signal

MODE_FOCUS = "focus"
MODE_BREAK = "break"

STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"

MIN_MINUTES = 1
MAX_MINUTES = 180


class TimerState(QObject):
    tick = Signal(int)              # 剩余秒数（每次整数秒变化）
    finished = Signal(str)          # 阶段结束，参数为结束的模式
    mode_changed = Signal(str)      # 模式切换
    state_changed = Signal(str, str)  # (mode, state)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.mode = MODE_FOCUS
        self.state = STATE_IDLE
        self.total = config.get("focus_minutes") * 60
        self.remaining = self.total
        self._end_ts = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._on_tick)
        # 用户操作版本号：每次用户主动操作 +1，用于弹窗判断"期间是否已被用户改过状态"
        self.mutation_count = 0

    # ---------- 只读 ----------
    def minutes(self):
        return self.total // 60

    def progress(self):
        """剩余比例 0~1，用于进度环 / 进度条"""
        if self.total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.remaining / self.total))

    # ---------- 时长 ----------
    def set_minutes(self, m):
        m = int(m)
        if m < MIN_MINUTES:
            m = MIN_MINUTES
        if m > MAX_MINUTES:
            m = MAX_MINUTES
        self.total = m * 60
        self.remaining = self.total
        self._stop_clock()
        self.state = STATE_IDLE
        self.mutation_count += 1
        # 持久化当前模式的时长
        key = "focus_minutes" if self.mode == MODE_FOCUS else "break_minutes"
        self.config.set(key, m)
        self.tick.emit(self.remaining)
        self.state_changed.emit(self.mode, self.state)

    def nudge_minutes(self, delta):
        """±5 分钟。倒计时中/已暂停：在【当前剩余时间】基础上增减，不打断计时；
        待开始：调整总时长（同 set_minutes）。"""
        self.mutation_count += 1
        if self.state != STATE_IDLE:
            # 只改剩余时间，总时长保持不变
            new_remaining = self.remaining + delta * 60
            new_remaining = max(MIN_MINUTES * 60, min(MAX_MINUTES * 60, new_remaining))
            self.remaining = new_remaining
            if self.state == STATE_RUNNING:
                self._end_ts = time.monotonic() + self.remaining
            self.tick.emit(self.remaining)
        else:
            self.set_minutes(self.minutes() + delta)

    # ---------- 模式 ----------
    def switch_mode(self, mode):
        if mode not in (MODE_FOCUS, MODE_BREAK):
            return
        self.mode = mode
        key = "focus_minutes" if mode == MODE_FOCUS else "break_minutes"
        self.total = self.config.get(key) * 60
        self.remaining = self.total
        self._stop_clock()
        self.state = STATE_IDLE
        self.mutation_count += 1
        self.mode_changed.emit(mode)
        self.state_changed.emit(mode, self.state)
        self.tick.emit(self.remaining)

    def toggle_mode(self):
        self.switch_mode(MODE_BREAK if self.mode == MODE_FOCUS else MODE_FOCUS)

    # ---------- 控制 ----------
    def start(self):
        if self.remaining <= 0:
            self.remaining = self.total
        self.state = STATE_RUNNING
        self._end_ts = time.monotonic() + self.remaining
        self._timer.start()
        self.mutation_count += 1
        self.state_changed.emit(self.mode, self.state)

    def pause(self):
        if self.state != STATE_RUNNING:
            return
        self.remaining = self._compute_remaining()
        self._stop_clock()
        self.state = STATE_PAUSED
        self.mutation_count += 1
        self.state_changed.emit(self.mode, self.state)
        self.tick.emit(self.remaining)

    def resume(self):
        if self.state != STATE_PAUSED:
            return
        self.state = STATE_RUNNING
        self._end_ts = time.monotonic() + self.remaining
        self._timer.start()
        self.mutation_count += 1
        self.state_changed.emit(self.mode, self.state)

    def toggle_start(self):
        if self.state == STATE_RUNNING:
            self.pause()
        else:
            self.resume() if self.state == STATE_PAUSED else self.start()

    def reset(self):
        self.remaining = self.total
        self._stop_clock()
        self.state = STATE_IDLE
        self.mutation_count += 1
        self.state_changed.emit(self.mode, self.state)
        self.tick.emit(self.remaining)

    def skip(self):
        """跳过当前阶段：切到另一模式待开始"""
        self.toggle_mode()

    # ---------- 内部 ----------
    def _compute_remaining(self):
        r = self._end_ts - time.monotonic()
        return max(0, int(math.ceil(r - 1e-9)))

    def _stop_clock(self):
        self._timer.stop()

    def _on_tick(self):
        remain = self._end_ts - time.monotonic()
        if remain <= 0:
            self._stop_clock()
            self.remaining = 0
            self.state = STATE_IDLE
            self.tick.emit(0)
            self.state_changed.emit(self.mode, self.state)
            self.finished.emit(self.mode)
        else:
            secs = int(math.ceil(remain - 1e-9))
            if secs != self.remaining:
                self.remaining = secs
                self.tick.emit(secs)
