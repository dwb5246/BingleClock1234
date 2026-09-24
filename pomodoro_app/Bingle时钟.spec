# -*- mode: python ; coding: utf-8 -*-
# Bingle时钟 · PyInstaller 瘦身配置
# 原理：PySide6 hook 会把 Qt 全量 DLL（含 194MB 的 WebEngine）一并收集，
# 这里在收集后按白名单过滤，只保留本应用用到的模块。

KEEP_QT_DLL = (
    "Qt6Core.dll",
    "Qt6Gui.dll",
    "Qt6Widgets.dll",
    "Qt6Multimedia.dll",            # QSoundEffect
    "Qt6MultimediaWidgets.dll",     # QtMultimedia hook 会连带收集其 pyd
    "Qt6Network.dll",               # QtMultimedia.pyd 依赖
    "Qt6Svg.dll",                   # QSvgRenderer（内联 SVG 图标）
)

# 插件目录白名单（按二进制相对路径匹配，统一为 posix 分隔符）
KEEP_PLUGIN_DIRS = (
    "plugins/platforms",           # qwindows 必需
    "plugins/imageformats",        # PNG 读取必需
    "plugins/multimedia",          # QSoundEffect 后端
    "plugins/styles",              # qwindowsvistastyle
    "plugins/iconengines",
    "plugins/platforminputcontexts",
    "plugins/generic",
)

# 明确剔除的大块 / 无用文件
DROP_SUBSTR = (
    "opengl32sw.dll",                       # 软件 OpenGL（纯 2D 应用用不到，-7.6MB）
    "plugins/platforms/qdirect2d.dll",      # Direct2D 平台插件（默认 qwindows）
    "plugins/imageformats/qpdf.dll",
    "plugins/imageformats/qicns.dll",
    "plugins/imageformats/qtiff.dll",
    "plugins/imageformats/qtga.dll",
    "plugins/imageformats/qwbmp.dll",
    "plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
)

# 翻译文件：只保留中文与英文
KEEP_TRANSLATIONS = ("qt_zh_CN.qm", "qt_zh_TW.qm", "qt_en.qm")


def _keep_binary(name):
    n = name.replace("\\", "/")
    if "Qt6" in n and "Qt6" in n.split("/")[-1][:4]:
        base = n.split("/")[-1]
        if base.startswith("Qt6") and base.endswith(".dll"):
            return base in KEEP_QT_DLL
        return True
    if "/plugins/" in n:
        return any(d in n for d in KEEP_PLUGIN_DIRS)
    return True


def _keep_data(name):
    n = name.replace("\\", "/")
    if "/translations/" in n:
        return n.split("/")[-1] in KEEP_TRANSLATIONS
    return True


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('app_icon_source.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = [(n, p, s) for (n, p, s) in a.binaries
              if _keep_binary(n) and not any(d in n.replace("\\", "/") for d in DROP_SUBSTR)]
a.datas = [(n, p, s) for (n, p, s) in a.datas if _keep_data(n)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Bingle时钟',
    icon='app.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='Bingle时钟',
)
