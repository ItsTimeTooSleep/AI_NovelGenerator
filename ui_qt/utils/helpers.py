# -*- coding: utf-8 -*-
"""
AI Novel Generator - UI 辅助工具模块
======================================

本模块提供 Qt 前端通用工具函数，避免在各个界面中重复实现：
- 当前项目路径获取
- 文本文件读取/保存的轻量封装
- 统一的项目界面基类
- 错误通知与复制功能

主要功能：
- get_current_project_path: 从主窗口或配置中获取当前项目路径
- read_text_file: 读取文本文件的简单封装
- write_text_file: 写入文本文件的简单封装
- BaseProjectInterface: 项目设定子界面的统一基类
- show_error_notification: 显示错误通知并支持点击复制功能
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import ScrollArea

from core.config_manager import load_config
from core.utils import read_file as _read_file
from core.utils import save_string_to_txt as _save_string_to_txt

from .notification_manager import NotificationManager, NotificationType
from .styles import Styles

_global_notify: NotificationManager = None


def get_global_notify() -> NotificationManager:
    """
    获取全局通知管理器实例

    Returns:
        NotificationManager: 全局通知管理器
    """
    global _global_notify
    return _global_notify


def set_global_notify(notify: NotificationManager) -> None:
    """
    设置全局通知管理器实例

    Args:
        notify: 通知管理器实例
    """
    global _global_notify
    _global_notify = notify


class AdaptiveStackedWidget(QStackedWidget):
    """
    自适应高度的 StackedWidget

    默认的 QStackedWidget 会采用所有页面中最大的高度作为其高度，
    导致较短的页面也会被拉伸，产生大量空白。
    本控件重写了 sizeHint，使其高度仅取决于当前显示的页面。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 必须设置为 Preferred 或 Minimum，否则无法自适应缩小
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # 当页面切换时，通知布局系统重新计算大小
        self.currentChanged.connect(self.updateGeometry)

    def sizeHint(self):
        current = self.currentWidget()
        if not current:
            return super().sizeHint()
        return current.sizeHint()

    def minimumSizeHint(self):
        current = self.currentWidget()
        if not current:
            return super().minimumSizeHint()
        return current.minimumSizeHint()


class BaseProjectInterface(ScrollArea):
    """
    项目界面基类，提供统一的布局和样式

    Args:
        parent: 父控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.view.setObjectName("projectBaseView")

        self.setStyleSheet(Styles.ScrollArea)
        self.setStyleSheet(
            "BaseProjectInterface { background-color: transparent; border: none; }"
        )
        self.viewport().setStyleSheet("background-color: transparent;")
        self.view.setStyleSheet(
            "QWidget#projectBaseView { background-color: transparent; }"
        )

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(20, 10, 20, 30)
        self.vBoxLayout.setSpacing(20)

        self.config_file = "config.json"
        self.loaded_config = load_config(self.config_file) or {}

    def get_filepath(self):
        """
        获取当前项目路径

        Returns:
            str: 项目路径
        """
        if hasattr(self.window(), "current_project") and self.window().current_project:
            return self.window().current_project.get("path", "").strip()

        other_params = self.loaded_config.get("other_params", {})
        return other_params.get("filepath", "").strip()


def get_current_project_path(widget: QWidget) -> str:
    """
    从主窗口或配置中获取当前项目路径

    Args:
        widget: 任意控件对象，用于获取主窗口

    Returns:
        str: 项目路径字符串，如果未找到则返回空字符串
    """
    if widget is None:
        return ""

    # 首先尝试从主窗口的 current_project 属性获取
    win = widget.window()
    if hasattr(win, "current_project") and getattr(win, "current_project", None):
        return win.current_project.get("path", "").strip() or ""

    # 兼容模式：从全局 config 中读取其它参数
    config = load_config("config.json") or {}
    other_params = config.get("other_params", {})
    return other_params.get("filepath", "").strip() or ""


def read_text_file(path: str) -> str:
    """
    读取文本文件的简单封装，统一编码与异常处理入口

    Args:
        path: 文件路径

    Returns:
        str: 文件内容
    """
    return _read_file(path)


def write_text_file(content: str, path: str) -> None:
    """
    写入文本文件的简单封装

    Args:
        content: 要写入的内容
        path: 文件路径
    """
    _save_string_to_txt(content, path)


def show_error_notification(title: str, message: str, parent: QWidget = None) -> None:
    """
    显示错误通知并支持点击复制功能

    Args:
        title: 错误通知标题
        message: 错误消息内容
        parent: 父控件
    """
    global _global_notify
    full_message = f"{title}: {message}" if title else message

    if _global_notify:
        _global_notify.error(title, message, copyable=True)
    elif parent:
        notify = NotificationManager(parent)
        notify.error(title, message, copyable=True)
    else:
        print(f"[ERROR] {full_message}")


__all__ = [
    "get_current_project_path",
    "read_text_file",
    "write_text_file",
    "BaseProjectInterface",
    "show_error_notification",
    "get_global_notify",
    "set_global_notify",
    "NotificationManager",
    "NotificationType",
]
