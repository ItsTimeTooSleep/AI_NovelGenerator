# -*- coding: utf-8 -*-
"""
带悬停提示的设置卡片模块

================================================================================
模块功能概述
================================================================================
本模块提供在标题旁带有悬停提示图标的设置卡片组件。

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (
    OptionsConfigItem,
    OptionsSettingCard,
    SettingCard,
)
from qfluentwidgets import FluentIcon as FIF

from ui_qt.widgets.hover_info_icon import HoverInfoIcon


class OptionsSettingCardWithTooltip(OptionsSettingCard):
    """
    带悬停提示的选项设置卡片

    继承自 OptionsSettingCard，在标题旁添加问号图标。
    """

    def __init__(
        self,
        configItem: OptionsConfigItem,
        icon: FIF,
        title: str,
        content: str,
        tooltip_content: str = "",
        texts=None,
        parent=None,
    ):
        """
        初始化带提示的选项设置卡片

        Args:
            configItem: 配置项
            icon: 图标
            title: 标题
            content: 描述内容
            tooltip_content: 悬停提示内容（HTML格式）
            texts: 选项文本列表
            parent: 父控件
        """
        self._tooltip_content = tooltip_content
        self._info_icon = None
        super().__init__(configItem, icon, title, content, texts, parent)

        if self._tooltip_content:
            self._add_tooltip_to_card_title()

    def _add_tooltip_to_card_title(self):
        """在卡片标题旁添加问号图标"""
        self._info_icon = HoverInfoIcon(
            self._tooltip_content, icon_size=14, parent=self.card
        )

        title_label = self.card.titleLabel
        v_box_layout = self.card.vBoxLayout

        # 先获取标题标签在布局中的索引位置（在改变父控件之前）
        index = v_box_layout.indexOf(title_label)

        # 创建标题容器
        title_container = QWidget(self.card)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 从布局中移除标题标签
        v_box_layout.removeWidget(title_label)

        # 将标题标签移到容器
        title_label.setParent(title_container)
        title_layout.addWidget(title_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(self._info_icon, 0, Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addStretch()

        # 在原来的位置插入新容器
        if index >= 0:
            v_box_layout.insertWidget(index, title_container, 0, Qt.AlignLeft)
        else:
            v_box_layout.addWidget(title_container, 0, Qt.AlignLeft)


class SettingCardWithTooltip(SettingCard):
    """
    带悬停提示的基础设置卡片

    在标题旁显示一个问号图标，鼠标悬停时显示详细说明。
    """

    def __init__(
        self,
        icon: FIF,
        title: str,
        content: str,
        tooltip_content: str = "",
        parent=None,
    ):
        """
        初始化带提示的设置卡片

        Args:
            icon: 图标
            title: 标题
            content: 描述内容
            tooltip_content: 悬停提示内容（HTML格式）
            parent: 父控件
        """
        self._tooltip_content = tooltip_content
        self._info_icon = None
        super().__init__(icon, title, content, parent)
        self._init_title_with_tooltip()

    def _init_title_with_tooltip(self):
        """初始化带提示图标的标题"""
        if not self._tooltip_content:
            return

        self._info_icon = HoverInfoIcon(
            self._tooltip_content, icon_size=14, parent=self
        )

        title_label = self.titleLabel
        v_box_layout = self.vBoxLayout

        # 先获取标题标签在布局中的索引位置（在改变父控件之前）
        index = v_box_layout.indexOf(title_label)

        # 创建标题容器
        title_container = QWidget(self)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 从布局中移除标题标签
        v_box_layout.removeWidget(title_label)

        # 将标题标签移到容器
        title_label.setParent(title_container)
        title_layout.addWidget(title_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(self._info_icon, 0, Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addStretch()

        # 在原来的位置插入新容器
        if index >= 0:
            v_box_layout.insertWidget(index, title_container, 0, Qt.AlignLeft)
        else:
            v_box_layout.addWidget(title_container, 0, Qt.AlignLeft)

    def setTooltipContent(self, content: str):
        """
        设置提示内容

        Args:
            content: HTML格式的提示内容
        """
        self._tooltip_content = content
        if self._info_icon:
            self._info_icon.setContent(content)
