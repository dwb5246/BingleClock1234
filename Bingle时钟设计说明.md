# Bingle 时钟・设计说明

> 版本：1.0 ｜ 适用产物：
>
> `pomodoro_app/dist/Bingle时钟.exe`
> 本文档面向后续维护与二次开发，覆盖软件架构、关键设计决策、注意事项与优化建议。



***

## 一、项目概览



| 项   | 内容                                                                  |
| --- | ------------------------------------------------------------------- |
| 产品  | Bingle 时钟 —— Windows 桌面极简番茄钟（目录版 exe）                               |
| 技术栈 | Python 3.14 + PySide6 6.11 + PyInstaller 6.22（--onedir --windowed，单文件版配置见 `Bingle时钟_onefile.spec.bak`） |
| 产物  | `dist/Bingle时钟/Bingle时钟.exe`（目录版约 87 MB，启动约 1 秒，离线运行，免装 Python）                              |
| 数据  | `%APPDATA%\PomodoroTimer\config.json`（utf-8-sig 兼容）                 |
| 音频  | 5 款 Mixkit 免费商用提示音，内嵌于 exe（assets\audio）                            |

### 核心产品规则（反复打磨后定稿）



1. **专注 / 休息双页签，用户可随时自由切换**，不受固定流程限制；

2. **倒计时结束绝不自动开始下一阶段**：只弹窗提醒 + 循环提示音，等用户手动决定；

3. **休息也必须手动点开始**：切到休息页签后停在待开始状态；

4. **跳过 / 重置任何状态可点**；

5. 时长就地调整：点击数字直接输入（聚焦即全选覆盖）；＋/－ 在基础上 ±5，**倒计时中 / 已暂停时按当前剩余时间 ±5，不打断、不重置倒计时**；**输入分钟数后按回车直接开始倒计时**；

6. 极简黑白界面，界面零提示文字；应用名「Bingle 时钟」只在任务栏显示，界面顶部不显示。

7. **弹窗防覆盖**：弹窗显示期间若用户已在主界面手动操作（状态机 `mutation_count` 变化），
   再点弹窗任何按钮只停音关窗，不改动任何状态。



***

## 二、软件架构

### 2.1 模块划分（pomodoro\_app/pomodoro/）



```
main.py                 入口：QApplication、单窗口装配、应用显示名

pomodoro/

├── config.py            配置读写（%APPDATA%\PomodoroTimer\config.json）

├── state.py             计时状态机（核心逻辑，无 UI 依赖）

├── sounds.py            提示音管理与循环播放

├── icons.py             内联 SVG → QIcon（黑白线条图标统一出口）

├── widgets.py           TimerRing 自绘圆环进度控件

├── main\_window.py       主窗口（无边框圆角、页签、环、操作区、顶栏）

├── mini\_window.py       置顶小窗（拖拽 / 缩放 / 双击展开）

├── popup.py             时间到弹窗（右下角、循环音、点任意键关闭）

└── settings\_dialog.py   设置面板（铃声 / 音量 / 开机自启）
```

### 2.2 计时状态机（state.py）



* **两个正交维度：**&#x6A21;式 `MODE_FOCUS / MODE_BREAK` × 状态 `STATE_IDLE / STATE_RUNNING / STATE_PAUSED`。

* **计时准确性**：不使用 `QTimer` 累加（会漂移），而是

  `deadline = time.monotonic() + remaining`，`QTimer(500ms)` 只负责刷新 UI 显示；

  暂停时记录 `remaining`，恢复时重设 `deadline`。

* **状态迁移**：


  * 专注倒计时结束 → `finished` 信号 → 切到休息页签（待开始），弹窗；

  * 休息倒计时结束 → 切到专注页签（待开始），弹窗；

  * 跳过 → 切到另一模式（待开始）；

  * 页签点击 → 直接切换模式（未运行时清空运行态）。

* 状态变更通过 Qt Signal（`tick / mode_changed / state_changed / finished`）广播，

  UI 层全部订阅刷新，逻辑与界面解耦。

* **用户操作版本号 `mutation_count`**：每次用户主动操作（改时长 / ± / 切模式 / 开始 / 暂停 / 恢复 / 重置）自增；
  弹窗弹出时记录快照，弹窗按钮回调前比对——不一致说明用户已手动接管，只停音关窗，不覆盖状态。

### 2.3 窗口体系



| 窗口             | 要点                                                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------------------------- |
| MainWindow 主窗  | 无边框（FramelessWindowHint + 圆角 18px + 淡边框 #E1E3E7）、默认 760×760 正方形、min 480×480、WA\_TranslucentBackground、空白处拖动、右下角缩放、全屏切换；顶栏：左[设置]，右[缩小][置顶][全屏][最小化][关闭] |
| MiniWindow 小窗  | 240×190（可缩放 180×140\~420×320）、置顶、模式名严格居中、时间大号（side×0.24）+ 环进度 + 淡色开始按钮（专注淡蓝 / 休息淡绿）+ 重置 / 开始 / 跳过（32px），右上角放大按钮与双击均可展开回主窗 |
| PopupWindow 弹窗 | 340×168（内容自适应）、右下角定位（距边缘 24px）、循环提示音（≥10s）、**点任意按钮即停声关窗**；专注结束=开始休息/稍后，休息结束=再休息一会/继续专注/稍后；按钮圆角 6px 等大；**防覆盖**：弹窗期间若用户已在主界面操作，按钮只停声关窗不改状态 |

主窗布局用 **2:3:2 弹性比例**（左右各 20%、中间 60%）控制环的大小：

环占窗口宽 60%，随窗口缩放等比自适应；＋/－ 按钮为手动定位（`_place_step_btns`），

始终贴环右缘 40px、垂直居中于环。

### 2.4 配置与持久化



* 配置项：专注时长 / 休息时长 / 专注提示音 / 休息提示音 / 音量 / 置顶 / 开机自启。

* 写入 `%APPDATA%\PomodoroTimer\config.json`，删除即恢复默认

  （专注 25 / 休息 5 / 音量 80 / 不置顶）。

* 开机自启通过 Windows 注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 写入。

### 2.5 音频



* `QMediaPlayer + QAudioOutput` 播放内嵌 mp3（FFmpeg 解码）；结束提醒循环 4 次（约 10 秒以上），

  确保用户即使离开也能听到；音量独立于系统（0-100）。

* 5 款铃声均为 Mixkit 免费商用授权（Happy Bells / Bell Notification / Flute Melody / Flute Uplifting / Magic Ring）。

### 2.6 数据与日志管理

**数据（配置）**

* 存放：`%APPDATA%\PomodoroTimer\config.json`（单文件 JSON，`ensure_ascii=False, indent=2`）。
* `Config` 类：`load()` 读取（`utf-8-sig` 兼容 BOM）、`set()` 修改单条并**立即写盘**（无批量事务）。
* 无数据库、无缓存层；删除配置文件即恢复默认（专注 25 / 休息 5 / 音量 80 / 不置顶）。
* 音频资源随 exe 内嵌（`assets/audio`），运行时从 `sys._MEIPASS` 解压目录读取。
* 开机自启写注册表 `HKCU\...\Run`（设置面板开关控制）。

**日志（现状与建议）**

* 现状：**当前没有日志系统**。早期调试用的 `debuglog.py` 已在上轮瘦身中移除；
  程序异常时靠 PyInstaller 的 traceback 弹窗提示，不落盘任何日志。
* 建议：如需留痕，用标准库 `logging` + `RotatingFileHandler`
  写 `%APPDATA%\PomodoroTimer\logs\app.log`（按大小滚动、保留最近 N 份），
  并在 `main()` 里挂 `sys.excepthook` 兜底记录未捕获异常（见"优化建议-崩溃兜底"）。



***

## 三、关键设计决策与注意事项（踩坑记录）

> 以下均为本项目实际遇到并修复过的问题，改动布局 / 窗口行为时务必留意。



1. **置顶切换会隐式隐藏窗口**：`setWindowFlag(Qt.WindowStaysOnTopHint)` 会让窗口重绘 / 隐藏，

   在 toggle 回调里直接 `show()` 会被后续事件吞掉。修复：`QTimer.singleShot(0, self.show)` 延后显示。

2. **控件默认不拉伸**：`TimerRing` 若只设 `setMinimumSize` 而不设

   `setSizePolicy(Expanding, Expanding)`，且网格里用了 `AlignCenter`，环将**永远卡在最小尺寸**，

   任何 "放大环" 的布局调整都不会生效。修复：Expanding 策略 + 网格内不加对齐。

3. **resizeEvent 里改控件尺寸会引发布局重入**：曾在 `resizeEvent` 中

   `setMaximumSize` 控制环大小，导致整个布局顶部 / 底部莫名多出 29px 空隙、环偏移。

   修复：改用 2:3:2 stretch 比例布局让尺寸天然受控，不在 resize 中动态改尺寸。

4. **手动定位控件必须等布局完成**：`move()` 依赖兄弟控件的最终几何，

   需先 `self.layout().activate()` 再取 `geometry()`，否则拿到旧值（± 按钮曾叠到环上）。

5. **配置编码**：配置文件统一用 `utf-8-sig` 读写，兼容带 BOM 的历史文件；

   加载配置时对触发信号的控件要 `blockSignals`，避免初值回写。

6. **测试必须隔离 APPDATA**：GUI 测试脚本需先

   `os.environ["APPDATA"] = tempfile.mkdtemp()`，否则会污染真实用户配置。

7. **离屏（offscreen）平台无字体**：预览图文字会变空白，界面验证必须在真实平台用

   `widget.grab()`（或真窗口截图）。

8. **PyInstaller 打包前必须清理残留进程**：`Bingle时钟` 或旧名进程占用 exe 时

   打包报 PermissionError；onefile 产物启动的子进程 PID 与主进程不同，

   验证窗口需用 `ctypes.EnumWindows` 全枚举按标题匹配。



***

## 四、优化建议（未实施）



| 优先级 | 建议       | 说明                                                                |
| --- | -------- | ----------------------------------------------------------------- |
| 高   | 单实例锁     | 当前可开多个实例，建议用命名互斥体保证单实例，托盘化更好                                      |
| 高   | 系统托盘     | 关闭按钮改为最小化到托盘，减少误退；提供托盘右键菜单                                        |
| 中   | exe 体积瘦身 | 已通过 `Bingle时钟.spec` 白名单过滤降至约 37 MB（剔除 WebEngine/opengl32sw/无用插件）；如需再减可尝试 UPX 二次压缩 |
| 中   | 高分屏适配    | 建议补充 `Qt.AA_EnableHighDpiScaling` 与 Per-Monitor DPI 测试（当前主窗为逻辑像素） |
| 中   | 主题扩展     | 当前专注黑白 / 休息绿色点缀；可预留主题配置便于后续换色                                     |
| 低   | 铃声替换     | 提示音集中在 `assets/audio`，可扩展用户自选铃声目录                                 |
| 低   | 崩溃兜底     | 加全局异常钩子写日志，便于远程排查（当前 debuglog 已移除）                                |



***

## 五、构建与验证



```
\# 打包（在 pomodoro\_app 目录，使用瘦身 spec，当前为 onedir 目录版）

python -m PyInstaller --noconfirm "Bingle时钟.spec"

\# 产物

pomodoro\_app\dist\Bingle时钟\Bingle时钟.exe（目录版，约 87 MB）
```

> PyInstaller 进程退出码为 1 属正常现象，以
>
> `dist\Bingle时钟\Bingle时钟.exe`
>
> 的时间戳与真机启动为准。
>
> **体积与启动对比**：PySide6 官方 hook 会把 Qt 全家桶（含 194MB 的 WebEngine、FFmpeg、软件 OpenGL）一并打包，
> 未瘦身时约 55 MB。`Bingle时钟.spec` 通过白名单过滤只保留
> QtCore/Gui/Widgets/Multimedia/Network/Svg 六个库与必要插件、翻译，
> 剔除 opengl32sw 与无用图片格式插件。
> 两种交付形式（`Bingle时钟_onefile.spec.bak` 保留单文件配置，可一键重建）：
> - **目录版 onedir（当前正式版）**：约 87 MB，免解压，实测启动约 **1 秒**（冷 2.6s / 热 0.9s）；
> - 单文件版 onefile：约 37 MB，每次启动自解压 + 杀毒扫描，实测 **5-7 秒**。
> 注意：**FFmpeg（av\*.dll）不可删**——QMediaPlayer 播放 mp3 依赖它解码；
> QtNetwork/QtMultimediaWidgets 的 DLL 必须保留——PySide6 hook 会连带收集对应 pyd，删了启动即崩。

### 目录结构（瘦身后）



```
new-chat/

├── pomodoro\_app/                  # 工程（源码 + 打包产物）

│   ├── main.py                    # 入口

│   ├── pomodoro/                  # 源码模块（10 个文件）

│   ├── assets/audio/              # 内嵌提示音

│   ├── dist/Bingle时钟/           # 交付物（目录版：exe + _internal）

│   ├── Bingle时钟.spec            # PyInstaller 配置（当前 onedir）

│   └── Bingle时钟_onefile.spec.bak # 单文件版配置备份

├── pomodoro\_assets/               # 提示音原始文件（备份）

├── pomodoro\_app - 副本/           # 用户备份（勿动）

├── Bingle时钟使用说明.md           # 用户操作手册

└── Bingle时钟设计说明.md           # 本文档
```