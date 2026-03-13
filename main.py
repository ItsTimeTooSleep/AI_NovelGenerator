# -*- coding: utf-8 -*-
"""
AI小说生成器 - Qt图形界面主入口模块

================================================================================
模块功能概述
================================================================================
本模块是AI小说生成器应用程序的主入口点，负责初始化PyQt5应用程序环境、
配置主题设置、显示启动画面，并加载主窗口。

================================================================================
核心流程
================================================================================
1. 配置高DPI支持，确保在现代高分辨率显示器上界面清晰
2. 加载配置文件并根据用户设置初始化主题（亮色/暗色/自动）
3. 创建并显示启动画面（Splash Screen）
4. 安装Fluent翻译器以支持国际化
5. 创建并显示主窗口

================================================================================
设计决策
================================================================================
- 使用PyQt5 + qfluentwidgets构建现代化UI界面
- 采用启动画面提升用户体验，避免启动时的空白等待
- 支持高DPI缩放，确保在不同显示器上显示效果一致
- 主题配置从config.json读取，实现用户偏好持久化

================================================================================
依赖模块
================================================================================
- PyQt5: Qt框架的Python绑定，提供GUI功能
- qfluentwidgets: Fluent Design风格的Qt控件库
- core.config_manager: 配置文件管理模块
- ui_qt.main_window: 主窗口模块
- ui_qt.utils.splash_screen: 启动画面模块

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator, Theme, setTheme

from core import LogLevel, get_logger


from core.config_manager import load_config
from ui_qt.main_window import MainWindow
from ui_qt.utils.splash_screen import create_splash_screen


def setup_windows_taskbar_icon():
    """
    配置Windows任务栏图标。

    在Windows系统上，需要设置AppUserModelID才能正确显示任务栏图标。
    该函数使用ctypes调用Windows API来设置应用程序标识。

    参数:
        无

    返回值:
        无

    设计说明:
        - 仅在Windows系统上执行
        - 使用ctypes调用shell32.dll的SetCurrentProcessExplicitAppUserModelID
        - AppUserModelID格式为"公司名.产品名"
    """
    if sys.platform == "win32":
        import ctypes

        try:
            my_app_id = "ItsTimeTooSleep.AI_Novel_Generator.1.0.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
        except Exception as e:
            print(f"Failed to set AppUserModelID: {e}")


def main():
    """
    应用程序主入口函数。

    该函数负责完成应用程序的完整初始化流程，包括：
    1. 配置高DPI支持
    2. 初始化日志系统
    3. 设置应用程序主题
    4. 创建Qt应用程序实例
    5. 显示启动画面
    6. 加载主窗口

    参数:
        无

    返回值:
        无（函数执行完毕后调用sys.exit()退出程序）

    异常:
        可能抛出以下异常：
        - FileNotFoundError: 配置文件不存在时
        - ImportError: 必要的依赖模块缺失时
        - RuntimeError: Qt应用程序初始化失败时

    使用示例:
        >>> if __name__ == "__main__":
        ...     main()

    设计说明:
        - 高DPI配置必须在QApplication创建之前设置
        - 日志系统应在其他模块初始化之前启动
        - 主题设置应在主窗口创建前完成，确保所有控件样式一致
        - 启动画面提供视觉反馈，改善用户等待体验
    """
    setup_windows_taskbar_icon()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    config = load_config("config.json")
    developer_mode = config.get("developer_mode", False)

    logger = get_logger()
    log_level = LogLevel.DEBUG if developer_mode else LogLevel.INFO
    logger.initialize(log_file="app.log", level=log_level, max_records=1000)
    logger.info(
        "main", f"应用程序启动 (开发者模式: {'启用' if developer_mode else '禁用'})"
    )

    theme_mode = config.get("theme", "Light")

    app = QApplication(sys.argv)

    # 主题设置必须在QApplication创建之后执行
    if theme_mode == "Dark":
        setTheme(Theme.DARK)
    elif theme_mode == "Light":
        setTheme(Theme.LIGHT)
    elif theme_mode == "Auto":
        setTheme(Theme.AUTO)
    else:
        setTheme(Theme.LIGHT)

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    translator = FluentTranslator()
    app.installTranslator(translator)

    window = MainWindow()

    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()
    splash.finish(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
