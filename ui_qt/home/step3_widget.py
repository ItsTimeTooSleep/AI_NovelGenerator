# -*- coding: utf-8 -*-
"""
Step 3 模块 - 生成草稿

本模块负责 Step 3 的 UI 构建和交互逻辑，包括：
- frameStep3Actions: 生成草稿操作界面
- 操作按钮
- 进度显示
"""

from PyQt5.QtWidgets import (
    QHBoxLayout,
)
from qfluentwidgets import (
    PushButton,
)
from qfluentwidgets import FluentIcon as FIF

from .common_components import (
    DecoratedTitleBar,
    ModernButtonGroup,
    ModernDescription,
    ModernStepCard,
)


class Step3Widget:
    """
    Step 3 界面管理器

    负责构建和管理 Step 3 相关的所有 UI 组件。
    """

    def __init__(self, home_tab):
        """
        初始化 Step3Widget

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab

    def build_frame_step3_actions(self, parent):
        """
        构建 Step 3 操作界面

        Args:
            parent: 父组件

        Returns:
            ModernStepCard: Step 3 操作界面
        """
        card = ModernStepCard(parent)

        chap_num = self.home_tab.currChapterSpin.value()
        title_bar = DecoratedTitleBar(f"第{chap_num}章·生成草稿", FIF.EDIT, card)
        card.set_title_bar(title_bar)

        self.home_tab.step3Title = title_bar.title_label

        desc = ModernDescription(
            description="根据目录与前文自动生成本章草稿，可在下方进行详细调整。",
            parent=card,
        )
        card.add_content_widget(desc)

        btn_group = ModernButtonGroup(card)
        self.home_tab.continueToStep4Btn = btn_group.add_primary_button(
            "继续到第四步（定稿）"
        )
        self.home_tab.step3Btn = btn_group.add_secondary_button("Step 3. 重新生成草稿")
        self.home_tab.step3Btn.setFixedHeight(40)
        self.home_tab.step3Btn.setMinimumWidth(180)
        card.add_content_widget(btn_group)

        stop_btn_row = QHBoxLayout()
        stop_btn_row.addStretch(1)
        self.home_tab.stopChapterStreamBtn = PushButton("终止生成", card)
        self.home_tab.stopChapterStreamBtn.setFixedHeight(34)
        self.home_tab.stopChapterStreamBtn.setMinimumWidth(180)
        self.home_tab.stopChapterStreamBtn.hide()
        stop_btn_row.addWidget(self.home_tab.stopChapterStreamBtn)
        stop_btn_row.addStretch(1)
        card.add_content_layout(stop_btn_row)

        return card
