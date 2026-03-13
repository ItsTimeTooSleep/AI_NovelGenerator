# -*- coding: utf-8 -*-
"""
可点击标签组件模块
==================

本模块提供可点击和悬停变色的标签组件。
"""

import webbrowser

from PyQt5.QtCore import Qt
from qfluentwidgets import BodyLabel


class ClickableLabel(BodyLabel):
    """
    支持点击和悬停变色的标签组件

    用于显示可点击的链接，支持悬停变色和点击打开链接功能。
    """

    def __init__(self, text: str, url: str, parent=None):
        """
        初始化可点击标签

        Args:
            text: 标签显示的文本
            url: 点击标签时打开的 URL
            parent: 父控件
        """
        super().__init__(parent)
        self.setText(text)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self._normal_color = "#8B5CF6"
        self._hover_color = "#6D28D9"
        self.setStyleSheet(f"color: {self._normal_color}; font-size: 12px;")
        self.setToolTip("点击打开链接")

    def enterEvent(self, event):
        """
        鼠标进入时改变颜色

        Args:
            event: 鼠标事件对象
        """
        self.setStyleSheet(f"color: {self._hover_color}; font-size: 12px;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        鼠标离开时恢复颜色

        Args:
            event: 鼠标事件对象
        """
        self.setStyleSheet(f"color: {self._normal_color}; font-size: 12px;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """
        鼠标点击时打开链接

        Args:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            webbrowser.open(self.url)
        super().mousePressEvent(event)
