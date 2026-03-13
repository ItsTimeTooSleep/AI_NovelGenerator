# -*- coding: utf-8 -*-
"""
设置对话框模块
==========

本模块包含设置界面的对话框。
"""

from .config_dialogs import (
    EmbeddingConfigDialog,
    ModelConfigDialog,
    ModelSelectionDialog,
)
from .other_dialogs import (
    ChangeDirectoryDialog,
    ComposerModelDialog,
    ModelTypeDialog,
    UpdateDialog,
)

__all__ = [
    "ModelConfigDialog",
    "EmbeddingConfigDialog",
    "ModelSelectionDialog",
    "ChangeDirectoryDialog",
    "UpdateDialog",
    "ModelTypeDialog",
    "ComposerModelDialog",
]
