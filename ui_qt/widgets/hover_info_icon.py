# -*- coding: utf-8 -*-
"""
悬停提示组件模块

================================================================================
模块功能概述
================================================================================
本模块提供可悬停显示详细提示信息的组件。
支持富文本显示和内容滚动功能。

================================================================================
主要组件
================================================================================
- HoverInfoIcon: 悬停显示提示信息的图标组件
- ScrollableTooltipWidget: 可滚动的提示框组件

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from PyQt5.QtCore import (
    QEvent,
    QPoint,
    Qt,
    QTimer,
)
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import isDarkTheme

from ui_qt.utils.styles import Styles, ThemeManager


class ScrollableTooltipWidget(QFrame):
    """
    可滚动的提示框组件

    显示富文本内容，支持垂直滚动，可通过鼠标拖拽滚动。
    """

    def __init__(self, content: str = "", parent=None, owner=None):
        """
        初始化可滚动提示框

        Args:
            content: HTML格式的提示内容
            parent: 父控件
            owner: 拥有此提示框的控件（用于检测鼠标是否在提示框或拥有者上）
        """
        super().__init__(parent)
        self._content = content
        self._is_pressed = False
        self._last_pos = None
        self._owner = owner
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_tertiary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )

        self.setStyleSheet(f"""
            ScrollableTooltipWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {Styles.ScrollBar}
        """)

        self.content_widget = QTextEdit()
        self.content_widget.setReadOnly(True)
        self.content_widget.setHtml(self._content)
        self.content_widget.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                padding: 4px;
                color: {text_tertiary};
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        self.content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_widget.textChanged.connect(self._adjust_height)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        self.setFixedWidth(400)
        self.setMinimumHeight(100)
        self.setMaximumHeight(280)

        self._adjust_height()

    def showEvent(self, event):
        """显示事件，确保高度正确"""
        super().showEvent(event)
        # 延迟调整高度，确保文档已完全渲染
        QTimer.singleShot(10, self._adjust_height)
        QTimer.singleShot(50, self._adjust_height)

    def _adjust_height(self):
        """根据内容调整高度"""
        # 强制文档重新计算布局
        doc = self.content_widget.document()
        doc.setTextWidth(self.width() - 24)  # 减去左右padding

        doc_height = doc.size().height()
        # 文本区域的margins
        text_margins = self.content_widget.contentsMargins()
        # 主布局的margins
        layout_margins = self.contentsMargins()

        # 计算总高度：文档高度 + 文本margins + 布局margins
        total_height = int(
            doc_height
            + text_margins.top()
            + text_margins.bottom()
            + layout_margins.top()
            + layout_margins.bottom()
            + 4  # 额外的小边距
        )

        # 限制高度范围
        clamped_height = max(80, min(total_height, 300))

        # 设置滚动区域高度（不设置固定高度，让它自适应）
        self.scroll_area.setMinimumHeight(min(clamped_height - 28, 250))
        self.scroll_area.setMaximumHeight(min(clamped_height - 28, 250))

        # 设置整个提示框的高度
        self.setFixedHeight(clamped_height)

    def setContent(self, content: str):
        """
        设置提示框内容

        Args:
            content: HTML格式的提示内容
        """
        self._content = content
        self.content_widget.setHtml(content)
        self._adjust_height()

    def mousePressEvent(self, event):
        """
        鼠标按下事件，记录起始位置用于拖拽滚动

        Args:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self._last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件，实现拖拽滚动

        Args:
            event: 鼠标事件对象
        """
        if self._is_pressed and self._last_pos:
            delta = self._last_pos.y() - event.pos().y()
            scrollbar = self.content_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.value() + delta)
            self._last_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件，结束拖拽滚动

        Args:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self._is_pressed = False
            self._last_pos = None
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)


class HoverInfoIcon(QWidget):
    """
    悬停显示提示信息的图标组件

    鼠标悬停时显示一个可滚动的提示框，支持富文本内容。
    支持鼠标移动到提示框上而不隐藏。
    """

    def __init__(
        self,
        content: str = "",
        icon_size: int = 16,
        parent=None,
    ):
        """
        初始化悬停提示图标

        Args:
            content: HTML格式的提示内容
            icon_size: 图标大小
            parent: 父控件
        """
        super().__init__(parent)
        self._content = content
        self._icon_size = icon_size
        self._tooltip_widget = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._delayed_hide)
        self._is_hovering_icon = False
        self._is_hovering_tooltip = False
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(self._icon_size, self._icon_size)
        self.icon_label.setText("?")
        self.icon_label.setAlignment(Qt.AlignCenter)

        is_dark = isDarkTheme()
        text_tertiary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)

        self._normal_style = f"""
            QLabel {{
                background-color: transparent;
                color: {text_tertiary};
                font-size: 12px;
                font-weight: bold;
                border: 1px solid {text_tertiary};
                border-radius: {self._icon_size // 2}px;
            }}
        """
        self._hover_style = f"""
            QLabel {{
                background-color: {primary_color};
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid {primary_color};
                border-radius: {self._icon_size // 2}px;
            }}
        """

        self.icon_label.setStyleSheet(self._normal_style)
        self.icon_label.setCursor(Qt.WhatsThisCursor)

        layout.addWidget(self.icon_label)
        self.setFixedSize(self._icon_size + 4, self._icon_size + 4)

    def setContent(self, content: str):
        """
        设置提示内容

        Args:
            content: HTML格式的提示内容
        """
        self._content = content

    def enterEvent(self, event):
        """
        鼠标进入事件，显示提示框

        Args:
            event: 事件对象
        """
        self._is_hovering_icon = True
        self._hide_timer.stop()
        self.icon_label.setStyleSheet(self._hover_style)
        self._show_tooltip()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        鼠标离开事件，延迟隐藏提示框

        Args:
            event: 事件对象
        """
        self._is_hovering_icon = False
        self.icon_label.setStyleSheet(self._normal_style)
        self._hide_timer.start(100)
        super().leaveEvent(event)

    def _is_mouse_over_tooltip(self) -> bool:
        """
        检查鼠标是否在提示框上

        Returns:
            bool: 鼠标是否在提示框上
        """
        if self._tooltip_widget is None or not self._tooltip_widget.isVisible():
            return False

        global_pos = QCursor.pos()
        tooltip_rect = self._tooltip_widget.rect()
        tooltip_top_left = self._tooltip_widget.mapToGlobal(tooltip_rect.topLeft())
        tooltip_bottom_right = self._tooltip_widget.mapToGlobal(
            tooltip_rect.bottomRight()
        )

        return (
            tooltip_top_left.x() <= global_pos.x() <= tooltip_bottom_right.x()
            and tooltip_top_left.y() <= global_pos.y() <= tooltip_bottom_right.y()
        )

    def _delayed_hide(self):
        """延迟隐藏提示框，检查鼠标是否仍在提示框上"""
        if not self._is_hovering_icon and not self._is_mouse_over_tooltip():
            self._hide_tooltip()

    def _show_tooltip(self):
        """显示提示框"""
        if not self._content:
            return

        if self._tooltip_widget is None:
            self._tooltip_widget = ScrollableTooltipWidget(self._content, owner=self)
            self._tooltip_widget.setParent(None)
            self._tooltip_widget.installEventFilter(self)

        self._tooltip_widget.setContent(self._content)

        global_pos = self.mapToGlobal(QPoint(0, self.height() + 8))
        self._tooltip_widget.move(global_pos)
        self._tooltip_widget.show()

    def _hide_tooltip(self):
        """隐藏提示框"""
        if self._tooltip_widget:
            self._tooltip_widget.hide()

    def eventFilter(self, obj, event):
        """
        事件过滤器，监控提示框的鼠标进入/离开事件

        Args:
            obj: 事件对象
            event: 事件类型

        Returns:
            bool: 是否处理了事件
        """
        if obj is self._tooltip_widget:
            if event.type() == QEvent.Enter:
                self._is_hovering_tooltip = True
                self._hide_timer.stop()
                return True
            elif event.type() == QEvent.Leave:
                self._is_hovering_tooltip = False
                self._hide_timer.start(100)
                return True
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        """
        组件隐藏事件，同时隐藏提示框

        Args:
            event: 事件对象
        """
        self._hide_tooltip()
        super().hideEvent(event)
