# -*- coding: utf-8 -*-
"""
AI Novel Generator - 项目设定模块
====================================

本模块实现了项目设定主界面，整合了四个子标签页：
- 目录结构：管理小说的章节目录
- 角色库：管理小说中的角色
- 剧情总纲：管理小说的全局摘要
- 小说架构：管理小说的整体架构

主要组件：
- ProjectTab: 项目设定主界面
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea, SegmentedWidget, SubtitleLabel, TitleLabel

from .architecture_tab import ArchitectureInterface
from .character_tab import RolesInterface
from .directory_tab import DirectoryInterface
from .summary_tab import SummaryInterface


class ProjectTab(QWidget):
    """
    项目设定主界面

    使用 SegmentedWidget 导航切换不同的项目设定子页面。
    """

    def __init__(self, parent=None):
        """
        初始化项目设定主界面

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("projectTab")

        # 主布局 - 使用滚动区域包裹
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setObjectName("projectScrollArea")
        self.scrollArea.setStyleSheet(
            "QScrollArea#projectScrollArea { background-color: transparent; border: none; }"
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

        # 内容布局 - 更紧凑的间距
        self.vBoxLayout = QVBoxLayout(self.contentWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(20, 15, 20, 15)

        # 标题区域
        self.headerLayout = QVBoxLayout()
        self.titleLabel = TitleLabel("项目设定", self)
        self.subtitleLabel = SubtitleLabel("管理您的小说项目配置", self)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addLayout(self.headerLayout)

        # 导航栏居中
        pivotLayout = QHBoxLayout()
        pivotLayout.addStretch()

        # 导航栏 - 使用 SegmentedWidget 更明显
        self.pivot = SegmentedWidget(self)
        self.pivot.setFixedWidth(550)
        pivotLayout.addWidget(self.pivot)
        pivotLayout.addStretch()

        self.vBoxLayout.addLayout(pivotLayout)

        # 页面堆栈
        self.stackedWidget = QStackedWidget(self)

        # 创建各子页面
        self.directoryTab = DirectoryInterface(self)
        self.characterTab = RolesInterface(self)
        self.summaryTab = SummaryInterface(self)
        self.architectureTab = ArchitectureInterface(self)

        # 添加导航项和子页面
        self.addSubInterface(self.directoryTab, "directory", "📁 目录结构")
        self.addSubInterface(self.characterTab, "roles", "👥 角色库")
        self.addSubInterface(self.summaryTab, "summary", "📖 剧情总纲")
        self.addSubInterface(self.architectureTab, "architecture", "🏗️ 小说架构")

        # 添加到主布局
        self.vBoxLayout.addWidget(self.stackedWidget)

        # 默认显示目录结构页
        self.stackedWidget.setCurrentIndex(0)
        self.pivot.setCurrentItem("directory")

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        """
        添加子界面

        Args:
            widget: 子界面控件
            objectName: 界面的对象名称
            text: 导航标签文本
        """
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )


__all__ = ["ProjectTab"]
