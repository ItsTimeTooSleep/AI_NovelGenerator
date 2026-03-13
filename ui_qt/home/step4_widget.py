# -*- coding: utf-8 -*-
"""
Step 4 模块 - 定稿章节

本模块负责 Step 4 的 UI 构建和交互逻辑，包括：
- frameStep4Actions: 定稿章节操作界面
- 操作按钮
"""

from qfluentwidgets import FluentIcon as FIF

from .common_components import (
    CommonComponents,
    DecoratedTitleBar,
    ModernButtonGroup,
    ModernDescription,
    ModernStepCard,
)


class Step4Widget:
    """
    Step 4 界面管理器

    负责构建和管理 Step 4 相关的所有 UI 组件。
    """

    def __init__(self, home_tab):
        """
        初始化 Step4Widget

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab

    def build_frame_step4_actions(self, parent):
        """
        构建 Step 4 操作界面

        Args:
            parent: 父组件

        Returns:
            ModernStepCard: Step 4 操作界面
        """
        card = ModernStepCard(parent)

        self.home_tab.step4TokenBtn = CommonComponents.create_token_button(
            card, "查看 Token 消耗详情"
        )
        title_bar = DecoratedTitleBar("第四步 · 定稿章节", FIF.SEND, card)
        title_bar.add_right_button(self.home_tab.step4TokenBtn)
        card.set_title_bar(title_bar)

        desc = ModernDescription(
            description="对草稿进行润色与统一文风后，保存为正式章节文件。", parent=card
        )
        card.add_content_widget(desc)

        btn_group = ModernButtonGroup(card)
        self.home_tab.step4Btn = btn_group.add_primary_button("Step 4. 定稿章节")
        self.home_tab.backToStep3Btn = btn_group.add_secondary_button("返回第三步")
        card.add_content_widget(btn_group)

        return card
