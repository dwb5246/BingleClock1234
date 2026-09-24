# -*- coding: utf-8 -*-
"""番茄时钟入口。"""
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from pomodoro import icons
from pomodoro.config import Config
from pomodoro.main_window import MainWindow
from pomodoro.mini_window import MiniWindow
from pomodoro.popup import PopupWindow
from pomodoro.settings_dialog import SettingsDialog
from pomodoro.sounds import SoundManager
from pomodoro.state import MODE_BREAK, MODE_FOCUS, TimerState
from pomodoro.stats import FocusStats
from pomodoro.stats_dialog import StatsDialog


def _other(mode):
    return MODE_BREAK if mode == MODE_FOCUS else MODE_FOCUS


def _resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bingle时钟")
    app.setApplicationDisplayName("Bingle时钟")
    # 应用图标：番茄时钟（打包内置 app_icon_source.png，源码运行读本地文件）
    try:
        app.setWindowIcon(QIcon(_resource("app_icon_source.png")))
    except Exception:
        app.setWindowIcon(icons.clock_icon())

    config = Config()
    sounds = SoundManager(config)
    state = TimerState(config)
    stats = FocusStats(config)

    win = MainWindow(config, state, sounds)
    win.setWindowTitle("Bingle时钟")
    mini = MiniWindow(state)
    popup = PopupWindow(config)
    settings = SettingsDialog(config, sounds, win)

    win.mini_window = mini
    win.popup = popup
    win.settings_dialog = settings

    # 顶栏统计按钮 → 专注统计窗口
    stats_dialog = StatsDialog(stats, win)

    def open_stats():
        stats_dialog.refresh()
        stats_dialog.show()
        stats_dialog.raise_()
        stats_dialog.activateWindow()

    win.request_stats.connect(open_stats)
    win.destroyed.connect(stats_dialog.close)

    # 小窗：双击 / 放大按钮 → 回到主窗口
    def back_to_main():
        mini.hide()
        win.show()
        win.raise_()
        win.activateWindow()

    mini.expand_requested.connect(back_to_main)

    # 弹窗按钮：主=切另一模式并开始；次=切另一模式待开始；三=继续休息；×=当前模式重置回完整时长
    # 任一操作都会停止循环提示音并关闭弹窗（弹窗内部已处理关闭）。
    # 防覆盖：弹窗显示期间若用户已在主界面操作过（mutation_count 变化），
    # 弹窗按钮只停音关闭，不再改动任何状态。
    popup_marker = {"count": 0}

    def on_finished(mode):
        # 专注自然走完才计入统计（跳过/重置不算）
        if mode == MODE_FOCUS:
            stats.record(state.minutes())
        popup_marker["count"] = state.mutation_count

    state.finished.connect(on_finished)

    def guard(fn):
        def wrap(*args):
            if state.mutation_count != popup_marker["count"]:
                sounds.stop()
                return
            fn(*args)
        return wrap

    popup.primary_clicked.connect(guard(lambda mode: (_switch(state, _other(mode)), sounds.stop(), state.start())))
    popup.secondary_clicked.connect(guard(lambda mode: (_switch(state, _other(mode)), sounds.stop())))
    popup.tertiary_clicked.connect(guard(lambda mode: (sounds.stop(), state.start())))
    popup.dismissed.connect(guard(lambda: (state.reset(), sounds.stop())))

    # 主窗口关闭时联动关闭其它窗口
    win.destroyed.connect(mini.close)
    win.destroyed.connect(popup.close)
    win.destroyed.connect(settings.close)

    win._ensure_on_screen()
    win.show()
    sys.exit(app.exec())


def _switch(state, mode):
    state.switch_mode(mode)


if __name__ == "__main__":
    main()
