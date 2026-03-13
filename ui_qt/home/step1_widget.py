# -*- coding: utf-8 -*-
"""
Step 1 模块 - 生成小说架构

本模块负责 Step 1 的 UI 构建和交互逻辑，包括：
- frameStep1: 生成小说架构主界面
- frameStep1Review: 小说架构查看界面
- frameNoProject: 无项目提示界面
- 进度显示组件
- 文本编辑器
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    IconWidget,
    PlainTextEdit,
    PushButton,
    StrongBodyLabel,
)
from qfluentwidgets import FluentIcon as FIF

from ..utils.animations import StepProgressContainer, StepProgressWidget
from ..utils.styles import Styles
from .common_components import (
    CommonComponents,
    DecoratedTitleBar,
    ModernButtonGroup,
    ModernDescription,
    ModernStepCard,
)


class Step1Widget:
    """
    Step 1 界面管理器

    负责构建和管理 Step 1 相关的所有 UI 组件。
    """

    def __init__(self, home_tab):
        """
        初始化 Step1Widget

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab

    def build_frame_no_project(self, parent):
        """
        构建无项目提示界面

        Args:
            parent: 父组件

        Returns:
            QFrame: 无项目提示界面
        """
        frame = CommonComponents.create_step_card_frame(parent)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        icon = IconWidget(FIF.BOOK_SHELF, frame)
        icon.setFixedSize(32, 32)
        layout.addWidget(icon, 0, Qt.AlignCenter)

        title = StrongBodyLabel("第一步 · 生成小说架构", frame)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(8)

        msg = BodyLabel(
            "请先在左侧「书库」中选择或创建一个项目，再回到此处开始 Step 1。",
            frame,
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(Styles.HintText + " margin: 0;")
        layout.addWidget(msg)

        layout.addSpacing(6)

        self.home_tab.step1BtnNoProject = PushButton(FIF.LIBRARY, "前往书库", frame)
        self.home_tab.step1BtnNoProject.setFixedHeight(36)
        self.home_tab.step1BtnNoProject.setFixedWidth(180)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.home_tab.step1BtnNoProject)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        return frame

    def build_frame_step1(self, parent):
        """
        构建 Step 1 主界面

        Args:
            parent: 父组件

        Returns:
            ModernStepCard: Step 1 主界面
        """
        card = ModernStepCard(parent)

        self.home_tab.step1TokenBtn = CommonComponents.create_token_button(
            card, "查看Token消耗详情"
        )
        self.home_tab.step1ToStep2Arrow = CommonComponents.create_nav_arrow(
            card, "right", "前往第二步（章节目录）"
        )

        title_bar = DecoratedTitleBar("第一步 · 生成小说架构", FIF.CERTIFICATE, card)
        title_bar.add_right_button(self.home_tab.step1TokenBtn)
        title_bar.add_right_button(self.home_tab.step1ToStep2Arrow)
        card.set_title_bar(title_bar)

        desc = ModernDescription(
            description="根据主题与类型生成整本书的世界观、主线与设定，是后续所有内容的基础。",
            parent=card,
            centered=False,
        )
        card.add_content_widget(desc)

        self._build_progress_container(card)
        card.add_content_widget(self.home_tab.step1ProgressContainer)

        self.home_tab.step1TextEdit = CommonComponents.create_text_edit(
            card,
            "小说整体架构将显示在这里，可在生成后进行修改。",
            hide_by_default=True,
        )
        card.add_content_widget(self.home_tab.step1TextEdit)

        btn_group = ModernButtonGroup(card, centered=True)
        self.home_tab.skipStep1Btn = btn_group.add_secondary_button("跳过 Step 1")
        self.home_tab.step1Btn = btn_group.add_primary_button("开始 Step 1")
        card.add_content_widget(btn_group)

        self.home_tab.continueToStep2Btn = CommonComponents.create_primary_button(
            "继续到 Step 2", card
        )
        self.home_tab.continueToStep2Btn.hide()
        continue_btn_row = QHBoxLayout()
        continue_btn_row.addStretch(1)
        continue_btn_row.addWidget(self.home_tab.continueToStep2Btn)
        continue_btn_row.addStretch(1)
        card.add_content_layout(continue_btn_row)

        self.home_tab.stopStep1Btn = CommonComponents.create_stop_button(
            "终止生成", card
        )
        stop_btn_row = QHBoxLayout()
        stop_btn_row.addStretch(1)
        stop_btn_row.addWidget(self.home_tab.stopStep1Btn)
        stop_btn_row.addStretch(1)
        card.add_content_layout(stop_btn_row)

        return card

    def _build_progress_container(self, parent):
        """
        构建进度容器组件

        Args:
            parent: 父组件
        """
        self.home_tab.step1ProgressContainer = StepProgressContainer(parent)
        self.home_tab.step1ProgressContainer.setObjectName("step1ProgressContainer")
        self.home_tab.step1ProgressContainer.setStyleSheet(Styles.StepProgressContainer)

        self.home_tab.step1ProgressWidgets = []
        step_names = [
            "书名生成",
            "核心种子生成",
            "角色动力学构建",
            "初始角色状态生成",
            "世界观搭建",
            "情节架构设计",
        ]

        for idx, name in enumerate(step_names):
            step_widget = StepProgressWidget(
                name, idx, self.home_tab.step1ProgressContainer
            )
            self.home_tab.step1ProgressWidgets.append(step_widget)
            self.home_tab.step1ProgressContainer.add_step(step_widget)

        self.home_tab.step1ProgressContainer.hide()
        sp = self.home_tab.step1ProgressContainer.sizePolicy()
        sp.setRetainSizeWhenHidden(False)
        self.home_tab.step1ProgressContainer.setSizePolicy(sp)

    def build_frame_step1_review(self, parent):
        """
        构建 Step 1 查看界面

        Args:
            parent: 父组件

        Returns:
            ModernStepCard: Step 1 查看界面
        """
        card = ModernStepCard(parent)

        self.home_tab.step1ReviewToStep2Arrow = CommonComponents.create_nav_arrow(
            card, "right", "前往第二步（章节目录）"
        )

        title_bar = DecoratedTitleBar(
            "第一步 · 小说架构（查看）", FIF.CERTIFICATE, card
        )
        title_bar.add_right_button(self.home_tab.step1ReviewToStep2Arrow)
        card.set_title_bar(title_bar)

        desc = ModernDescription(
            description="上方预览区显示已生成的小说架构内容（框架）。",
            hint="💡 需要调整时，可在「项目已就绪」中点击'重新生成架构'。",
            parent=card,
        )
        card.add_content_widget(desc)

        self.home_tab.step1ReviewTextEdit = PlainTextEdit(card)
        self.home_tab.step1ReviewTextEdit.setPlaceholderText(
            "小说架构内容将显示在这里，可在此处进行修改。"
        )
        self.home_tab.step1ReviewTextEdit.setMinimumHeight(300)
        self.home_tab.step1ReviewTextEdit.setMaximumHeight(450)
        self.home_tab.step1ReviewTextEdit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        card.add_content_widget(self.home_tab.step1ReviewTextEdit)

        return card
