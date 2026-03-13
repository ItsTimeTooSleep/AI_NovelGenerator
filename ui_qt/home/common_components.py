# -*- coding: utf-8 -*-
"""
通用 UI 组件模块

本模块提供可复用的 UI 组件构建方法和工厂函数，
用于统一创建常用的 UI 元素，确保界面风格一致。

主要组件工厂函数：
- create_step_card_frame: 创建步骤卡片框架
- create_primary_button: 创建主要操作按钮
- create_secondary_button: 创建次要操作按钮
- create_stop_button: 创建停止按钮
- create_text_edit: 创建文本编辑器
- create_plain_text_edit: 创建纯文本编辑器
- create_step_title_row: 创建步骤标题行
- create_step_description: 创建步骤描述
- create_step_hint: 创建步骤提示
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    IconWidget,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    TransparentToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from ..utils.styles import Styles, ThemeManager


class CommonComponents:
    """
    通用 UI 组件工厂类

    提供统一的 UI 组件创建方法，确保界面风格一致。
    """

    @staticmethod
    def create_step_card_frame(parent, object_name="stepCardFrame"):
        """
        创建步骤卡片框架

        Args:
            parent: 父组件
            object_name: 对象名称，默认为 "stepCardFrame"

        Returns:
            QFrame: 步骤卡片框架对象
        """
        frame = QFrame(parent)
        frame.setObjectName(object_name)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        return frame

    @staticmethod
    def create_primary_button(
        text, parent, icon=None, fixed_height=36, fixed_width=180
    ):
        """
        创建主要操作按钮

        Args:
            text: 按钮文本
            parent: 父组件
            icon: 按钮图标（可选）
            fixed_height: 固定高度，默认为 36
            fixed_width: 固定宽度，默认为 180

        Returns:
            PrimaryPushButton: 主要按钮对象
        """
        if icon:
            btn = PrimaryPushButton(icon, text, parent)
        else:
            btn = PrimaryPushButton(text, parent)
        btn.setFixedHeight(fixed_height)
        if fixed_width:
            btn.setFixedWidth(fixed_width)
        return btn

    @staticmethod
    def create_secondary_button(text, parent, icon=None, fixed_height=32):
        """
        创建次要操作按钮

        Args:
            text: 按钮文本
            parent: 父组件
            icon: 按钮图标（可选）
            fixed_height: 固定高度，默认为 32

        Returns:
            PushButton: 次要按钮对象
        """
        if icon:
            btn = PushButton(icon, text, parent)
        else:
            btn = PushButton(text, parent)
        btn.setFixedHeight(fixed_height)
        return btn

    @staticmethod
    def create_stop_button(text, parent, fixed_height=32, fixed_width=180):
        """
        创建停止按钮

        Args:
            text: 按钮文本
            parent: 父组件
            fixed_height: 固定高度，默认为 32
            fixed_width: 固定宽度，默认为 180

        Returns:
            PushButton: 停止按钮对象
        """
        btn = PushButton(text, parent)
        btn.setFixedHeight(fixed_height)
        if fixed_width:
            btn.setFixedWidth(fixed_width)
        btn.hide()
        sp = btn.sizePolicy()
        sp.setRetainSizeWhenHidden(False)
        btn.setSizePolicy(sp)
        return btn

    @staticmethod
    def create_text_edit(
        parent,
        placeholder_text="",
        min_height=300,
        max_height=450,
        hide_by_default=False,
    ):
        """
        创建文本编辑器

        Args:
            parent: 父组件
            placeholder_text: 占位符文本
            min_height: 最小高度，默认为 300
            max_height: 最大高度，默认为 450
            hide_by_default: 是否默认隐藏，默认为 False

        Returns:
            PlainTextEdit: 纯文本编辑器对象
        """
        edit = PlainTextEdit(parent)
        edit.setPlaceholderText(placeholder_text)
        edit.setMinimumHeight(min_height)
        edit.setMaximumHeight(max_height)
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if hide_by_default:
            edit.hide()
            sp = edit.sizePolicy()
            sp.setRetainSizeWhenHidden(False)
            edit.setSizePolicy(sp)
        return edit

    @staticmethod
    def create_step_title_row(
        parent,
        icon,
        title_text,
        parent_layout=None,
        token_btn=None,
        nav_arrow_left=None,
        nav_arrow_right=None,
    ):
        """
        创建步骤标题行

        Args:
            parent: 父组件
            icon: 标题图标
            title_text: 标题文本
            parent_layout: 父布局（可选）
            token_btn: Token 按钮（可选）
            nav_arrow_left: 左侧导航箭头（可选）
            nav_arrow_right: 右侧导航箭头（可选）

        Returns:
            tuple: (标题行布局, 图标组件, 标题标签)
        """
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        if nav_arrow_left:
            row_layout.addWidget(nav_arrow_left)

        row_layout.addStretch(1)

        icon_widget = IconWidget(icon, parent)
        icon_widget.setFixedSize(32, 32)
        row_layout.addWidget(icon_widget)

        title_label = StrongBodyLabel(title_text, parent)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        font = title_label.font()
        pt = font.pointSize()
        if pt > 0:
            font.setPointSize(min(20, pt + 1))
            title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(title_label, 1)

        row_layout.addStretch(1)

        if token_btn:
            row_layout.addWidget(token_btn)

        if nav_arrow_right:
            row_layout.addWidget(nav_arrow_right)

        if parent_layout:
            parent_layout.addLayout(row_layout)

        return row_layout, icon_widget, title_label

    @staticmethod
    def create_step_description(parent, description_text, parent_layout=None):
        """
        创建步骤描述标签

        Args:
            parent: 父组件
            description_text: 描述文本
            parent_layout: 父布局（可选）

        Returns:
            BodyLabel: 描述标签对象
        """
        desc_label = BodyLabel(description_text, parent)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(Styles.SecondaryText + " margin: 0;")
        if parent_layout:
            parent_layout.addWidget(desc_label)
        return desc_label

    @staticmethod
    def create_step_hint(parent, hint_text, parent_layout=None):
        """
        创建步骤提示标签

        Args:
            parent: 父组件
            hint_text: 提示文本
            parent_layout: 父布局（可选）

        Returns:
            CaptionLabel: 提示标签对象
        """
        hint_label = CaptionLabel(hint_text, parent)
        hint_label.setWordWrap(True)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet(Styles.HintText + " margin: 0; padding: 0;")
        if parent_layout:
            parent_layout.addWidget(hint_label)
        return hint_label

    @staticmethod
    def create_token_button(parent, tooltip="查看Token消耗详情"):
        """
        创建 Token 信息按钮

        Args:
            parent: 父组件
            tooltip: 提示文本，默认为 "查看Token消耗详情"

        Returns:
            TransparentToolButton: Token 按钮对象
        """
        btn = TransparentToolButton(FIF.INFO, parent)
        btn.setFixedSize(28, 28)
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip(tooltip)
        return btn

    @staticmethod
    def create_nav_arrow(parent, direction="right", tooltip=""):
        """
        创建导航箭头按钮

        Args:
            parent: 导航方向，可选值 "right" 或 "left"
            tooltip: 提示文本

        Returns:
            TransparentToolButton: 导航箭头按钮对象
        """
        if direction == "right":
            icon = FIF.RIGHT_ARROW
        else:
            icon = FIF.LEFT_ARROW
        btn = TransparentToolButton(icon, parent)
        btn.setFixedSize(28, 28)
        btn.setIconSize(QSize(16, 16))
        if tooltip:
            btn.setToolTip(tooltip)
        return btn

    @staticmethod
    def create_button_row(parent, buttons, parent_layout=None):
        """
        创建居中按钮行

        Args:
            parent: 父组件
            buttons: 要放置的按钮，可以是单个按钮或按钮列表
            parent_layout: 父布局（可选）

        Returns:
            QHBoxLayout: 按钮行布局
        """
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        if isinstance(buttons, list):
            for i, btn in enumerate(buttons):
                btn_row.addWidget(btn)
                if i < len(buttons) - 1:
                    btn_row.addSpacing(10)
        else:
            btn_row.addWidget(buttons)
        btn_row.addStretch(1)
        if parent_layout:
            parent_layout.addLayout(btn_row)
        return btn_row


class AccentLine(QFrame):
    """
    纯紫色装饰线

    用于标题栏左侧的视觉强调
    """

    def __init__(self, parent=None, height=40):
        """
        初始化装饰线

        参数:
            parent: 父组件
            height: 装饰线高度，默认为40像素
        """
        super().__init__(parent)
        self.setFixedWidth(4)
        self.setFixedHeight(height)

    def paintEvent(self, event):
        """
        绘制圆角紫色装饰线

        参数:
            event: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        primary_color = QColor(ThemeManager.get_color(ThemeManager.Colors.PRIMARY))
        painter.setPen(Qt.NoPen)
        painter.setBrush(primary_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 2, 2)


class DecoratedTitleBar(QFrame):
    """
    装饰性标题栏组件

    特点：
    - 左对齐布局（打破居中）
    - 渐变色装饰线
    - 可选的右上角操作按钮
    """

    def __init__(self, title: str, icon: FIF, parent=None):
        super().__init__(parent)
        self.setObjectName("decoratedTitleBar")
        self.setFixedHeight(56)
        self._init_ui(title, icon)
        self._apply_style()

    def _init_ui(self, title: str, icon: FIF):
        """
        初始化UI布局

        参数:
            title: 标题文本
            icon: 图标枚举值
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(0)

        # 创建装饰竖线，高度设置为32px以适应圆角标题栏
        self.accent_line = AccentLine(self, height=32)
        self.accent_line.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.accent_line, alignment=Qt.AlignVCenter)

        layout.addSpacing(16)

        self.icon_widget = IconWidget(icon, self)
        self.icon_widget.setFixedSize(28, 28)
        layout.addWidget(self.icon_widget)

        layout.addSpacing(12)

        self.title_label = StrongBodyLabel(title, self)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        self.right_buttons = QWidget(self)
        self.right_buttons_layout = QHBoxLayout(self.right_buttons)
        self.right_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.right_buttons_layout.setSpacing(8)
        layout.addWidget(self.right_buttons)

    def add_right_button(self, button):
        """添加右侧按钮"""
        self.right_buttons_layout.addWidget(button)

    def _apply_style(self):
        is_dark = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY) == "#ffffff"
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)
        bg_color = (
            f"rgba(139, 92, 246, 0.08)" if is_dark else f"rgba(139, 92, 246, 0.05)"
        )
        self.setStyleSheet(f"""
            QFrame#decoratedTitleBar {{
                background-color: {bg_color};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(139, 92, 246, 0.2);
            }}
        """)


class ModernDescription(QFrame):
    """
    现代化描述组件

    特点：
    - 支持左对齐或居中对齐
    - 可选的前置图标
    - 分层文字样式
    """

    def __init__(self, description: str, hint: str = None, parent=None, centered=False):
        super().__init__(parent)
        self._centered = centered
        self._init_ui(description, hint)

    def _init_ui(self, description: str, hint: str = None):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        desc_label = BodyLabel(description, self)
        desc_label.setWordWrap(True)
        if self._centered:
            desc_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        else:
            desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        desc_label.setStyleSheet(Styles.SecondaryText)
        layout.addWidget(desc_label)

        if hint:
            hint_label = CaptionLabel(hint, self)
            hint_label.setWordWrap(True)
            if self._centered:
                hint_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            else:
                hint_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            hint_label.setStyleSheet(Styles.HintText)
            layout.addWidget(hint_label)


class ModernButtonGroup(QFrame):
    """
    现代化按钮组

    特点：
    - 支持右对齐或居中对齐
    - 主次按钮分离
    - 统一间距
    """

    def __init__(self, parent=None, centered=False):
        super().__init__(parent)
        self._centered = centered
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.secondary_buttons = []
        self.primary_button = None

    def add_secondary_button(self, text: str, icon: FIF = None):
        """添加次要按钮"""
        if icon:
            btn = PushButton(icon, text, self)
        else:
            btn = PushButton(text, self)
        btn.setFixedHeight(36)
        self.secondary_buttons.append(btn)
        self.layout().addWidget(btn)
        return btn

    def add_primary_button(self, text: str, icon: FIF = None):
        """添加主要按钮"""
        if icon:
            btn = PrimaryPushButton(icon, text, self)
        else:
            btn = PrimaryPushButton(text, self)
        btn.setFixedHeight(40)
        btn.setMinimumWidth(160)
        self.primary_button = btn
        self.layout().addWidget(btn)

        if self._centered:
            self.layout().insertStretch(0, 1)
            self.layout().addStretch(1)

        return btn


class ModernStepCard(QFrame):
    """
    现代化步骤卡片

    特点：
    - 装饰性标题栏
    - 分层内容区域
    - 渐变边框效果
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernStepCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.title_bar = None

        self.content_area = QFrame(self)
        self.content_area.setObjectName("cardContent")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 16, 20, 20)
        self.content_layout.setSpacing(12)
        self.main_layout.addWidget(self.content_area)

    def set_title_bar(self, title_bar: DecoratedTitleBar):
        """设置标题栏"""
        self.title_bar = title_bar
        self.main_layout.insertWidget(0, title_bar)

    def add_content_widget(self, widget):
        """添加内容控件"""
        self.content_layout.addWidget(widget)

    def add_content_layout(self, layout):
        """添加内容布局"""
        self.content_layout.addLayout(layout)

    def _apply_style(self):
        from ..utils.styles import ThemeManager

        is_dark = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY) == "#ffffff"

        if is_dark:
            bg = "rgba(255, 255, 255, 0.03)"
            border = "rgba(255, 255, 255, 0.08)"
        else:
            bg = "rgba(255, 255, 255, 0.8)"
            border = "rgba(0, 0, 0, 0.08)"

        self.setStyleSheet(f"""
            QFrame#modernStepCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 16px;
            }}
            QFrame#cardContent {{
                background-color: transparent;
            }}
        """)
