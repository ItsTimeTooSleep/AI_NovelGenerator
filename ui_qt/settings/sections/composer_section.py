# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    IconWidget,
    MessageBoxBase,
    OptionsConfigItem,
    OptionsValidator,
    PushSettingCard,
    SettingCardGroup,
    SubtitleLabel,
    SwitchSettingCard,
    qconfig,
)
from qfluentwidgets import FluentIcon as FIF

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from core.version import (
    AUTHOR,
    DONATION_URL,
    GITHUB_API_RELEASES_URL,
    GITHUB_REPO_URL,
    LICENSE_URL,
    __version__,
)

from core.config_manager import (
    load_config,
)
from core.ui_prompts import get_prompt
from ui_qt.utils.helpers import get_global_notify
from ui_qt.utils.styles import Styles, ThemeManager
from ui_qt.widgets.setting_card_with_tooltip import OptionsSettingCardWithTooltip

from ..base import BaseSettingsSection


class ComposerSection(BaseSettingsSection):
    """
    Composer AI 设置分区

    配置 Composer AI 的各项参数，包括：
    - AI 等级选择（mini、standard、pro）
    - 使用的模型配置
    - 自动保存设置
    """

    def __init__(self, parent=None):
        """
        初始化 Composer 设置分区

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 顶部标题区域
        self.headerWidget = QWidget(self.view)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.iconWidget = IconWidget(FIF.EDIT, self.view)
        self.iconWidget.setFixedSize(32, 32)

        self.titleContainer = QWidget()
        self.titleLayout = QVBoxLayout(self.titleContainer)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.setSpacing(0)

        self.titleLabel = SubtitleLabel("Composer AI 设置", self.view)

        self.subtitleLabel = BodyLabel("配置 Composer AI 的智能编辑功能", self.view)
        self.subtitleLabel.setStyleSheet(Styles.SecondaryText)

        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addWidget(self.subtitleLabel)

        self.headerLayout.addWidget(self.iconWidget)
        self.headerLayout.addSpacing(10)
        self.headerLayout.addWidget(self.titleContainer)
        self.headerLayout.addStretch()

        self.vBoxLayout.addWidget(self.headerWidget)
        self.vBoxLayout.addSpacing(20)

        # 创建设置卡片组
        self.composerGroup = SettingCardGroup("Composer 配置", self.view)

        # 加载当前配置
        composer_settings = self.loaded_config.get("composer_settings", {})

        self.aiLevelItem = OptionsConfigItem(
            "Composer",
            "AILevel",
            composer_settings.get("ai_level", "standard"),
            OptionsValidator(["mini", "standard", "pro"]),
        )

        tooltip_content = self._get_ai_level_tooltip_content()

        self.aiLevelCard = OptionsSettingCardWithTooltip(
            self.aiLevelItem,
            FIF.ROBOT,
            "AI 等级",
            "选择 Composer AI 的智能等级",
            tooltip_content=tooltip_content,
            texts=["mini (精简)", "standard (标准)", "pro (专业)"],
            parent=self.composerGroup,
        )
        self.aiLevelCard.optionChanged.connect(self._on_ai_level_changed)
        self.composerGroup.addSettingCard(self.aiLevelCard)

        # Composer 使用的模型选择
        self.composerModelCard = PushSettingCard(
            "选择模型",
            FIF.LIBRARY,
            "Composer 模型",
            composer_settings.get("model", "未选择"),
            self.composerGroup,
        )
        self.composerModelCard.clicked.connect(self.show_model_selection_dialog)
        self.composerGroup.addSettingCard(self.composerModelCard)

        # TODO: 自动保存功能暂未实现，暂时隐藏此选项
        # self.autoSaveCard = SwitchSettingCard(
        #     FIF.SAVE,
        #     "自动保存",
        #     "Composer 修改后自动保存更改",
        #     parent=self.composerGroup,
        # )
        # self.autoSaveCard.setChecked(composer_settings.get("auto_save", True))
        # self.autoSaveCard.checkedChanged.connect(self.on_auto_save_toggled)
        # self.composerGroup.addSettingCard(self.autoSaveCard)

        # 差异预览模式选择
        self.diffPreviewModeItem = OptionsConfigItem(
            "Composer",
            "DiffPreviewMode",
            composer_settings.get("diff_preview_mode", "dialog"),
            OptionsValidator(["dialog", "inline"]),
        )

        from qfluentwidgets import OptionsSettingCard

        self.diffPreviewModeCard = OptionsSettingCard(
            self.diffPreviewModeItem,
            FIF.VIEW,
            "差异预览模式",
            "选择 AI 修改结果的显示方式",
            texts=["弹窗预览", "行内显示"],
            parent=self.composerGroup,
        )
        self.diffPreviewModeCard.optionChanged.connect(
            self.on_diff_preview_mode_changed
        )
        self.composerGroup.addSettingCard(self.diffPreviewModeCard)

        self.vBoxLayout.addWidget(self.composerGroup)
        self.vBoxLayout.addStretch()

    def _get_ai_level_tooltip_content(self) -> str:
        """
        获取AI等级提示内容

        Returns:
            str: HTML格式的提示内容
        """
        text_tertiary = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)
        info_color = ThemeManager.get_color(ThemeManager.Colors.INFO)
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)
        pro_color = ThemeManager.get_color(ThemeManager.Colors.PRO_MODE)

        return get_prompt(
            "composer_ai_level_description",
            text_tertiary=text_tertiary,
            info_color=info_color,
            primary_color=primary_color,
            pro_color=pro_color,
        )

    def _on_ai_level_changed(self, config_item):
        """
        AI 等级变更事件处理

        Args:
            config_item: 配置项对象
        """
        if config_item and hasattr(config_item, "value"):
            level_value = config_item.value
        else:
            level_value = "standard"

        if "composer_settings" not in self.loaded_config:
            self.loaded_config["composer_settings"] = {}

        self.loaded_config["composer_settings"]["ai_level"] = level_value

        if self.save_config_to_file():
            self.show_info("成功", f"AI 等级已设置为 {level_value}")

    def on_auto_save_toggled(self, enabled: bool):
        """
        自动保存开关变更事件处理

        Args:
            enabled: 是否启用自动保存
        """
        if "composer_settings" not in self.loaded_config:
            self.loaded_config["composer_settings"] = {}

        self.loaded_config["composer_settings"]["auto_save"] = bool(enabled)

        if self.save_config_to_file():
            status = "启用" if enabled else "禁用"
            self.show_info("成功", f"自动保存已{status}")

    def on_diff_preview_mode_changed(self, option):
        """
        差异预览模式变更事件处理

        Args:
            option: 选中的选项
        """
        if isinstance(option, str):
            mode_value = option
        elif hasattr(option, "text"):
            mode_text = option.text()
            if "弹窗" in mode_text:
                mode_value = "dialog"
            else:
                mode_value = "inline"
        else:
            try:
                mode_value = qconfig.get(self.diffPreviewModeItem)
            except Exception:
                mode_value = "dialog"

        if "composer_settings" not in self.loaded_config:
            self.loaded_config["composer_settings"] = {}

        self.loaded_config["composer_settings"]["diff_preview_mode"] = mode_value

        if self.save_config_to_file():
            mode_name = "弹窗预览" if mode_value == "dialog" else "行内显示"
            self.show_info("成功", f"差异预览模式已设置为 {mode_name}")

    def show_model_selection_dialog(self):
        """显示 Composer 模型选择对话框"""
        self.loaded_config = load_config(self.config_file) or {}
        llm_configs = list(self.loaded_config.get("llm_configs", {}).keys())

        if not llm_configs:
            notify = get_global_notify()
            if notify:
                notify.warning("提示", "请先在 AI 模型库中添加 LLM 模型配置")
            return

        class ComposerModelDialog(MessageBoxBase):
            def __init__(self, configs, current_model, parent=None):
                super().__init__(parent)
                self.selected_model = current_model

                self.titleLabel = SubtitleLabel("选择 Composer 使用的模型", self)
                self.viewLayout.addWidget(self.titleLabel)

                self.formLayout = QVBoxLayout()

                label = BodyLabel("选择一个 LLM 模型配置用于 Composer AI", self)
                self.formLayout.addWidget(label)

                self.combo = ComboBox(self)
                self.combo.addItems(configs)
                if current_model in configs:
                    self.combo.setCurrentText(current_model)
                self.formLayout.addWidget(self.combo)

                self.viewLayout.addLayout(self.formLayout)

                self.yesButton.setText("确认")
                self.cancelButton.setText("取消")
                self.widget.setMinimumWidth(400)

            def get_selected_model(self):
                return self.combo.currentText()

        current_model = self.loaded_config.get("composer_settings", {}).get("model", "")
        dialog = ComposerModelDialog(llm_configs, current_model, parent=self.window())

        if dialog.exec():
            selected_model = dialog.get_selected_model()

            if "composer_settings" not in self.loaded_config:
                self.loaded_config["composer_settings"] = {}

            self.loaded_config["composer_settings"]["model"] = selected_model
            self.composerModelCard.setContent(selected_model)

            if self.save_config_to_file():
                self.show_info("成功", f"Composer 模型已设置为 {selected_model}")
