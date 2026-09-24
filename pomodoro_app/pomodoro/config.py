# -*- coding: utf-8 -*-
"""配置持久化：时长、铃声、音量等，存于 %APPDATA%/PomodoroTimer/config.json"""
import json
import os

APP_NAME = "PomodoroTimer"

DEFAULTS = {
    "focus_minutes": 25,
    "break_minutes": 5,
    "focus_sound": 1,   # 1-5 对应 5 款提示音
    "break_sound": 3,
    "volume": 80,       # 0-100
    "always_on_top": False,
    "auto_start": False,
    "stats": {},        # 专注统计：{"YYYY-MM-DD": 分钟}
}


def config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    return d


def config_path():
    return os.path.join(config_dir(), "config.json")


class Config:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            # utf-8-sig 兼容带 BOM 的文件（记事本/部分编辑器写入）
            with open(config_path(), "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)
            for k in DEFAULTS:
                if k in loaded:
                    self.data[k] = loaded[k]
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()
