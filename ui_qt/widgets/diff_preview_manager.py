# -*- coding: utf-8 -*-
"""
AI Novel Generator - 差异预览管理器
====================================

本模块实现了统一的差异预览功能，支持两种显示模式：
- 弹窗模式 (dialog): 在独立弹窗中显示差异，适合长文本和需要仔细审核的场景
- 行内模式 (inline): 在编辑器中直接显示差异，适合短文本和快速修改的场景

核心类：
- DiffPreviewMode: 差异预览模式枚举
- DiffPreviewManager: 统一的差异预览管理器

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from enum import Enum
from typing import Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication

from .inline_diff_manager import InlineDiffManager
from .composer_widget import ComposerDiffWidget
from .overlay_manager import OverlayManager


class DiffPreviewMode(Enum):
    """
    差异预览模式枚举

    Attributes:
        DIALOG: 弹窗模式，在独立窗口中显示差异
        INLINE: 行内模式，在编辑器中直接显示差异
    """

    DIALOG = "dialog"
    INLINE = "inline"


class DiffPreviewManager(QObject):
    """
    统一的差异预览管理器

    根据配置选择合适的差异显示方式，支持弹窗和行内两种模式。
    提供统一的接口，屏蔽底层实现差异。

    Signals:
        changes_accepted: 用户接受修改时发出，参数为修改后的文本
        changes_rejected: 用户拒绝修改时发出
    """

    changes_accepted = pyqtSignal(str)
    changes_rejected = pyqtSignal()

    def __init__(self, editor: QWidget, parent: QWidget = None, mode: str = "dialog"):
        """
        初始化差异预览管理器

        Args:
            editor: 文本编辑器实例 (PlainTextEdit 或 TextEdit)
            parent: 父控件
            mode: 预览模式，"dialog" 或 "inline"
        """
        super().__init__(parent)
        self.editor = editor
        self.parent = parent
        self._mode = (
            DiffPreviewMode(mode)
            if mode in ["dialog", "inline"]
            else DiffPreviewMode.DIALOG
        )

        self._dialog_widget: Optional[ComposerDiffWidget] = None
        self._inline_manager: Optional[InlineDiffManager] = None

        self._original_text = ""
        self._modified_text = ""
        self._selection_start = 0
        self._selection_end = 0

    @property
    def mode(self) -> DiffPreviewMode:
        """
        获取当前预览模式

        Returns:
            DiffPreviewMode: 当前预览模式
        """
        return self._mode

    def set_mode(self, mode: str):
        """
        设置预览模式

        Args:
            mode: 预览模式，"dialog" 或 "inline"
        """
        if mode in ["dialog", "inline"]:
            self._mode = DiffPreviewMode(mode)

    def show_diff(
        self,
        original_text: str,
        modified_text: str,
        selection_start: int = None,
        selection_end: int = None,
    ):
        """
        显示差异预览

        根据当前模式选择合适的显示方式。

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置（行内模式需要）
            selection_end: 选区结束位置（行内模式需要）
        """
        self._original_text = original_text
        self._modified_text = modified_text
        self._selection_start = selection_start if selection_start is not None else 0
        self._selection_end = selection_end if selection_end is not None else 0

        if self._mode == DiffPreviewMode.DIALOG:
            self._show_dialog_diff(original_text, modified_text)
        else:
            self._show_inline_diff(
                original_text, modified_text, selection_start, selection_end
            )

    def _show_dialog_diff(self, original_text: str, modified_text: str):
        """
        以弹窗模式显示差异

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
        """
        if self._dialog_widget:
            OverlayManager.hide_widget(
                self.parent, self._dialog_widget, "composer_diff"
            )
            self._dialog_widget.deleteLater()

        self._dialog_widget = ComposerDiffWidget(
            original_text, modified_text, self.parent
        )
        self._dialog_widget.changes_accepted.connect(self._on_dialog_accepted)
        self._dialog_widget.changes_rejected.connect(self._on_dialog_rejected)

        OverlayManager.show_widget(self.parent, self._dialog_widget, "composer_diff")

    def _show_inline_diff(
        self,
        original_text: str,
        modified_text: str,
        selection_start: int,
        selection_end: int,
    ):
        """
        以行内模式显示差异

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置
            selection_end: 选区结束位置
        """
        if not self._inline_manager:
            self._inline_manager = InlineDiffManager(self.editor, self.parent)

        self._inline_manager.show_diff(
            original_text, modified_text, selection_start, selection_end
        )

    def _on_dialog_accepted(self, modified_text: str):
        """
        弹窗模式接受修改的回调

        Args:
            modified_text: 修改后的文本
        """
        self.changes_accepted.emit(modified_text)
        self._cleanup_dialog()

    def _on_dialog_rejected(self):
        """弹窗模式拒绝修改的回调"""
        self.changes_rejected.emit()
        self._cleanup_dialog()

    def _cleanup_dialog(self):
        """清理弹窗资源"""
        if self._dialog_widget:
            OverlayManager.hide_widget(
                self.parent, self._dialog_widget, "composer_diff"
            )
            self._dialog_widget.deleteLater()
            self._dialog_widget = None

    def accept_inline_changes(self):
        """接受行内模式的修改（供外部调用）"""
        if self._inline_manager and self._inline_manager.is_showing_diff():
            self._inline_manager.accept_changes()
            self.changes_accepted.emit(self._modified_text)

    def reject_inline_changes(self):
        """拒绝行内模式的修改（供外部调用）"""
        if self._inline_manager and self._inline_manager.is_showing_diff():
            self._inline_manager.reject_changes()
            self.changes_rejected.emit()

    def is_showing_diff(self) -> bool:
        """
        检查是否正在显示差异

        Returns:
            bool: 是否正在显示差异
        """
        if self._mode == DiffPreviewMode.DIALOG:
            return self._dialog_widget is not None and self._dialog_widget.isVisible()
        else:
            return (
                self._inline_manager is not None
                and self._inline_manager.is_showing_diff()
            )

    def append_content(self, content: str):
        """
        追加内容到差异显示（用于流式传输）

        Args:
            content: 要追加的内容
        """
        if self._mode == DiffPreviewMode.DIALOG and self._dialog_widget:
            self._dialog_widget.append_content(content)
        elif self._inline_manager and self._inline_manager.is_showing_diff():
            self._inline_manager.append_content(content)

    def set_modified_text(self, text: str):
        """
        设置完整的修改后文本（用于流式传输）

        Args:
            text: 完整的修改后文本
        """
        if self._mode == DiffPreviewMode.DIALOG and self._dialog_widget:
            self._dialog_widget.set_modified_text(text)
        elif self._inline_manager and self._inline_manager.is_showing_diff():
            self._inline_manager.set_modified_text(text)

    def cleanup(self):
        """清理所有资源"""
        self._cleanup_dialog()
        if self._inline_manager:
            self._inline_manager.cleanup()
            self._inline_manager = None


def get_diff_preview_mode_from_config(config: dict) -> str:
    """
    从配置中获取差异预览模式

    Args:
        config: 配置字典

    Returns:
        str: 预览模式，"dialog" 或 "inline"
    """
    composer_settings = config.get("composer_settings", {})
    mode = composer_settings.get("diff_preview_mode", "dialog")
    return mode if mode in ["dialog", "inline"] else "dialog"


__all__ = ["DiffPreviewMode", "DiffPreviewManager", "get_diff_preview_mode_from_config"]
