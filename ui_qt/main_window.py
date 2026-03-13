# -*- coding: utf-8 -*-
"""
AI Novel Generator - 主窗口模块
==================================

本模块实现了应用程序的主窗口，负责：
- 管理各个功能标签页（Tab）的切换与显示
- 处理项目打开/关闭的导航逻辑
- 提供现代化的 UI 界面（基于 PyQt5 和 qfluentwidgets）
- 支持 Mica/Acrylic 等 Windows 特效

主要组件：
- MainWindow: 继承自 FluentWindow 的主窗口类
"""

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, NavigationItemPosition, setThemeColor

from .tabs.home_tab import HomeTab
from .tabs.library_tab import LibraryTab
from .tabs.project_tab import ProjectTab
from .tabs.settings_tab import SettingsTab
from .tabs.writing_tab import WritingTab
from .utils.helpers import set_global_notify
from .utils.notification_manager import NotificationManager
from .utils.styles import ThemeManager
from core import get_logger

logger = get_logger()


class MainWindow(FluentWindow):
    """
    AI Novel Generator 主窗口类

    继承自 qfluentwidgets 的 FluentWindow，提供现代化的 Fluent Design 界面。

    主要功能：
    - 管理图书馆模式和项目模式的切换
    - 导航栏的显示/隐藏控制
    - 项目数据的传递与同步
    """

    def __init__(self):
        """
        初始化主窗口

        创建所有子界面并初始化导航、窗口设置等。
        """
        super().__init__()
        logger.info("main_window", "主窗口初始化开始")

        self.setMicaEffectEnabled(False)

        setThemeColor(ThemeManager.get_color(ThemeManager.Colors.PRIMARY))

        self.current_project = None

        self._notify = NotificationManager(self)
        set_global_notify(self._notify)

        self.libraryTab = LibraryTab(self)
        self.homeTab = HomeTab(self)  # 生成台（主创作界面）
        self.projectTab = ProjectTab(self)  # 项目设定
        self.writingTab = WritingTab(self)  # 写作编辑
        self.settingsTab = SettingsTab(self)  # 统一设置

        # 连接信号：从图书馆选择项目时触发
        self.libraryTab.project_selected.connect(self.open_project)

        # 初始化窗口属性
        self.initWindow()

        # 初始化导航栏
        self.initNavigation()

        # 禁用导航栏的亚克力效果
        self.navigationInterface.setAcrylicEnabled(False)

        # 调整导航栏宽度
        self.navigationInterface.setExpandWidth(240)

    def initWindow(self):
        """
        初始化窗口的基本属性

        设置窗口大小、标题、图标，并将窗口居中显示在屏幕上。
        """
        # 设置窗口尺寸
        self.resize(1200, 800)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setWindowTitle("AI Novel Generator")

        # 设置窗口图标
        import os
        import sys

        icon_path = None
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        icon_path = os.path.join(base_path, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 将窗口居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def initNavigation(self):
        """
        初始化导航栏

        添加所有导航项，并设置初始显示状态为图书馆模式。
        """
        # 1. 图书馆（全局导航，始终可见）
        self.addSubInterface(self.libraryTab, FIF.LIBRARY, "图书馆")

        # 2. 项目相关导航项（默认隐藏，打开项目后显示）
        # 返回图书馆按钮
        self.navigationInterface.addItem(
            routeKey="back_to_library",
            icon=FIF.RETURN,
            text="返回图书馆",
            onClick=self.back_to_library,
            position=NavigationItemPosition.TOP,
        )

        # 添加项目相关标签页
        self.addSubInterface(self.homeTab, FIF.EDIT, "生成台")
        self.addSubInterface(self.projectTab, FIF.FOLDER, "项目设定")
        self.addSubInterface(self.writingTab, FIF.DOCUMENT, "写作编辑")

        # 3. 统一设置（底部）
        self.addSubInterface(
            self.settingsTab,
            FIF.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM,
        )

        # 初始状态：显示图书馆模式，隐藏项目相关导航
        self.set_project_nav_visible(False)

    def set_project_nav_visible(self, visible):
        """
        设置项目相关导航项的可见性

        Args:
            visible: 是否显示项目相关导航项
                     - True: 显示项目导航，隐藏图书馆
                     - False: 显示图书馆，隐藏项目导航
        """
        # 需要切换显示/隐藏的导航项
        project_items = ["back_to_library", "homeTab", "projectTab", "writingTab"]
        library_items = ["libraryTab"]

        # 显示或隐藏项目导航项
        for key in project_items:
            item = self.navigationInterface.widget(key)
            if item:
                item.setHidden(not visible)

        # 显示或隐藏图书馆导航项
        for key in library_items:
            item = self.navigationInterface.widget(key)
            if item:
                item.setHidden(visible)

    def open_project(self, project_data):
        """
        打开一个项目

        Args:
            project_data: 包含项目信息的字典，必须包含 'name', 'path' 等关键字段

        该函数会：
        1. 更新当前项目数据
        2. 将项目数据传递给各子界面
        3. 刷新相关界面内容
        4. 切换到项目模式并显示项目导航
        5. 自动跳转到生成台
        """
        logger.info(
            "main_window",
            f"打开项目: {project_data.get('name', '未知')}, 路径: {project_data.get('path', '未知')}",
        )
        self.current_project = project_data

        self.homeTab.set_project(project_data)

        if hasattr(self.writingTab, "load_chapters"):
            self.writingTab.load_chapters()

        if hasattr(self.projectTab, "directoryTab"):
            self.projectTab.directoryTab.load_directory()
            self.projectTab.characterTab.load_roles()
            self.projectTab.summaryTab.load_summary()
            self.projectTab.architectureTab.load_architecture()

        self.set_project_nav_visible(True)

        self.switchTo(self.homeTab)
        self._notify.success("项目已加载", f"正在编辑: {project_data['name']}")
        logger.debug("main_window", "项目加载完成，已切换到生成台")

    def back_to_library(self):
        """
        返回图书馆

        清除当前项目上下文，切换回图书馆模式，并刷新项目列表。
        """
        logger.info("main_window", "返回图书馆")
        self.current_project = None

        self.set_project_nav_visible(False)

        self.switchTo(self.libraryTab)

        self.libraryTab.load_projects()
        logger.debug("main_window", "已切换到图书馆模式")

    def switchTo(self, interface):
        """
        切换到指定界面（重写以在切换前清理composer组件）

        Args:
            interface: 要切换到的界面
        """
        # 先清理当前显示界面的composer组件
        current_interface = self.stackedWidget.currentWidget()
        if hasattr(current_interface, "cleanup_composer"):
            current_interface.cleanup_composer()

        # 调用父类的switchTo方法
        super().switchTo(interface)
