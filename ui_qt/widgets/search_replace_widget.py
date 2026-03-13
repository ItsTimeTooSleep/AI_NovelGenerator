# -*- coding: utf-8 -*-
"""
AI Novel Generator - 搜索与替换模块
=====================================

本模块实现了文本编辑器的搜索与替换功能组件：
- SearchReplaceWidget: 搜索替换悬浮窗口
- 支持模糊匹配、区分大小写、全字匹配
- 支持上一个/下一个导航
- 支持替换和全部替换
"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QTextCursor, QTextDocument
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import LineEdit, PushButton, ToolButton, isDarkTheme

from ..utils.styles import Styles, ThemeManager


class SearchReplaceWidget(QWidget):
    """
    搜索替换悬浮窗口组件

    提供文本搜索和替换功能，支持：
    - 模糊匹配
    - 区分大小写
    - 全字匹配
    - 上一个/下一个导航
    - 替换和全部替换
    """

    closed = pyqtSignal()

    def __init__(self, editor, parent=None):
        """
        初始化搜索替换窗口

        Args:
            editor: 关联的文本编辑器 (QPlainTextEdit)
            parent: 父控件
        """
        super().__init__(parent)
        self.editor = editor
        self.current_match_index = -1
        self.matches = []

        self.setObjectName("searchReplaceWidget")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """初始化用户界面"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # 主容器卡片
        self.container = QFrame(self)
        self.container.setObjectName("searchContainer")

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )

        self.container.setStyleSheet(f"""
            QFrame#searchContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 12px;
            }}
        """)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(8)

        # 第一行：搜索输入和关闭按钮
        self.search_row = QHBoxLayout()

        self.search_input = LineEdit(self.container)
        self.search_input.setPlaceholderText("搜索...")
        self.search_input.setClearButtonEnabled(True)

        self.close_btn = ToolButton(FIF.CLOSE, self.container)
        self.close_btn.setFixedSize(28, 28)

        self.search_row.addWidget(self.search_input)
        self.search_row.addWidget(self.close_btn)

        self.container_layout.addLayout(self.search_row)

        # 第二行：替换输入和替换按钮
        self.replace_row = QHBoxLayout()

        self.replace_input = LineEdit(self.container)
        self.replace_input.setPlaceholderText("替换为...")

        self.replace_btn = PushButton("替换", self.container)
        self.replace_btn.setFixedWidth(70)

        self.replace_all_btn = PushButton("全部替换", self.container)
        self.replace_all_btn.setFixedWidth(80)

        self.replace_row.addWidget(self.replace_input)
        self.replace_row.addWidget(self.replace_btn)
        self.replace_row.addWidget(self.replace_all_btn)

        self.container_layout.addLayout(self.replace_row)

        # 第三行：导航按钮和计数
        self.nav_row = QHBoxLayout()

        self.prev_btn = ToolButton(FIF.UP, self.container)
        self.prev_btn.setFixedSize(28, 28)

        self.next_btn = ToolButton(FIF.DOWN, self.container)
        self.next_btn.setFixedSize(28, 28)

        self.count_label = QLabel("0/0", self.container)
        self.count_label.setStyleSheet(Styles.HintText + " font-size: 12px;")

        self.nav_row.addWidget(self.prev_btn)
        self.nav_row.addWidget(self.next_btn)
        self.nav_row.addWidget(self.count_label)
        self.nav_row.addStretch()

        self.container_layout.addLayout(self.nav_row)

        # 第四行：高级选项
        self.options_row = QHBoxLayout()

        self.case_sensitive = QCheckBox("区分大小写", self.container)
        self.case_sensitive.setStyleSheet(Styles.SecondaryText)

        self.whole_word = QCheckBox("全字匹配", self.container)
        self.whole_word.setStyleSheet(Styles.SecondaryText)

        self.options_row.addWidget(self.case_sensitive)
        self.options_row.addWidget(self.whole_word)
        self.options_row.addStretch()

        self.container_layout.addLayout(self.options_row)

        self.main_layout.addWidget(self.container)

        # 设置固定宽度
        self.setFixedWidth(380)

    def connect_signals(self):
        """连接信号和槽"""
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_next)

        self.prev_btn.clicked.connect(self.on_prev)
        self.next_btn.clicked.connect(self.on_next)

        self.replace_btn.clicked.connect(self.on_replace)
        self.replace_all_btn.clicked.connect(self.on_replace_all)

        self.close_btn.clicked.connect(self.hide)

        self.case_sensitive.stateChanged.connect(self.on_search_text_changed)
        self.whole_word.stateChanged.connect(self.on_search_text_changed)

    def show_at_position(self, pos):
        """
        在指定位置显示搜索窗口

        Args:
            pos: 显示位置 (QPoint)
        """
        self.move(pos)
        self.show()
        self.search_input.setFocus()
        if self.search_input.text():
            self.perform_search()

    def keyPressEvent(self, event):
        """
        键盘事件处理

        Args:
            event: 键盘事件
        """
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def on_search_text_changed(self):
        """搜索文本变化时触发"""
        self.perform_search()

    def perform_search(self):
        """执行搜索并高亮匹配项"""
        search_text = self.search_input.text()
        if not search_text:
            self.clear_highlights()
            self.count_label.setText("0/0")
            self.current_match_index = -1
            self.matches = []
            return

        # 构建搜索标志
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word.isChecked():
            flags |= QTextDocument.FindWholeWords

        # 查找所有匹配
        self.matches = []
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        # 清除之前的高亮
        self.clear_highlights()

        # 从头开始搜索
        cursor.setPosition(0)
        document = self.editor.document()

        while True:
            cursor = document.find(search_text, cursor, flags)
            if cursor.isNull():
                break
            self.matches.append((cursor.selectionStart(), cursor.selectionEnd()))
            # 移动游标到匹配之后
            cursor.setPosition(cursor.selectionEnd())

        cursor.endEditBlock()

        # 更新计数
        total = len(self.matches)
        self.count_label.setText(f"0/{total}" if total > 0 else "0/0")

        # 如果有匹配，高亮第一个
        if self.matches:
            self.current_match_index = 0
            self.highlight_current_match()

    def clear_highlights(self):
        """清除所有高亮"""
        # 使用ExtraSelections来清除高亮
        self.editor.setExtraSelections([])

    def highlight_current_match(self):
        """高亮当前匹配项"""
        if not self.matches or self.current_match_index < 0:
            return

        selections = []
        is_dark = isDarkTheme()

        # 高亮所有匹配（背景色）
        for i, (start, end) in enumerate(self.matches):
            cursor = QTextCursor(self.editor.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor

            if i == self.current_match_index:
                # 当前匹配用更明显的颜色
                bg_color = QColor(
                    ThemeManager.get_color(
                        ThemeManager.Colors.SEARCH_MATCH_CURRENT_BG, is_dark
                    )
                )
                fg_color = QColor(
                    ThemeManager.get_color(ThemeManager.Colors.SEARCH_MATCH_FG, is_dark)
                )
                selection.format.setBackground(bg_color)
                selection.format.setForeground(fg_color)
            else:
                # 其他匹配用淡色
                bg_color = QColor(
                    ThemeManager.get_color(ThemeManager.Colors.SEARCH_MATCH_BG, is_dark)
                )
                selection.format.setBackground(bg_color)

            selections.append(selection)

        self.editor.setExtraSelections(selections)

        # 滚动到当前匹配
        if self.matches:
            start, _ = self.matches[self.current_match_index]
            cursor = QTextCursor(self.editor.document())
            cursor.setPosition(start)
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()

        # 更新计数
        total = len(self.matches)
        current = self.current_match_index + 1 if total > 0 else 0
        self.count_label.setText(f"{current}/{total}")

    def on_prev(self):
        """上一个匹配"""
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index - 1) % len(self.matches)
        self.highlight_current_match()

    def on_next(self):
        """下一个匹配"""
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index + 1) % len(self.matches)
        self.highlight_current_match()

    def on_replace(self):
        """替换当前匹配"""
        if not self.matches or self.current_match_index < 0:
            return

        replace_text = self.replace_input.text()
        start, end = self.matches[self.current_match_index]

        cursor = QTextCursor(self.editor.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.insertText(replace_text)

        # 重新搜索
        self.perform_search()

    def on_replace_all(self):
        """全部替换"""
        if not self.matches:
            return

        replace_text = self.replace_input.text()

        # 从后往前替换，避免索引变化问题
        cursor = QTextCursor(self.editor.document())
        cursor.beginEditBlock()

        for start, end in reversed(self.matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.insertText(replace_text)

        cursor.endEditBlock()

        # 重新搜索
        self.perform_search()

    def hideEvent(self, event):
        """
        隐藏事件处理

        Args:
            event: 隐藏事件
        """
        self.clear_highlights()
        self.closed.emit()
        super().hideEvent(event)

    def focusOutEvent(self, event):
        """
        失去焦点时检查是否需要隐藏

        Args:
            event: 焦点事件
        """
        # 延迟隐藏，给按钮点击留出时间
        QTimer.singleShot(200, self.check_focus)

    def check_focus(self):
        """检查是否还需要保持焦点"""
        if (
            not self.hasFocus()
            and not self.search_input.hasFocus()
            and not self.replace_input.hasFocus()
            and not self.isAncestorOf(self.focusWidget())
        ):
            pass  # 不自动隐藏，让用户手动关闭
