# -*- coding: utf-8 -*-
"""
AI Novel Generator - 统一设置模块（向后兼容代理）
=============================================

本模块是向后兼容代理，所有类都从新的 ui_qt.settings 模块导入。

注意：此文件仅用于保持向后兼容性，新代码应直接从 ui_qt.settings 导入。
"""

from ui_qt.settings import (
    AboutSection,
    AppearanceSection,
    BaseSettingsSection,
    ChangeDirectoryDialog,
    ClickableLabel,
    ComposerModelDialog,
    ComposerSection,
    DirectorySection,
    EmbeddingCard,
    EmbeddingConfigDialog,
    LLMSection,
    ModelCard,
    ModelConfigDialog,
    ModelSelectionDialog,
    ModelTypeDialog,
    PromptSection,
    ProxySection,
    SettingsTab,
    UpdateCheckThread,
    UpdateDialog,
    WebDAVClient,
    WebDAVSection,
)

__all__ = [
    "SettingsTab",
    "BaseSettingsSection",
    "LLMSection",
    "ComposerSection",
    "DirectorySection",
    "ProxySection",
    "AppearanceSection",
    "WebDAVSection",
    "AboutSection",
    "PromptSection",
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
]
