# -*- coding: utf-8 -*-
"""设置面板：专注/休息提示音选择 + 试听、音量、开机自启。改动即时生效。"""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton,
    QSlider, QVBoxLayout, QWidget,
)

from .sounds import SOUNDS
from .widgets import FramelessDialog

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Microsoft YaHei, sans-serif"

DIALOG_STYLE = """
QDialog {{
    background: #FFFFFF; font-family: {font};
}}
QLabel {{ color: #1A1B1C; font-size: 12px; }}
QLabel.muted {{ color: #6B7280; }}
QPushButton {{
    border: 1px solid #E5E7EB; border-radius: 8px; padding: 4px 12px;
    font-size: 12px; color: #6B7280; background: #FFFFFF;
}}
QPushButton:hover {{ background: #F9FAFB; }}
QComboBox {{
    border: 1px solid #E5E7EB; border-radius: 6px; padding: 3px 8px;
    font-size: 12px; color: #1A1B1C; background: #FFFFFF;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QSlider::groove:horizontal {{
    height: 4px; background: #E5E7EB; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; background: #1A1B1C;
}}
QCheckBox {{ font-size: 12px; color: #6B7280; }}
"""

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def set_auto_start(enabled):
    """写入/删除 HKCU Run 键，实现开机自启。"""
    try:
        import winreg
    except ImportError:
        return
    exe = sys.executable
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, "PomodoroTimer", 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, "PomodoroTimer")
                except FileNotFoundError:
                    pass
    except OSError:
        pass


class SettingsDialog(FramelessDialog):
    def __init__(self, config, sounds, parent=None):
        super().__init__("设置", parent)
        self.config = config
        self.sounds = sounds
        self.setWindowTitle("设置")
        self.setFixedSize(320, 292)
        self.setStyleSheet(DIALOG_STYLE.format(font=FONT_FAMILY))
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        root = self.layout

        # 专注完成提示音
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lbl1 = QLabel("专注完成提示音", self)
        lbl1.setProperty("class", "muted")
        self.focus_combo = QComboBox(self)
        self._fill_combo(self.focus_combo)
        btn1 = QPushButton("试听", self)
        btn1.clicked.connect(lambda: self.sounds.play(self.focus_combo.currentData()))
        row1.addWidget(lbl1)
        row1.addWidget(self.focus_combo, 1)
        row1.addWidget(btn1)
        root.addLayout(row1)

        # 休息完成提示音
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl2 = QLabel("休息完成提示音", self)
        lbl2.setProperty("class", "muted")
        self.break_combo = QComboBox(self)
        self._fill_combo(self.break_combo)
        btn2 = QPushButton("试听", self)
        btn2.clicked.connect(lambda: self.sounds.play(self.break_combo.currentData()))
        row2.addWidget(lbl2)
        row2.addWidget(self.break_combo, 1)
        row2.addWidget(btn2)
        root.addLayout(row2)

        # 音量
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        lbl3 = QLabel("音量", self)
        lbl3.setProperty("class", "muted")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_value = QLabel("80", self)
        self.volume_value.setFixedWidth(28)
        self.volume_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row3.addWidget(lbl3)
        row3.addWidget(self.volume_slider, 1)
        row3.addWidget(self.volume_value)
        root.addLayout(row3)

        # 开机自启
        row4 = QHBoxLayout()
        self.auto_start_check = QCheckBox("开机自启", self)
        row4.addWidget(self.auto_start_check)
        row4.addStretch(1)
        root.addLayout(row4)

        root.addStretch(1)

        # 连接
        self.focus_combo.currentIndexChanged.connect(self._on_focus_sound_changed)
        self.break_combo.currentIndexChanged.connect(self._on_break_sound_changed)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.auto_start_check.toggled.connect(self._on_auto_start_toggled)

    def _fill_combo(self, combo):
        for idx, (fname, name) in SOUNDS.items():
            combo.addItem(f"{idx} {name}", idx)

    def _load_values(self):
        # blockSignals：加载初值时不触发保存逻辑，避免无谓写盘/覆盖用户配置
        self.focus_combo.blockSignals(True)
        self.break_combo.blockSignals(True)
        self.volume_slider.blockSignals(True)
        self.auto_start_check.blockSignals(True)
        try:
            idx = self.config.get("focus_sound")
            self.focus_combo.setCurrentIndex(self.focus_combo.findData(idx))
            idx = self.config.get("break_sound")
            self.break_combo.setCurrentIndex(self.break_combo.findData(idx))
            v = self.config.get("volume")
            self.volume_slider.setValue(v)
            self.volume_value.setText(str(v))
            self.auto_start_check.setChecked(bool(self.config.get("auto_start")))
        finally:
            self.focus_combo.blockSignals(False)
            self.break_combo.blockSignals(False)
            self.volume_slider.blockSignals(False)
            self.auto_start_check.blockSignals(False)

    def _on_focus_sound_changed(self, _):
        self.config.set("focus_sound", self.focus_combo.currentData())

    def _on_break_sound_changed(self, _):
        self.config.set("break_sound", self.break_combo.currentData())

    def _on_volume_changed(self, v):
        self.volume_value.setText(str(v))
        self.sounds.set_volume(v)

    def _on_auto_start_toggled(self, on):
        self.config.set("auto_start", on)
        set_auto_start(on)
