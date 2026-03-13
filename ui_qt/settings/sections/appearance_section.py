# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys

from qfluentwidgets import (
    OptionsConfigItem,
    OptionsSettingCard,
    OptionsValidator,
    SettingCardGroup,
    SwitchSettingCard,
    Theme,
    qconfig,
    setTheme,
)
from qfluentwidgets import FluentIcon as FIF

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from core.version import (
        AUTHOR,
        DONATION_URL,
        GITHUB_API_RELEASES_URL,
        GITHUB_REPO_URL,
        LICENSE_URL,
        __version__,
    )
except ImportError:
    __version__ = "1.0.0"
    GITHUB_REPO_URL = "https://github.com/Doctor-Shadow/AI_NovelGenerator"
    GITHUB_API_RELEASES_URL = (
        "https://api.github.com/repos/Doctor-Shadow/AI_NovelGenerator/releases/latest"
    )
    DONATION_URL = "https://afadian.com/"
    LICENSE_URL = f"{GITHUB_REPO_URL}/blob/main/LICENSE"
    AUTHOR = "ItsTimeTooSleep"

from core.config_manager import (
    save_config,
)

from ..base import BaseSettingsSection


class AppearanceSection(BaseSettingsSection):
    """
    外观设置分区
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.appearanceGroup = SettingCardGroup("界面", self.view)

        self.themeItem = OptionsConfigItem(
            "Appearance",
            "Theme",
            "Light",
            OptionsValidator(["Light", "Dark", "Auto"]),
            restart=True,
        )

        self.themeCard = OptionsSettingCard(
            self.themeItem,
            FIF.BRUSH,
            "应用主题",
            "选择界面显示模式",
            texts=["Light", "Dark", "Auto"],
            parent=self.appearanceGroup,
        )
        initial_theme = self.loaded_config.get("theme", "Light")
        if initial_theme in ["Light", "Dark", "Auto"]:
            qconfig.set(self.themeItem, initial_theme)

        self.themeCard.optionChanged.connect(self.set_theme)
        self.appearanceGroup.addSettingCard(self.themeCard)

        if "streaming_enabled" not in self.loaded_config:
            self.loaded_config["streaming_enabled"] = True
            save_config(self.loaded_config, self.config_file)

        self.streamingCard = SwitchSettingCard(
            FIF.VIDEO,
            "流式传输",
            "生成小说架构等内容时，以流式方式实时显示文本预览",
            parent=self.appearanceGroup,
        )
        self.streamingCard.setChecked(self.loaded_config.get("streaming_enabled", True))
        self.streamingCard.checkedChanged.connect(self.on_streaming_toggled)
        self.appearanceGroup.addSettingCard(self.streamingCard)

        self.wheelTabSwitchCard = SwitchSettingCard(
            FIF.SYNC,
            "开启滚轮切换设置标签页",
            "若开启允许滚轮切换标签页，反之需要手动点击",
            parent=self.appearanceGroup,
        )
        if "enable_wheel_tab_switch" not in self.loaded_config:
            self.loaded_config["enable_wheel_tab_switch"] = True
            save_config(self.loaded_config, self.config_file)
        self.wheelTabSwitchCard.setChecked(
            self.loaded_config.get("enable_wheel_tab_switch", True)
        )
        self.wheelTabSwitchCard.checkedChanged.connect(self.on_wheel_tab_switch_toggled)
        self.appearanceGroup.addSettingCard(self.wheelTabSwitchCard)

        self.vBoxLayout.addWidget(self.appearanceGroup)

    def on_wheel_tab_switch_toggled(self, enabled: bool):
        """
        处理滚轮切换标签页选项的开关事件

        Args:
            enabled: 是否开启滚轮切换
        """
        self.loaded_config["enable_wheel_tab_switch"] = bool(enabled)
        save_config(self.loaded_config, self.config_file)

    def on_streaming_toggled(self, enabled: bool):
        self.loaded_config["streaming_enabled"] = bool(enabled)
        save_config(self.loaded_config, self.config_file)

    def set_theme(self, option):
        if isinstance(option, str):
            theme_value = option
        elif hasattr(option, "text"):
            theme_value = option.text()
        else:
            try:
                theme_value = qconfig.get(self.themeItem)
            except Exception:
                theme_value = "Light"
        if theme_value not in ["Light", "Dark", "Auto"]:
            theme_value = "Light"
        if theme_value == "Light":
            setTheme(Theme.LIGHT)
        elif theme_value == "Dark":
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)

        self.loaded_config["theme"] = theme_value
        save_config(self.loaded_config, self.config_file)
