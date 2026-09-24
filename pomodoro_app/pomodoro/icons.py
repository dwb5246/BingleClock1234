# -*- coding: utf-8 -*-
"""黑白线条图标：从内联 SVG 渲染成 QIcon（QtSvg）。"""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4h6v5l3 3v2H6v-2l3-3z"/><path d="M12 14v6"/></svg>"""

_MINI = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><rect x="13.5" y="12.5" width="6.5" height="5.5" rx="1" fill="{c}" stroke="none"/></svg>"""

_GEAR = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.2"/><path d="M19 12a7 7 0 0 0-.15-1.4l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2.4-1.4L13.5 3h-3l-.55 2.2A7 7 0 0 0 7.55 6.6l-2.4-1-2 3.4 2 1.6A7 7 0 0 0 5 12c0 .48.05.94.15 1.4l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2.4 1.4l.55 2.2h3l.55-2.2a7 7 0 0 0 2.4-1.4l2.4 1 2-3.4-2-1.6c.1-.46.15-.92.15-1.4z"/></svg>"""

_CLOSE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>"""

_PLAY = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{c}"><path d="M8 5v14l11-7z"/></svg>"""

_PAUSE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{c}"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>"""

_RESET = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg>"""

_SKIP = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 3v6h6"/></svg>"""

_CLOCK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>"""

_BELL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>"""

_FULLSCREEN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>"""

_RESTORE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3"/><path d="M16 3v3a2 2 0 0 0 2 2h3"/><path d="M8 21v-3a2 2 0 0 0-2-2H3"/><path d="M16 21v-3a2 2 0 0 1 2-2h3"/></svg>"""

_MINIMIZE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"><path d="M5 12h14"/></svg>"""

_STATS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7" rx="0.6"/><rect x="12" y="6" width="3" height="11" rx="0.6"/><rect x="17" y="13" width="3" height="4" rx="0.6"/></svg>"""


def _render(svg, size=20, color="#1A1B1C", bg=None):
    renderer = QSvgRenderer(QByteArray(svg.format(c=color).encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    if bg is not None:
        pm.fill(bg)
    painter = QPainter(pm)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    return QIcon(pm)


def pin_icon(color="#1A1B1C", bg=None):
    return _render(_PIN, color=color, bg=bg)


def mini_icon(color="#1A1B1C", bg=None):
    return _render(_MINI, color=color, bg=bg)


def gear_icon(color="#1A1B1C", bg=None):
    return _render(_GEAR, color=color, bg=bg)


def close_icon(color="#9CA3AF"):
    return _render(_CLOSE, color=color, size=16)


def play_icon(color="#FFFFFF"):
    return _render(_PLAY, color=color, size=16)


def pause_icon(color="#FFFFFF"):
    return _render(_PAUSE, color=color, size=16)


def reset_icon(color="#1A1B1C", size=16):
    return _render(_RESET, color=color, size=size)


def skip_icon(color="#1A1B1C", size=16):
    return _render(_SKIP, color=color, size=size)


def clock_icon(color="#1A1B1C"):
    return _render(_CLOCK, color=color, size=32)


def bell_icon(color="#9CA3AF", size=14):
    return _render(_BELL, color=color, size=size)


def fullscreen_icon(color="#1A1B1C", size=20):
    return _render(_FULLSCREEN, color=color, size=size)


def restore_icon(color="#1A1B1C", size=20):
    return _render(_RESTORE, color=color, size=size)


def minimize_icon(color="#1A1B1C", size=20):
    return _render(_MINIMIZE, color=color, size=size)


def stats_icon(color="#1A1B1C", size=20):
    return _render(_STATS, color=color, size=size)
