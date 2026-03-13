# -*- coding: utf-8 -*-
"""
设置模块基类
==========

本模块提供了设置分区的基础类：
- BaseSettingsSection: 设置分区基类
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from core.config_manager import load_config, save_config
from ui_qt.utils.helpers import get_global_notify
from ui_qt.utils.notification_manager import NotificationManager


class BaseSettingsSection(ScrollArea):
    """
    设置分区基类

    提供设置分区的通用功能：
    - 加载/保存配置文件
    - 显示信息/错误提示
    - 统一的样式设置
    """

    def __init__(self, parent=None):
        """
        初始化设置分区基类

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.view = QWidget(self)
        self.view.setObjectName("settingsView")

        # 设置透明背景样式
        self.setStyleSheet(
            "BaseSettingsSection { background-color: transparent; border: none; }"
        )
        self.viewport().setStyleSheet("background-color: transparent;")
        self.view.setStyleSheet(
            "QWidget#settingsView { background-color: transparent; }"
        )

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)

        # 配置文件路径
        self.config_file = "config.json"
        # 加载配置
        self.loaded_config = load_config(self.config_file) or {}

    def show_info(self, title, content):
        """
        显示成功提示信息

        Args:
            title: 提示标题
            content: 提示内容
        """
        notify = get_global_notify()
        if notify:
            notify.success(title, content)

    def show_error(self, title, content):
        """
        显示错误提示信息

        Args:
            title: 错误标题
            content: 错误内容
        """
        notify = get_global_notify()
        if notify:
            notify.error(title, content)

    def show_warning(self, title, content):
        """
        显示警告提示信息

        Args:
            title: 警告标题
            content: 警告内容
        """
        notify = get_global_notify()
        if notify:
            notify.warning(title, content)

    def save_config_to_file(self):
        """
        将配置保存到文件

        Returns:
            bool: 保存是否成功
        """
        try:
            save_config(self.loaded_config, self.config_file)
            return True
        except Exception as e:
            self.show_error("保存失败", str(e))
            return False
