# -*- coding: utf-8 -*-
"""提示音管理：5 款内嵌音效（Mixkit 免费商用授权）。"""
import os
import sys

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

SOUNDS = {
    1: ("01-happy-bells.mp3", "清脆双铃"),
    2: ("02-bell-notification.mp3", "经典单铃"),
    3: ("03-flute-melody.mp3", "柔和长笛"),
    4: ("04-flute-uplifting.mp3", "轻快笛声"),
    5: ("05-magic-ring.mp3", "魔法铃"),
}


def resource_path(rel):
    """开发环境返回源码目录路径；打包后返回 PyInstaller 解压目录。"""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def audio_files():
    """返回 [(index, filename, name), ...]"""
    return [(i, fn, nm) for i, (fn, nm) in SOUNDS.items()]


class SoundManager(QObject):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._output.setVolume(max(0, min(100, config.get("volume"))) / 100.0)

    def play(self, sound_index, loops=4):
        """播放提示音；loops 为循环次数（3 秒音 ×4 ≈ 12 秒，保证可闻）。"""
        try:
            fname = SOUNDS[int(sound_index)][0]
        except (KeyError, ValueError, TypeError):
            fname = SOUNDS[1][0]
        path = resource_path(os.path.join("assets", "audio", fname))
        self._player.setSource(QUrl.fromLocalFile(path))
        try:
            self._player.setLoops(max(1, int(loops)))
        except (AttributeError, TypeError):
            pass
        self._player.play()

    def play_focus(self):
        self.play(self.config.get("focus_sound"))

    def play_break(self):
        self.play(self.config.get("break_sound"))

    def stop(self):
        try:
            self._player.stop()
        except RuntimeError:
            pass

    def set_volume(self, v):
        v = max(0, min(100, int(v)))
        self._output.setVolume(v / 100.0)
        self.config.set("volume", v)
