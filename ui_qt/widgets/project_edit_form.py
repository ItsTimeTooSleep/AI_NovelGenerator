# -*- coding: utf-8 -*-
"""
项目编辑表单组件
================================================================================
模块功能概述
================================================================================
本模块提供项目编辑的共享表单组件，用于：
1. 图书馆中的"编辑"功能
2. 生成台中的"属性"功能

支持功能：
- 书名、作者、主题、类型编辑
- 封面编辑（支持编辑器模式）
- 章节数量、单章字数设置
- Token消耗统计查看
- 项目路径打开

================================================================================
设计决策
================================================================================
- 使用ScrollableContainer实现自适应布局
- 支持主题/类型修改警告提示
- 统一封装表单逻辑，减少代码重复
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    EditableComboBox,
    LineEdit,
    PushButton,
    SpinBox,
    StrongBodyLabel,
    TextEdit,
)
from qfluentwidgets import FluentIcon as FIF

from ..utils.dialog_sizer import ScrollableContainer
from ..utils.helpers import get_global_notify
from ..utils.styles import Styles


class ProjectEditForm(QWidget):
    """
    项目编辑表单组件

    Args:
        project_data: 项目数据字典
        parent: 父窗口
        dialog_title: 对话框标题，默认"编辑图书信息"

    Attributes:
        nameEdit: 书名输入框
        authorEdit: 作者输入框
        topicEdit: 主题输入框
        genreCombo: 类型下拉框
        coverPathEdit: 封面路径输入框
        numChaptersSpin: 章节数量输入框
        wordCountSpin: 单章字数输入框

    Signals:
        无直接信号，通过get_data()获取表单数据
    """

    GENRE_OPTIONS = [
        "玄幻",
        "科幻",
        "都市",
        "历史",
        "武侠",
        "仙侠",
        "悬疑",
        "奇幻",
        "游戏",
        "轻小说",
    ]

    def __init__(
        self,
        project_data: dict,
        parent: Optional[QWidget] = None,
        dialog_title: str = "编辑图书信息",
    ):
        super().__init__(parent)
        self.project_data = project_data
        self._dialog_title = dialog_title
        self._tokens_manager = None

        try:
            from core.llm import get_global_tokens_manager

            self._tokens_manager = get_global_tokens_manager()
        except Exception:
            pass

        self._setup_ui()

    def _setup_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(15)

        def add_section(title: str, widget: QWidget):
            label = StrongBodyLabel(title, self._container)
            content_layout.addWidget(label)
            content_layout.addWidget(widget)

        paramLabel = StrongBodyLabel("小说参数", self._container)
        content_layout.addWidget(paramLabel)

        self.nameEdit = LineEdit(self._container)
        self.nameEdit.setText(self.project_data.get("name", "未命名"))
        add_section("书名", self.nameEdit)

        self.authorEdit = LineEdit(self._container)
        self.authorEdit.setText(self.project_data.get("author", "未知"))
        add_section("作者", self.authorEdit)

        self._setup_topic_section(content_layout, add_section)
        self._setup_genre_section(content_layout, add_section)
        self._setup_cover_section(add_section)
        self._setup_stats_section(content_layout)
        self._setup_actions_section(content_layout)

        content_layout.addStretch()
        main_layout.addWidget(self._container)

    def _setup_topic_section(self, content_layout, add_section):
        """设置主题编辑区域"""
        self.topicEdit = TextEdit(self._container)
        self.topicEdit.setPlainText(self.project_data.get("topic", ""))
        self.topicEdit.setMinimumHeight(80)
        self.topicEdit.setMaximumHeight(150)

        self.themeWarningLabel = CaptionLabel(
            "⚠️ 修改此项会影响后续章节生成，可能导致剧情不符等意外，请确认您的操作。",
            self._container,
        )
        self.themeWarningLabel.setStyleSheet(Styles.WarningText)
        self.themeWarningLabel.setWordWrap(True)
        self.themeWarningLabel.hide()

        self.topicEdit.textChanged.connect(
            lambda: self.themeWarningLabel.setVisible(
                self.topicEdit.toPlainText() != self.project_data.get("topic", "")
            )
        )

        add_section("小说主题", self.topicEdit)
        content_layout.addWidget(self.themeWarningLabel)

    def _setup_genre_section(self, content_layout, add_section):
        """设置类型选择区域"""
        self.genreCombo = EditableComboBox(self._container)
        self.genreCombo.addItems(self.GENRE_OPTIONS)
        self.genreCombo.setCurrentText(self.project_data.get("genre", "玄幻"))
        self.genreCombo.setEnabled(True)

        self.genreWarningLabel = CaptionLabel(
            "⚠️ 修改此项会影响后续章节生成，可能导致剧情不符等意外，请确认您的操作。",
            self._container,
        )
        self.genreWarningLabel.setStyleSheet(Styles.WarningText)
        self.genreWarningLabel.setWordWrap(True)
        self.genreWarningLabel.hide()

        self.genreCombo.currentTextChanged.connect(
            lambda text: self.genreWarningLabel.setVisible(
                text != self.project_data.get("genre", "玄幻")
            )
        )

        add_section("小说类型", self.genreCombo)
        content_layout.addWidget(self.genreWarningLabel)

    def _setup_cover_section(self, add_section):
        """设置封面编辑区域"""
        self.coverLayout = QHBoxLayout()
        self.coverPathEdit = LineEdit(self._container)
        self.coverPathEdit.setPlaceholderText("选择封面图片 (可选)")
        self.coverPathEdit.setReadOnly(True)
        self.coverBtn = PushButton(FIF.PHOTO, "编辑", self._container)
        self.coverLayout.addWidget(self.coverPathEdit)
        self.coverLayout.addWidget(self.coverBtn)

        coverContainer = QWidget(self._container)
        coverContainer.setLayout(self.coverLayout)
        add_section("封面", coverContainer)

        cover_rel_path = self.project_data.get("cover_image", "")
        if cover_rel_path and "path" in self.project_data:
            cover_abs_path = os.path.join(self.project_data["path"], cover_rel_path)
            self.coverPathEdit.setText(cover_abs_path)

        self.coverBtn.clicked.connect(self._browse_cover)

    def _setup_stats_section(self, content_layout):
        """设置统计信息区域"""
        statsLayout = QHBoxLayout()

        current_chapters = int(self.project_data.get("total_chapters_plan", 100))
        self.numChaptersSpin = SpinBox(self._container)
        self.numChaptersSpin.setRange(current_chapters, 2000)
        self.numChaptersSpin.setValue(current_chapters)
        self.numChaptersSpin.setEnabled(True)

        self.wordCountSpin = SpinBox(self._container)
        self.wordCountSpin.setRange(100, 20000)
        self.wordCountSpin.setSingleStep(100)
        self.wordCountSpin.setValue(
            int(self.project_data.get("words_per_chapter_plan", 3000))
        )
        self.wordCountSpin.setEnabled(True)

        statsContainer = QWidget(self._container)
        statsL = QVBoxLayout(statsContainer)
        statsL.setContentsMargins(0, 0, 0, 0)
        statsL.addWidget(BodyLabel("章节数量 (仅可增加)", self._container))
        statsL.addWidget(self.numChaptersSpin)

        statsContainer2 = QWidget(self._container)
        statsL2 = QVBoxLayout(statsContainer2)
        statsL2.setContentsMargins(0, 0, 0, 0)
        statsL2.addWidget(BodyLabel("单章字数 (仅影响后续生成)", self._container))
        statsL2.addWidget(self.wordCountSpin)

        statsLayout.addWidget(statsContainer)
        statsLayout.addWidget(statsContainer2)

        content_layout.addLayout(statsLayout)

    def _setup_actions_section(self, content_layout):
        """设置操作按钮区域"""
        actionsLayout = QHBoxLayout()

        self.openPathBtn = PushButton(FIF.FOLDER, "在资源管理器中打开", self._container)
        self.openPathBtn.clicked.connect(self._open_path)
        actionsLayout.addWidget(self.openPathBtn)

        if self._tokens_manager:
            self.tokenStatsBtn = PushButton(
                FIF.INFO, "查看Token消耗统计", self._container
            )
            self.tokenStatsBtn.clicked.connect(self._show_token_stats)
            actionsLayout.addWidget(self.tokenStatsBtn)

        actionsLayout.addStretch(1)
        content_layout.addLayout(actionsLayout)

    def _browse_cover(self):
        """打开封面编辑器对话框"""
        from .cover_editor import CoverEditorDialog

        dialog = CoverEditorDialog(self.coverPathEdit.text(), self.window())
        if dialog.exec():
            result = dialog.get_result()
            if result:
                self.coverPathEdit.setText(result)

    def _open_path(self):
        """在资源管理器中打开项目路径"""
        path = self.project_data.get("path", "")
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            notify = get_global_notify()
            if notify:
                notify.error("错误", "路径不存在")

    def _show_token_stats(self):
        """显示Token消耗统计"""
        if not self._tokens_manager:
            notify = get_global_notify()
            if notify:
                notify.warning("提示", "暂无Token消耗记录")
            return

        try:
            from .token_info_dialog import NovelTokenStatsDialog

            dialog = NovelTokenStatsDialog(self._tokens_manager, self.window())
            dialog.exec()
        except Exception as e:
            notify = get_global_notify()
            if notify:
                notify.error("错误", f"打开Token统计失败: {e}")

    def get_data(self) -> dict:
        """
        获取表单数据

        Returns:
            dict: 包含所有表单字段的数据字典
        """
        return {
            "name": self.nameEdit.text(),
            "topic": self.topicEdit.toPlainText(),
            "genre": self.genreCombo.currentText(),
            "author": self.authorEdit.text(),
            "cover_path": self.coverPathEdit.text(),
            "total_chapters_plan": self.numChaptersSpin.value(),
            "words_per_chapter_plan": self.wordCountSpin.value(),
        }
