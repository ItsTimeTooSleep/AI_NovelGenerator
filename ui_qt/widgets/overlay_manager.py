# -*- coding: utf-8 -*-
"""
AI Novel Generator - 遮罩层管理器
====================================

本模块实现了通用的遮罩层管理功能，用于：
- 提供半透明遮罩背景
- 管理子窗口的显示与隐藏
- 支持多个子窗口的堆叠

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsOpacityEffect
from ..utils.styles import ThemeManager, isDarkTheme


class OverlayWidget(QWidget):
    """
    遮罩层容器组件

    提供半透明遮罩背景，用于承载子窗口。
    """

    def __init__(self, parent=None):
        """
        初始化遮罩层

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self._child_widgets = []
        self._init_ui()

        if parent:
            parent.installEventFilter(self)

    def _init_ui(self):
        """初始化用户界面"""
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)

        is_dark = isDarkTheme()
        bg_color = "#000000" if is_dark else "#000000"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 0.5);
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.hide()

    def eventFilter(self, obj, event):
        """
        事件过滤器，监听父窗口的大小变化

        Args:
            obj: 事件目标对象
            event: 事件对象

        Returns:
            bool: 是否拦截事件
        """
        if obj == self.parent() and event.type() == QEvent.Resize:
            self._update_geometry()
        return super().eventFilter(obj, event)

    def _update_geometry(self):
        """更新遮罩层大小以匹配父窗口"""
        if self.parent():
            self.setGeometry(self.parent().rect())

    def showEvent(self, event):
        """显示事件，更新大小"""
        self._update_geometry()
        super().showEvent(event)

    def show_widget(self, widget):
        """
        在遮罩层中显示一个子窗口

        Args:
            widget: 要显示的子窗口组件
        """
        if widget not in self._child_widgets:
            self._child_widgets.append(widget)
            self.main_layout.addWidget(widget, 0, Qt.AlignCenter)

        self.show()
        widget.show()
        widget.raise_()

    def hide_widget(self, widget):
        """
        从遮罩层中隐藏一个子窗口

        Args:
            widget: 要隐藏的子窗口组件
        """
        if widget in self._child_widgets:
            widget.hide()
            self._child_widgets.remove(widget)

        if not self._child_widgets:
            self.hide()

    def hide_all(self):
        """隐藏所有子窗口和遮罩层"""
        for widget in self._child_widgets:
            widget.hide()
        self._child_widgets.clear()
        self.hide()

    def is_visible(self):
        """
        检查遮罩层是否可见

        Returns:
            bool: 遮罩层是否可见
        """
        return self.isVisible()

    def mousePressEvent(self, event):
        """
        鼠标点击事件处理

        Args:
            event: 鼠标事件对象
        """
        event.accept()


class OverlayManager:
    """
    遮罩层管理器

    管理遮罩层的创建、显示和隐藏，提供统一的接口。
    """

    _instance = None
    _overlays = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_overlay(cls, parent, key="default"):
        """
        获取或创建一个遮罩层

        Args:
            parent: 父控件
            key: 遮罩层的唯一标识符

        Returns:
            OverlayWidget: 遮罩层实例
        """
        if key not in cls._overlays or cls._overlays[key].parent() != parent:
            overlay = OverlayWidget(parent)

            if hasattr(parent, "layout"):
                layout = parent.layout()
                if layout:
                    overlay.setGeometry(parent.rect())

            cls._overlays[key] = overlay

        return cls._overlays[key]

    @classmethod
    def show_widget(cls, parent, widget, key="default"):
        """
        在遮罩层中显示一个子窗口

        Args:
            parent: 父控件
            widget: 要显示的子窗口组件
            key: 遮罩层的唯一标识符
        """
        overlay = cls.get_overlay(parent, key)
        overlay.show_widget(widget)

        overlay.raise_()
        overlay.stackUnder(widget)

    @classmethod
    def hide_widget(cls, parent, widget, key="default"):
        """
        从遮罩层中隐藏一个子窗口

        Args:
            parent: 父控件
            widget: 要隐藏的子窗口组件
            key: 遮罩层的唯一标识符
        """
        if key in cls._overlays:
            cls._overlays[key].hide_widget(widget)

    @classmethod
    def cleanup(cls):
        """清理所有遮罩层"""
        for key in list(cls._overlays.keys()):
            overlay = cls._overlays.pop(key)
            overlay.hide_all()
            overlay.deleteLater()
