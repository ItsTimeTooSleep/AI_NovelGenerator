# -*- coding: utf-8 -*-
"""
Step 2 模块 - 生成章节目录

本模块负责 Step 2 的 UI 构建和交互逻辑，包括：
- frameStep2: 生成章节目录界面
- 文本编辑器
- 操作按钮
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
)
from qfluentwidgets import CaptionLabel
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


class Step2Widget:
    """
    Step 2 界面管理器

    负责构建和管理 Step 2 相关的所有 UI 组件。
    """

    def __init__(self, home_tab):
        """
        初始化 Step2Widget

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab

    def build_frame_step2(self, parent):
        """
        构建 Step 2 界面

        Args:
            parent: 父组件

        Returns:
            ModernStepCard: Step 2 界面
        """
        card = ModernStepCard(parent)

        self.home_tab.step2TokenBtn = CommonComponents.create_token_button(
            card, "查看Token消耗详情"
        )
        self.home_tab.step2ToStep1Arrow = CommonComponents.create_nav_arrow(
            card, "left", "返回第一步（小说架构）"
        )

        title_bar = DecoratedTitleBar("第二步 · 生成章节目录", FIF.DOCUMENT, card)
        title_bar.add_right_button(self.home_tab.step2TokenBtn)
        title_bar.add_right_button(self.home_tab.step2ToStep1Arrow)
        card.set_title_bar(title_bar)

        desc = ModernDescription(
            description="基于已生成的架构，自动规划每一章的标题与要点，形成完整目录。",
            parent=card,
            centered=False,
        )
        card.add_content_widget(desc)

        self._build_progress_container(card)
        card.add_content_widget(self.home_tab.step2ProgressContainer)

        self.home_tab.step2TextEdit = CommonComponents.create_text_edit(
            card,
            "生成的章节目录将显示在这里，可在生成后进行修改。",
            hide_by_default=True,
        )
        card.add_content_widget(self.home_tab.step2TextEdit)

        btn_group = ModernButtonGroup(card, centered=True)
        self.home_tab.skipStep2Btn = btn_group.add_secondary_button("跳过 Step 2")
        self.home_tab.step2Btn = btn_group.add_primary_button("开始 Step 2")
        card.add_content_widget(btn_group)

        self.home_tab.step2HintLabel = CaptionLabel(
            "💡 完成 Step 1 后即可进行。生成目录后即可在下方「章节生成」中写正文。",
            card,
        )
        self.home_tab.step2HintLabel.setWordWrap(True)
        self.home_tab.step2HintLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.home_tab.step2HintLabel.setStyleSheet(Styles.HintText)
        card.add_content_widget(self.home_tab.step2HintLabel)

        self.home_tab.continueToReadyBtn = CommonComponents.create_primary_button(
            "继续到第三步", card
        )
        self.home_tab.continueToReadyBtn.hide()
        continue_btn_row = QHBoxLayout()
        continue_btn_row.addStretch(1)
        continue_btn_row.addWidget(self.home_tab.continueToReadyBtn)
        continue_btn_row.addStretch(1)
        card.add_content_layout(continue_btn_row)

        self.home_tab.stopStep2Btn = CommonComponents.create_stop_button(
            "终止生成", card
        )
        stop_btn_row = QHBoxLayout()
        stop_btn_row.addStretch(1)
        stop_btn_row.addWidget(self.home_tab.stopStep2Btn)
        stop_btn_row.addStretch(1)
        card.add_content_layout(stop_btn_row)

        return card

    def _build_progress_container(self, parent):
        """
        构建进度容器组件

        Args:
            parent: 父组件
        """
        self.home_tab.step2ProgressContainer = StepProgressContainer(parent)
        self.home_tab.step2ProgressContainer.setObjectName("step2ProgressContainer")
        self.home_tab.step2ProgressContainer.setStyleSheet(Styles.StepProgressContainer)

        self.home_tab.step2ProgressWidgets = []
        step_names = [
            "章节目录生成",
        ]

        for idx, name in enumerate(step_names):
            step_widget = StepProgressWidget(
                name, idx, self.home_tab.step2ProgressContainer
            )
            self.home_tab.step2ProgressWidgets.append(step_widget)
            self.home_tab.step2ProgressContainer.add_step(step_widget)

        self.home_tab.step2ProgressContainer.hide()
        sp = self.home_tab.step2ProgressContainer.sizePolicy()
        sp.setRetainSizeWhenHidden(False)
        self.home_tab.step2ProgressContainer.setSizePolicy(sp)
