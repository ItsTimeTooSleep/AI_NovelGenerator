# -*- coding: utf-8 -*-
"""
AI Novel Generator - Unified Placeholder Component
===================================================

This module provides a unified empty content placeholder component that displays
friendly prompts when the content area is empty, including an icon, title, and detailed description.

Main Components:
- PlaceholderWidget: General placeholder component
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import IconWidget, StrongBodyLabel


class PlaceholderWidget(QWidget):
    """
    General placeholder component for displaying friendly prompts in empty content states

    Args:
        icon: Icon object (FluentIcon)
        title: Title text
        description: Detailed description text
        parent: Parent widget
    """

    def __init__(self, icon, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName("placeholderWidget")

        # 主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(20)
        self.mainLayout.setAlignment(Qt.AlignCenter)

        # 居中容器
        self.container = QWidget(self)
        self.containerLayout = QVBoxLayout(self.container)
        self.containerLayout.setContentsMargins(40, 60, 40, 60)
        self.containerLayout.setSpacing(20)
        self.containerLayout.setAlignment(Qt.AlignCenter)

        # 图标
        self.iconWidget = IconWidget(icon, self.container)
        self.iconWidget.setFixedSize(64, 64)
        self.containerLayout.addWidget(self.iconWidget, 0, Qt.AlignCenter)

        # 标题
        from ..utils.styles import Styles

        self.titleLabel = StrongBodyLabel(title, self.container)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setStyleSheet(Styles.PlaceholderTitle)
        self.containerLayout.addWidget(self.titleLabel, 0, Qt.AlignCenter)

        # 描述
        self.descriptionLabel = BodyLabel(description, self.container)
        self.descriptionLabel.setAlignment(Qt.AlignCenter)
        self.descriptionLabel.setWordWrap(True)
        self.descriptionLabel.setStyleSheet(Styles.PlaceholderDescription)
        self.descriptionLabel.setMaximumWidth(400)
        self.containerLayout.addWidget(self.descriptionLabel, 0, Qt.AlignCenter)

        self.mainLayout.addWidget(self.container, 1)

        # 设置样式
        self.setStyleSheet("""
            QWidget#placeholderWidget {
                background-color: transparent;
            }
        """)


class EmptyState:
    """
    Predefined empty state configuration collection

    Provides common placeholder configurations to ensure consistent placeholder styling across the app
    """

    @staticmethod
    def library():
        """
        Library empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.LIBRARY,
            "title": "暂无图书",
            "description": "点击右上角「新建图书」按钮，开始创作您的第一部小说吧！",
        }

    @staticmethod
    def chapters():
        """
        Chapter list empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.DOCUMENT,
            "title": "暂无章节",
            "description": "请先在「生成台」中生成章节目录，或手动创建章节文件。",
        }

    @staticmethod
    def chapter_content():
        """
        Chapter content empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.EDIT,
            "title": "开始写作",
            "description": "在这里输入您的章节内容，让故事展开吧！",
        }

    @staticmethod
    def no_project():
        """
        No project selected empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.FOLDER,
            "title": "未选择项目",
            "description": "请先在左侧「书库」中选择或创建一个小说项目。",
        }

    @staticmethod
    def architecture():
        """
        Novel architecture empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.IOT,
            "title": "小说架构未生成",
            "description": "请在「生成台」中点击「开始 Step 1」来生成小说架构，包含世界观、主线与设定。",
        }

    @staticmethod
    def character_state():
        """
        Character state empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.PEOPLE,
            "title": "角色状态未生成",
            "description": "请在「生成台」中完成小说架构生成，系统将自动创建角色状态文件。",
        }

    @staticmethod
    def summary():
        """
        Plot summary empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.QUICK_NOTE,
            "title": "剧情总纲未生成",
            "description": "请在「生成台」中完成相应步骤来生成剧情总纲。",
        }

    @staticmethod
    def directory():
        """
        Chapter directory empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.MENU,
            "title": "章节目录未生成",
            "description": "请先完成「第一步」生成小说架构，然后在「生成台」中点击「开始 Step 2」来生成章节目录。",
        }

    @staticmethod
    def llm_models():
        """
        LLM models empty state configuration

        Returns:
            dict: Dictionary containing icon, title, and description
        """
        return {
            "icon": FIF.ROBOT,
            "title": "暂无模型配置",
            "description": "点击右上角「新增模型」按钮，添加您的大语言模型配置吧！",
        }


__all__ = ["PlaceholderWidget", "EmptyState"]
