# -*- coding: utf-8 -*-
"""专注统计：按天累计专注分钟数，数据存在 config.json 的 stats 字段，轻量无额外文件。"""
from datetime import date, timedelta


class FocusStats:
    def __init__(self, config):
        self.config = config
        self.data = dict(config.get("stats") or {})

    def _save(self):
        self.config.set("stats", self.data)

    def record(self, minutes):
        key = date.today().isoformat()
        self.data[key] = self.data.get(key, 0) + int(minutes)
        self._save()

    def today(self):
        return self.data.get(date.today().isoformat(), 0)

    def total(self):
        return sum(self.data.values())

    def week_total(self):
        today = date.today()
        start = today - timedelta(days=today.weekday())
        return sum(v for k, v in self.data.items()
                   if start.isoformat() <= k <= today.isoformat())

    def recent(self, n=7):
        """最近 n 天，返回 [(日期, 分钟), ...] 按时间正序。"""
        today = date.today()
        out = []
        for i in range(n - 1, -1, -1):
            d = today - timedelta(days=i)
            out.append((d.isoformat(), self.data.get(d.isoformat(), 0)))
        return out
