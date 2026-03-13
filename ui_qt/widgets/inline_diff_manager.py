# -*- coding: utf-8 -*-
"""
AI Novel Generator - 行内差异显示管理器
==========================================

本模块实现了在编辑器中直接显示 AI 修改差异的功能：
- InlineDiffManager: 行内差异管理器
- DiffHoverToolbar: 悬停时显示的差异操作工具栏
- 支持逐处修改的确认/取消
"""

import difflib

from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QObject,
)
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QWidget,
    QApplication,
)
from qfluentwidgets import isDarkTheme

from ..utils.styles import ThemeManager


class DiffHoverToolbar(QFrame):
    """
    悬停时显示的差异操作工具栏

    当鼠标悬停在差异区域时，在差异旁边显示接受/拒绝按钮
    """

    accept_clicked = pyqtSignal()
    reject_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """
        初始化差异工具栏

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_CARD, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        success_color = ThemeManager.get_color(ThemeManager.Colors.SUCCESS, is_dark)
        error_color = ThemeManager.get_color(ThemeManager.Colors.ERROR, is_dark)

        self.setStyleSheet(f"""
            DiffHoverToolbar {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        self.reject_btn = QPushButton("✕", self)
        self.reject_btn.setFixedSize(28, 28)
        self.reject_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {error_color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
        """)
        self.reject_btn.clicked.connect(self._on_reject)
        self.reject_btn.setToolTip("拒绝修改")
        layout.addWidget(self.reject_btn)

        self.accept_btn = QPushButton("✓", self)
        self.accept_btn.setFixedSize(28, 28)
        self.accept_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {success_color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:pressed {{
                background-color: #047857;
            }}
        """)
        self.accept_btn.clicked.connect(self._on_accept)
        self.accept_btn.setToolTip("接受修改")
        layout.addWidget(self.accept_btn)

        self.adjustSize()

    def show_at_position(self, pos: QPoint):
        """
        在指定位置显示工具栏

        Args:
            pos: 全局坐标位置
        """
        self.setWindowOpacity(1.0)
        self.move(pos)
        self.show()

    def hide_with_animation(self):
        """带动画的隐藏"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def _on_accept(self):
        """确认按钮点击"""
        self.accept_clicked.emit()
        self.hide()

    def _on_reject(self):
        """取消按钮点击"""
        self.reject_clicked.emit()
        self.hide()


class DiffHighlighter(QObject):
    """
    差异高亮区域管理器

    用于检测鼠标是否悬停在差异区域上
    """

    def __init__(self, editor: QTextEdit, parent=None):
        """
        初始化差异高亮管理器

        Args:
            editor: 文本编辑器
            parent: 父控件
        """
        super().__init__(parent)
        self.editor = editor
        self.diff_ranges = []
        self._is_enabled = False

        self.editor.setMouseTracking(True)
        self.editor.viewport().installEventFilter(self)

    def set_diff_ranges(self, ranges):
        """
        设置差异范围列表

        Args:
            ranges: 差异范围列表，每个元素为 (start, end) 元组
        """
        self.diff_ranges = ranges

    def enable(self):
        """启用差异高亮检测"""
        self._is_enabled = True

    def disable(self):
        """禁用差异高亮检测"""
        self._is_enabled = False
        self.diff_ranges = []

    def eventFilter(self, obj, event):
        """事件过滤器，检测鼠标移动"""
        if not self._is_enabled:
            return super().eventFilter(obj, event)

        if event.type() == event.MouseMove:
            cursor = self.editor.cursorForPosition(event.pos())
            position = cursor.position()

            for start, end in self.diff_ranges:
                if start <= position <= end:
                    self._show_toolbar_at_cursor(cursor, start, end)
                    return super().eventFilter(obj, event)

            self._hide_toolbar()

        return super().eventFilter(obj, event)

    def _show_toolbar_at_cursor(self, cursor, start, end):
        """在光标位置显示工具栏"""
        pass

    def _hide_toolbar(self):
        """隐藏工具栏"""
        pass


class InlineDiffManager(QObject):
    """
    行内差异管理器

    在编辑器中直接显示 AI 修改的差异，并提供确认/取消操作
    当鼠标悬停在差异区域时，动态显示接受/拒绝按钮
    """

    def __init__(self, editor: QTextEdit, parent=None):
        """
        初始化行内差异管理器

        Args:
            editor: QTextEdit 或 PlainTextEdit 实例
            parent: 父控件
        """
        super().__init__(parent)
        self.editor = editor
        self.parent = parent
        self.original_text = ""
        self.modified_text = ""
        self.original_selection_start = 0
        self.original_selection_end = 0
        self.differences = []
        self.toolbar = None
        self._is_showing_diff = False
        self._saved_cursor_position = 0
        self._diff_group_id = 0
        self._hover_timer = QTimer()
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._check_hover)
        self._last_hover_pos = None
        self._is_hovering = False

        self.editor.setMouseTracking(True)
        self.editor.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器，检测鼠标悬停"""
        if not self._is_showing_diff:
            return False

        if event.type() == event.MouseMove:
            self._last_hover_pos = event.pos()
            self._hover_timer.start(100)
        elif event.type() == event.Leave:
            self._hover_timer.stop()
            self._hide_toolbar_delayed()

        return False

    def _check_hover(self):
        """检查鼠标是否悬停在差异区域上"""
        if not self._last_hover_pos or not self._is_showing_diff:
            return

        cursor = self.editor.cursorForPosition(self._last_hover_pos)
        position = cursor.position()

        is_in_diff = False
        for diff in self.differences:
            if diff["start"] <= position <= diff["end"]:
                is_in_diff = True
                if not self._is_hovering:
                    self._is_hovering = True
                    # 不传递 cursor 对象，而是传递位置信息
                    self._show_toolbar_at_diff(self._last_hover_pos, diff)
                break

        if not is_in_diff and self._is_hovering:
            self._is_hovering = False
            self._hide_toolbar_delayed()

    def _show_toolbar_at_diff(self, hover_pos, diff):
        """
        在差异位置显示工具栏

        Args:
            hover_pos: 鼠标悬停位置
            diff: 差异信息字典
        """
        if not self.toolbar:
            self.toolbar = DiffHoverToolbar(self.parent)
            self.toolbar.accept_clicked.connect(self.accept_changes)
            self.toolbar.reject_clicked.connect(self.reject_changes)

        # 使用悬停位置获取光标矩形
        cursor = self.editor.cursorForPosition(hover_pos)
        cursor_rect = self.editor.cursorRect(cursor)
        global_pos = self.editor.mapToGlobal(cursor_rect.bottomRight())

        toolbar_x = global_pos.x() + 5
        toolbar_y = global_pos.y() - self.toolbar.height() // 2

        screen = QApplication.primaryScreen().geometry()
        if toolbar_x + self.toolbar.width() > screen.width():
            toolbar_x = global_pos.x() - self.toolbar.width() - 5
        if toolbar_y < 0:
            toolbar_y = global_pos.y()
        if toolbar_y + self.toolbar.height() > screen.height():
            toolbar_y = global_pos.y() - self.toolbar.height()

        self.toolbar.show_at_position(QPoint(toolbar_x, toolbar_y))

    def _hide_toolbar_delayed(self):
        """延迟隐藏工具栏"""
        QTimer.singleShot(200, self._try_hide_toolbar)

    def _try_hide_toolbar(self):
        """尝试隐藏工具栏（如果鼠标不在工具栏上）"""
        if self.toolbar and self.toolbar.isVisible():
            if not self.toolbar.geometry().contains(QApplication.cursor().pos()):
                self.toolbar.hide_with_animation()

    def is_showing_diff(self) -> bool:
        """
        检查是否正在显示差异

        Returns:
            bool: 是否正在显示差异
        """
        return self._is_showing_diff

    def show_diff(
        self,
        original_text: str,
        modified_text: str,
        selection_start: int = None,
        selection_end: int = None,
    ):
        """
        在编辑器中显示差异

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置（可选，用于异步处理后定位）
            selection_end: 选区结束位置（可选，用于异步处理后定位）
        """
        self.original_text = original_text
        self.modified_text = modified_text
        self._diff_group_id += 1

        cursor = self.editor.textCursor()
        # 如果提供了选区位置，使用提供的位置；否则使用当前选区
        if selection_start is not None and selection_end is not None:
            self.original_selection_start = selection_start
            self.original_selection_end = selection_end
            self._saved_cursor_position = selection_start
            # 将光标移动到保存的选区位置
            cursor.setPosition(selection_start)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            # 将修改后的光标设置回编辑器
            self.editor.setTextCursor(cursor)
        else:
            self.original_selection_start = cursor.selectionStart()
            self.original_selection_end = cursor.selectionEnd()
            self._saved_cursor_position = cursor.position()

        self._render_diff()

        self._is_showing_diff = True
        self._is_hovering = False

        cursor.setPosition(self.original_selection_start)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _render_diff(self):
        """
        内部方法：渲染差异显示
        """
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        # 清除当前显示的差异内容
        if self._is_showing_diff:
            cursor.setPosition(self.original_selection_start)
            cursor.setPosition(
                self.original_selection_start + len(self.modified_text),
                QTextCursor.KeepAnchor,
            )
            cursor.removeSelectedText()
        else:
            cursor.removeSelectedText()

        differ = difflib.SequenceMatcher(None, self.original_text, self.modified_text)
        self.differences = []

        is_dark = isDarkTheme()
        delete_fg = QColor("#F87171")
        delete_bg = QColor("#FEE2E2") if not is_dark else QColor("#7F1D1D")
        insert_fg = QColor("#059669")
        insert_bg = QColor("#D1FAE5") if not is_dark else QColor("#064E3B")

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            start_pos = cursor.position()

            if tag == "equal":
                format = QTextCharFormat()
                format.setForeground(
                    QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY))
                )
                format.setBackground(QColor("transparent"))
                cursor.insertText(self.modified_text[j1:j2], format)

            elif tag == "delete":
                format = QTextCharFormat()
                format.setForeground(delete_fg)
                format.setBackground(delete_bg)
                format.setFontStrikeOut(True)
                text = self.original_text[i1:i2]
                cursor.insertText(text, format)

                end_pos = cursor.position()
                self.differences.append(
                    {
                        "type": "delete",
                        "start": start_pos,
                        "end": end_pos,
                        "original": text,
                        "modified": "",
                        "group_id": self._diff_group_id,
                    }
                )

            elif tag == "insert":
                format = QTextCharFormat()
                format.setForeground(insert_fg)
                format.setBackground(insert_bg)
                text = self.modified_text[j1:j2]
                cursor.insertText(text, format)

                end_pos = cursor.position()
                self.differences.append(
                    {
                        "type": "insert",
                        "start": start_pos,
                        "end": end_pos,
                        "original": "",
                        "modified": text,
                        "group_id": self._diff_group_id,
                    }
                )

            elif tag == "replace":
                format = QTextCharFormat()
                format.setForeground(delete_fg)
                format.setBackground(delete_bg)
                format.setFontStrikeOut(True)
                del_text = self.original_text[i1:i2]
                cursor.insertText(del_text, format)

                del_end = cursor.position()
                self.differences.append(
                    {
                        "type": "delete",
                        "start": start_pos,
                        "end": del_end,
                        "original": del_text,
                        "modified": "",
                        "group_id": self._diff_group_id,
                    }
                )

                format = QTextCharFormat()
                format.setForeground(insert_fg)
                format.setBackground(insert_bg)
                ins_text = self.modified_text[j1:j2]
                cursor.insertText(ins_text, format)

                ins_end = cursor.position()
                self.differences.append(
                    {
                        "type": "insert",
                        "start": del_end,
                        "end": ins_end,
                        "original": "",
                        "modified": ins_text,
                        "group_id": self._diff_group_id,
                    }
                )

        cursor.endEditBlock()

    def append_content(self, content: str):
        """
        追加内容到修改后的文本并更新显示（用于流式传输）

        Args:
            content: 要追加的内容
        """
        self.modified_text += content
        self._render_diff()

    def set_modified_text(self, text: str):
        """
        设置修改后的文本并更新显示（用于流式传输）

        Args:
            text: 完整的修改后文本
        """
        self.modified_text = text
        self._render_diff()

    def accept_changes(self):
        """接受修改 - 清除差异格式，保留修改后的文本"""
        cursor = self.editor.textCursor()
        cursor.setPosition(self.original_selection_start)
        cursor.setPosition(
            self.original_selection_start + len(self.modified_text),
            QTextCursor.KeepAnchor,
        )

        format = QTextCharFormat()
        format.setForeground(
            QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY))
        )
        format.setBackground(QColor("transparent"))
        format.setFontStrikeOut(False)

        cursor.mergeCharFormat(format)

        self._cleanup()

        if self.parent and hasattr(self.parent, "on_diff_accepted"):
            self.parent.on_diff_accepted(self.modified_text)

    def reject_changes(self):
        """拒绝修改 - 恢复原始文本"""
        cursor = self.editor.textCursor()
        cursor.setPosition(self.original_selection_start)
        cursor.setPosition(
            self.original_selection_start + len(self.modified_text),
            QTextCursor.KeepAnchor,
        )

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(self.original_text)
        cursor.endEditBlock()

        cursor.setPosition(self.original_selection_start)
        self.editor.setTextCursor(cursor)

        self._cleanup()

        if self.parent and hasattr(self.parent, "on_diff_rejected"):
            self.parent.on_diff_rejected()

    def _cleanup(self):
        """清理状态"""
        self._is_showing_diff = False
        self._is_hovering = False
        self.differences = []
        if self.toolbar:
            self.toolbar.hide()

    def hide_toolbar(self):
        """隐藏工具栏"""
        if self.toolbar:
            self.toolbar.hide()

    def cleanup(self):
        """完全清理"""
        self._cleanup()
        self.editor.viewport().removeEventFilter(self)
        if self.toolbar:
            self.toolbar.deleteLater()
            self.toolbar = None


__all__ = ["InlineDiffManager", "DiffHoverToolbar"]
