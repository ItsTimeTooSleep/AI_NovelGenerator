# -*- coding: utf-8 -*-
"""
UI 设置模块
==========

本模块包含设置界面的核心组件。
"""

from .base import BaseSettingsSection
from .components import EmbeddingCard, ModelCard
from .dialogs import (
    ChangeDirectoryDialog,
    ComposerModelDialog,
    EmbeddingConfigDialog,
    ModelConfigDialog,
    ModelSelectionDialog,
    ModelTypeDialog,
    UpdateDialog,
)
from .main_tab import SettingsTab
from .sections import (
    AboutSection,
    AppearanceSection,
    ComposerSection,
    DirectorySection,
    LLMSection,
    PromptSection,
    ProxySection,
    WebDAVSection,
)
from .utils import ClickableLabel, UpdateCheckThread, WebDAVClient

__all__ = [
    "BaseSettingsSection",
    "SettingsTab",
    "ModelCard",
    "EmbeddingCard",
    "ModelConfigDialog",
    "EmbeddingConfigDialog",
    "ModelSelectionDialog",
    "ChangeDirectoryDialog",
    "UpdateDialog",
    "UpdateCheckThread",
    "ModelTypeDialog",
    "ComposerModelDialog",
    "WebDAVClient",
    "ClickableLabel",
    "LLMSection",
    "ComposerSection",
    "DirectorySection",
    "ProxySection",
    "AppearanceSection",
    "WebDAVSection",
    "AboutSection",
    "PromptSection",
]
