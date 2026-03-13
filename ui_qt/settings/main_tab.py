# -*- coding: utf-8 -*-
"""
设置主界面
==========

本模块提供了设置的主界面：
- SettingsTab: 统一设置主界面
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ScrollArea, SegmentedWidget, ToolButton

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .sections import (
    AboutSection,
    AppearanceSection,
    ComposerSection,
    DirectorySection,
    LLMSection,
    PromptSection,
    ProxySection,
    WebDAVSection,
)


class SettingsTab(QWidget):
    """
    统一设置主界面

    使用 SegmentedWidget 导航切换不同的设置分区：
    - LLM配置
    - Embedding配置
    - 小说目录
    - 代理设置
    - 外观设置
    - WebDAV备份
    - 关于
    """

    def __init__(self, parent=None):
        """
        初始化设置主界面

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("settingsTab")

        # 主布局 - 使用滚动区域包裹
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setObjectName("settingsScrollArea")
        self.scrollArea.setStyleSheet(
            "QScrollArea#settingsScrollArea { background-color: transparent; border: none; }"
        )
        self.scrollArea.viewport().setStyleSheet("background-color: transparent;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建滚动区域内的内容控件
        self.contentWidget = QWidget()
        self.scrollArea.setWidget(self.contentWidget)

        # 主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.scrollArea)

        # 内容布局
        self.vBoxLayout = QVBoxLayout(self.contentWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 顶部导航栏容器
        self.navContainer = QWidget(self.contentWidget)
        self.navContainer.setObjectName("navContainer")
        self.navLayout = QHBoxLayout(self.navContainer)
        self.navLayout.setContentsMargins(30, 20, 30, 10)

        # 分段导航控件
        self.pivot = SegmentedWidget(self.navContainer)
        self.navLayout.addWidget(self.pivot)

        # 恢复默认按钮
        self.restoreDefaultsBtn = ToolButton(FIF.SYNC, self.navContainer)
        self.restoreDefaultsBtn.setToolTip("恢复所有Prompt为默认值")
        self.restoreDefaultsBtn.hide()  # 初始隐藏
        self.restoreDefaultsBtn.clicked.connect(self._on_restore_defaults)
        self.navLayout.addWidget(self.restoreDefaultsBtn)

        self.navLayout.addStretch()

        # 页面堆栈
        self.stackedWidget = QStackedWidget(self.contentWidget)

        # 添加导航项
        self.pivot.addItem(
            routeKey="llm", text="AI模型库", onClick=lambda: self.switch_to("llm")
        )
        self.pivot.addItem(
            routeKey="composer",
            text="Composer",
            onClick=lambda: self.switch_to("composer"),
        )
        self.pivot.addItem(
            routeKey="directory",
            text="小说目录",
            onClick=lambda: self.switch_to("directory"),
        )
        self.pivot.addItem(
            routeKey="proxy", text="代理设置", onClick=lambda: self.switch_to("proxy")
        )
        self.pivot.addItem(
            routeKey="appearance",
            text="界面",
            onClick=lambda: self.switch_to("appearance"),
        )
        self.pivot.addItem(
            routeKey="webdav", text="WebDAV", onClick=lambda: self.switch_to("webdav")
        )
        self.pivot.addItem(
            routeKey="prompt",
            text="Prompt编辑",
            onClick=lambda: self.switch_to("prompt"),
        )
        self.pivot.addItem(
            routeKey="about", text="关于", onClick=lambda: self.switch_to("about")
        )

        # 创建各设置分区
        self.llmSection = LLMSection(self)
        self.composerSection = ComposerSection(self)
        self.directorySection = DirectorySection(self)
        self.proxySection = ProxySection(self)
        self.appearanceSection = AppearanceSection(self)
        self.webdavSection = WebDAVSection(self)
        self.promptSection = PromptSection(self)
        self.aboutSection = AboutSection(self)

        # 连接PromptSection的信号
        self.promptSection.restore_defaults_changed.connect(
            self._on_restore_state_changed
        )

        # 检查初始状态
        if self.promptSection.is_edited():
            self.restoreDefaultsBtn.show()

        # 将分区添加到堆栈
        self.stackedWidget.addWidget(self.llmSection)
        self.stackedWidget.addWidget(self.composerSection)
        self.stackedWidget.addWidget(self.directorySection)
        self.stackedWidget.addWidget(self.proxySection)
        self.stackedWidget.addWidget(self.appearanceSection)
        self.stackedWidget.addWidget(self.webdavSection)
        self.stackedWidget.addWidget(self.promptSection)
        self.stackedWidget.addWidget(self.aboutSection)

        # 添加到主布局
        self.vBoxLayout.addWidget(self.navContainer)
        self.vBoxLayout.addWidget(self.stackedWidget)

        # 默认显示 LLM 配置页
        self.pivot.setCurrentItem("llm")
        self.stackedWidget.setCurrentIndex(0)
        self.current_key = "llm"

    def switch_to(self, key):
        """
        切换到指定的设置分区

        Args:
            key: 分区的 routeKey
        """
        index = [
            "llm",
            "composer",
            "directory",
            "proxy",
            "appearance",
            "webdav",
            "prompt",
            "about",
        ].index(key)
        self.stackedWidget.setCurrentIndex(index)
        self.pivot.setCurrentItem(key)
        self.current_key = key

        # 只有在prompt页面时显示恢复默认按钮（如果有编辑）
        if key == "prompt" and self.promptSection.is_edited():
            self.restoreDefaultsBtn.show()
        elif key != "prompt":
            self.restoreDefaultsBtn.hide()

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，用于切换设置选项

        智能检测：
        - 检查是否开启了滚轮切换功能
        - 检查鼠标是否在输入控件上，避免误触发

        Args:
            event: 滚轮事件对象
        """
        # 检查配置是否开启了滚轮切换功能
        try:
            import os

            from core.config_manager import load_config

            config_file = os.path.join(os.getcwd(), "config.json")
            config = load_config(config_file)
            if not config.get("enable_wheel_tab_switch", True):
                event.ignore()
                return
        except Exception:
            # 如果加载配置失败，默认允许
            pass

        # 智能检测：检查鼠标是否在输入控件上
        if self._is_focus_on_input_widget():
            event.ignore()
            return

        keys = [
            "llm",
            "composer",
            "directory",
            "proxy",
            "appearance",
            "webdav",
            "prompt",
            "about",
        ]
        current_index = keys.index(self.current_key)

        # 向上滚动：向后切换，向下滚动：向前切换
        if event.angleDelta().y() > 0:
            new_index = (current_index - 1) % len(keys)
        else:
            new_index = (current_index + 1) % len(keys)

        self.switch_to(keys[new_index])

    def _is_focus_on_input_widget(self):
        """
        检查当前焦点是否在输入控件上

        Returns:
            bool: 如果焦点在输入控件上返回 True，否则返回 False
        """
        from PyQt5.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit
        from qfluentwidgets import LineEdit as QFLineEdit
        from qfluentwidgets import TextEdit as QFTextEdit

        focus_widget = QApplication.focusWidget()
        if not focus_widget:
            return False

        # 检查是否是常见的输入控件类型
        input_widget_types = (
            QTextEdit,
            QLineEdit,
            QPlainTextEdit,
            QFLineEdit,
            QFTextEdit,
        )

        # 检查类型名称以覆盖所有可能的输入控件
        widget_class_name = focus_widget.__class__.__name__.lower()
        input_widget_keywords = [
            "lineedit",
            "textedit",
            "plaintextedit",
            "textbrowser",
            "spinbox",
            "doublespinbox",
            "combobox",
        ]

        return isinstance(focus_widget, input_widget_types) or any(
            keyword in widget_class_name for keyword in input_widget_keywords
        )

    def _on_restore_state_changed(self, has_edited):
        """
        恢复默认按钮状态变化的处理

        Args:
            has_edited: 是否有编辑过的prompt
        """
        if has_edited and self.current_key == "prompt":
            self.restoreDefaultsBtn.show()
        else:
            self.restoreDefaultsBtn.hide()

    def _on_restore_defaults(self):
        """
        点击恢复默认按钮的处理
        """
        self.promptSection.restore_defaults()
