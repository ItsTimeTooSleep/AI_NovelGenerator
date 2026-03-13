# -*- coding: utf-8 -*-
"""
对话框尺寸管理器模块
====================

本模块提供统一的对话框尺寸自适应管理功能：
- DialogSizer: 对话框尺寸管理器，基于父窗口尺寸计算对话框尺寸
- 支持相对比例单位（百分比）设置对话框尺寸
- 自动响应窗口大小变化
- 提供滚动区域包装器，确保内容可滚动
"""

from typing import Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QScrollArea, QVBoxLayout, QWidget

from .styles import Styles


class DialogSizer:
    """
    对话框尺寸管理器

    提供基于父窗口尺寸的相对比例计算功能，实现对话框尺寸自适应。

    Attributes:
        width_ratio: 对话框宽度相对于父窗口宽度的比例 (0.0-1.0)
        height_ratio: 对话框高度相对于父窗口高度的比例 (0.0-1.0)
        min_width: 最小宽度（像素）
        min_height: 最小高度（像素）
        max_width: 最大宽度（像素），None表示不限制
        max_height: 最大高度（像素），None表示不限制
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"

    PRESETS = {
        SMALL: {
            "width_ratio": 0.35,
            "height_ratio": 0.45,
            "min_width": 300,
            "min_height": 250,
        },
        MEDIUM: {
            "width_ratio": 0.45,
            "height_ratio": 0.55,
            "min_width": 400,
            "min_height": 350,
        },
        LARGE: {
            "width_ratio": 0.55,
            "height_ratio": 0.65,
            "min_width": 500,
            "min_height": 450,
        },
        XLARGE: {
            "width_ratio": 0.75,
            "height_ratio": 0.80,
            "min_width": 800,
            "min_height": 600,
        },
    }

    def __init__(
        self,
        width_ratio: float = 0.5,
        height_ratio: float = 0.6,
        min_width: int = 400,
        min_height: int = 300,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ):
        """
        初始化对话框尺寸管理器

        Args:
            width_ratio: 宽度比例 (0.0-1.0)
            height_ratio: 高度比例 (0.0-1.0)
            min_width: 最小宽度（像素）
            min_height: 最小高度（像素）
            max_width: 最大宽度（像素），None表示不限制
            max_height: 最大高度（像素），None表示不限制
        """
        self.width_ratio = max(0.1, min(1.0, width_ratio))
        self.height_ratio = max(0.1, min(1.0, height_ratio))
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    @classmethod
    def from_preset(cls, preset_name: str) -> "DialogSizer":
        """
        从预设创建尺寸管理器

        Args:
            preset_name: 预设名称 (SMALL, MEDIUM, LARGE, XLARGE)

        Returns:
            DialogSizer: 尺寸管理器实例

        Raises:
            ValueError: 无效的预设名称
        """
        if preset_name not in cls.PRESETS:
            raise ValueError(
                f"无效的预设名称: {preset_name}，可用预设: {list(cls.PRESETS.keys())}"
            )

        preset = cls.PRESETS[preset_name]
        return cls(
            width_ratio=preset["width_ratio"],
            height_ratio=preset["height_ratio"],
            min_width=preset["min_width"],
            min_height=preset["min_height"],
        )

    def calculate_size(self, parent: Optional[QWidget] = None) -> Tuple[int, int]:
        """
        计算对话框尺寸

        Args:
            parent: 父窗口，用于获取参考尺寸。如果为None，则使用主窗口或屏幕尺寸

        Returns:
            Tuple[int, int]: (宽度, 高度) 元组
        """
        if parent is None:
            parent = QApplication.activeWindow()

        if parent is None:
            screen = QApplication.primaryScreen()
            if screen:
                available_geometry = screen.availableGeometry()
                ref_width = available_geometry.width()
                ref_height = available_geometry.height()
            else:
                ref_width = 1920
                ref_height = 1080
        else:
            ref_width = parent.width()
            ref_height = parent.height()

        width = int(ref_width * self.width_ratio)
        height = int(ref_height * self.height_ratio)

        width = max(self.min_width, width)
        height = max(self.min_height, height)

        if self.max_width is not None:
            width = min(self.max_width, width)
        if self.max_height is not None:
            height = min(self.max_height, height)

        return width, height

    def apply_to_widget(self, widget: QWidget, parent: Optional[QWidget] = None):
        """
        将计算出的尺寸应用到控件

        Args:
            widget: 要设置尺寸的控件
            parent: 父窗口
        """
        width, height = self.calculate_size(parent)

        widget.setMinimumWidth(width)
        widget.setMinimumHeight(height)

        if self.max_width is not None:
            widget.setMaximumWidth(self.max_width)
        else:
            widget.setMaximumWidth(16777215)

        if self.max_height is not None:
            widget.setMaximumHeight(self.max_height)
        else:
            widget.setMaximumHeight(16777215)


class ScrollableContainer(QWidget):
    """
    可滚动容器控件

    提供自动滚动功能的容器，用于对话框内容区域。
    当内容超出可视区域时，自动显示滚动条。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化可滚动容器

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            {Styles.ScrollBar}
        """)

        self._content_widget = QWidget(self._scroll_area)
        self._content_widget.setStyleSheet("background: transparent;")

        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 8, 0)
        self._content_layout.setSpacing(12)

        self._scroll_area.setWidget(self._content_widget)
        self._main_layout.addWidget(self._scroll_area)

    def content_layout(self) -> QVBoxLayout:
        """
        获取内容布局

        Returns:
            QVBoxLayout: 内容区域的垂直布局
        """
        return self._content_layout

    def add_widget(self, widget: QWidget):
        """
        添加控件到内容区域

        Args:
            widget: 要添加的控件
        """
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """
        添加布局到内容区域

        Args:
            layout: 要添加的布局
        """
        self._content_layout.addLayout(layout)

    def add_spacing(self, size: int):
        """
        添加间距

        Args:
            size: 间距大小（像素）
        """
        self._content_layout.addSpacing(size)

    def add_stretch(self, stretch: int = 1):
        """
        添加弹性空间

        Args:
            stretch: 拉伸因子
        """
        self._content_layout.addStretch(stretch)

    def set_content_margins(self, left: int, top: int, right: int, bottom: int):
        """
        设置内容边距

        Args:
            left: 左边距
            top: 上边距
            right: 右边距
            bottom: 下边距
        """
        self._content_layout.setContentsMargins(left, top, right, bottom)


def setup_dialog_scrollable_content(
    dialog,
    sizer: DialogSizer,
    parent: Optional[QWidget] = None,
    content_max_height_ratio: float = 0.5,
) -> ScrollableContainer:
    """
    为对话框设置可滚动内容区域

    Args:
        dialog: 对话框实例（需要有widget属性和viewLayout属性）
        sizer: 尺寸管理器
        parent: 父窗口
        content_max_height_ratio: 内容区域最大高度占对话框高度的比例

    Returns:
        ScrollableContainer: 可滚动容器实例
    """
    sizer.apply_to_widget(dialog.widget, parent)

    container = ScrollableContainer(dialog)
    dialog.viewLayout.addWidget(container)

    return container


def make_dialog_responsive(
    dialog,
    parent: Optional[QWidget] = None,
    width_ratio: float = 0.5,
    height_ratio: float = 0.6,
    min_width: int = 400,
    min_height: int = 300,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
):
    """
    使对话框具有响应式尺寸

    Args:
        dialog: 对话框实例
        parent: 父窗口
        width_ratio: 宽度比例
        height_ratio: 高度比例
        min_width: 最小宽度
        min_height: 最小高度
        max_width: 最大宽度
        max_height: 最大高度
    """
    sizer = DialogSizer(
        width_ratio=width_ratio,
        height_ratio=height_ratio,
        min_width=min_width,
        min_height=min_height,
        max_width=max_width,
        max_height=max_height,
    )
    sizer.apply_to_widget(dialog.widget, parent)


__all__ = [
    "DialogSizer",
    "ScrollableContainer",
    "setup_dialog_scrollable_content",
    "make_dialog_responsive",
]
