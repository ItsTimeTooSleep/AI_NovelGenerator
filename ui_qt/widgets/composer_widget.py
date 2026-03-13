# -*- coding: utf-8 -*-
"""
AI Novel Generator - Composer AI交互模块
=========================================

本模块实现了Composer AI的交互功能：
- ComposerInputWidget: AI查询输入组件
- ComposerDiffWidget: 修改可视化组件（显示新增/删除内容）
- 精细化提示词系统
"""

import difflib

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt5.QtGui import QColor, QTextCharFormat
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QToolTip,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    CaptionLabel,
    SubtitleLabel,
    BodyLabel,
)

from ..utils.styles import ThemeManager, isDarkTheme


class ComposerAIWorker(QThread):
    """
    Composer AI工作线程

    负责在后台处理AI请求，避免阻塞UI。
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt, llm_adapter):
        """
        初始化AI工作线程

        Args:
            prompt: 要发送给AI的提示词
            llm_adapter: LLM适配器实例
        """
        super().__init__()
        self.prompt = prompt
        self.llm_adapter = llm_adapter

    def run(self):
        """执行AI请求"""
        try:
            response = self.llm_adapter.invoke(self.prompt)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class ComposerInputWidget(QWidget):
    """
    Composer AI查询输入组件

    提供用户查询AI的输入界面。
    """

    query_submitted = pyqtSignal(str)
    ai_level_changed = pyqtSignal(str)

    def __init__(self, selected_text="", ai_level="standard", parent=None):
        """
        初始化输入组件

        Args:
            selected_text: 选中文本
            ai_level: AI等级 (mini/standard/pro)
            parent: 父控件
        """
        super().__init__(parent)
        self.selected_text = selected_text
        self.ai_level = ai_level
        self.ai_levels = ["mini", "standard", "pro"]

        # 初始高度
        self.min_height = 44
        self.max_height = 150

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        from PyQt5.QtWidgets import QPushButton, QTextEdit

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        is_dark = isDarkTheme()
        # 使用主题统一的颜色
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        border_focus_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        text_primary = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        text_placeholder = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )
        primary = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        text_inverted = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_INVERTED, is_dark
        )

        # 外层容器 - 提供美观的外边框
        self.outer_container = QFrame(self)
        self.outer_container.setObjectName("composerInputOuterContainer")
        self.outer_container.setStyleSheet(f"""
            QFrame#composerInputOuterContainer {{
                background-color: {bg_color};
                border: 2px solid {primary};
                border-radius: 16px;
            }}
        """)

        self.outer_layout = QVBoxLayout(self.outer_container)
        self.outer_layout.setContentsMargins(6, 6, 6, 6)
        self.outer_layout.setSpacing(0)

        # 主容器 - 白色背景、浅灰边框
        self.container = QFrame(self.outer_container)
        self.container.setObjectName("composerInputContainer")
        self.container.setStyleSheet(f"""
            QFrame#composerInputContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 0px;
            }}
            QFrame#composerInputContainer:focus-within {{
                border: 1px solid {border_focus_color};
            }}
        """)

        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)

        # 多行输入框，支持动态高度，占位提示显示快捷键说明
        self.query_input = QTextEdit(self.container)
        self.query_input.setPlaceholderText(
            f'按 "↑↓" 切换模式 (当前: {self.ai_level})，按 "ESC" 关闭'
        )
        self.query_input.setAcceptRichText(False)
        self.query_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.query_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.query_input.setMinimumHeight(self.min_height - 16)  # 减去padding
        self.query_input.setMaximumHeight(self.max_height - 16)
        self.query_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px 0px 0px 4px;
                color: {text_primary};
                font-size: 14px;
                font-family: Consolas, 'Microsoft YaHei', monospace;
            }}
            QTextEdit::placeholder {{
                color: {text_placeholder};
            }}
        """)
        self.container_layout.addWidget(self.query_input, 1)

        # 向上箭头发送按钮，固定在右下角，紫色背景，白色箭头
        self.submit_btn = QPushButton("↑", self.container)
        self.submit_btn.setFixedSize(28, 28)  # 缩小按钮

        # 获取主题颜色
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        primary_dark = ThemeManager.get_color(ThemeManager.Colors.PRIMARY_DARK, is_dark)
        primary_light = ThemeManager.get_color(
            ThemeManager.Colors.PRIMARY_LIGHT, is_dark
        )
        disabled_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )

        self.submit_btn.setStyleSheet(
            "QPushButton {"
            + "background-color: "
            + primary_color
            + ";"
            + "color: #ffffff;"
            + "border: none;"
            + "border-radius: 6px;"
            + "font-size: 16px;"
            + "font-weight: bold;"
            + "padding: 0px;"
            + "padding-bottom: 2px;"
            + "}"
            + "QPushButton:hover {"
            + "background-color: "
            + primary_light
            + ";"
            + "}"
            + "QPushButton:pressed {"
            + "background-color: "
            + primary_dark
            + ";"
            + "}"
            + "QPushButton:disabled {"
            + "background-color: "
            + disabled_color
            + ";"
            + "}"
        )

        # 按钮容器，用于定位
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        self.container_layout.addLayout(button_layout)

        self.outer_layout.addWidget(self.container)
        self.main_layout.addWidget(self.outer_container)

        # 连接信号
        self.submit_btn.clicked.connect(self.on_submit)
        self.query_input.textChanged.connect(self.on_text_changed)

        # 为query_input安装事件过滤器，以便捕获键盘事件
        self.query_input.installEventFilter(self)

        # 初始化时检查文本状态
        self.update_submit_button_state()

        # 设置初始大小
        self.setMinimumWidth(500)
        self.setMaximumWidth(700)
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)

        # 初始化时设置正确的高度（外层边距 6px * 2 + 内层边距 8px * 2）
        initial_container_height = self.min_height
        self.setFixedHeight(initial_container_height + 28)  # 6*2 + 8*2 = 28
        self.outer_container.setFixedHeight(initial_container_height + 28)
        self.container.setFixedHeight(initial_container_height)

    def on_text_changed(self):
        """文本变化时调整高度"""

        # 计算所需高度
        doc = self.query_input.document()
        doc_height = doc.size().height()

        # 计算新高度（加上 padding）
        new_height = int(doc_height) + 16

        # 限制在最小和最大高度之间
        new_height = max(self.min_height, min(new_height, self.max_height))

        # 调整高度（外层边距 6px * 2 + 内层边距 8px * 2 = 28px）
        if new_height != self.container.height():
            self.setFixedHeight(new_height + 28)
            self.outer_container.setFixedHeight(new_height + 28)
            self.container.setFixedHeight(new_height)

        # 更新提交按钮状态
        self.update_submit_button_state()

    def update_submit_button_state(self):
        """更新提交按钮的状态

        根据输入框是否有文本，启用或禁用提交按钮
        """
        text = self.query_input.toPlainText().strip()
        self.submit_btn.setEnabled(bool(text))

    def eventFilter(self, obj, event):
        """
        事件过滤器，用于捕获query_input的键盘事件

        Args:
            obj: 事件目标对象
            event: 事件对象

        Returns:
            bool: 是否拦截事件
        """
        from PyQt5.QtCore import QEvent, Qt

        if obj == self.query_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide()
                return True
            elif event.key() == Qt.Key_Up:
                self.switch_ai_level(1)
                return True
            elif event.key() == Qt.Key_Down:
                self.switch_ai_level(-1)
                return True
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() != Qt.ShiftModifier:
                    self.on_submit()
                    return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """
        键盘事件处理

        Args:
            event: 键盘事件
        """
        from PyQt5.QtCore import Qt

        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Up:
            self.switch_ai_level(1)
        elif event.key() == Qt.Key_Down:
            self.switch_ai_level(-1)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() != Qt.ShiftModifier:
                self.on_submit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def switch_ai_level(self, direction):
        """
        切换AI等级

        Args:
            direction: 切换方向，1表示向上，-1表示向下
        """
        try:
            current_index = self.ai_levels.index(self.ai_level)
            new_index = (current_index + direction) % len(self.ai_levels)
            self.ai_level = self.ai_levels[new_index]
            # 更新placeholder文本显示当前等级
            self.query_input.setPlaceholderText(
                f'按 "↑↓" 切换模式 (当前: {self.ai_level})，按 "ESC" 关闭'
            )
            # 发送ai_level变化信号
            self.ai_level_changed.emit(self.ai_level)
        except ValueError:
            pass

    def on_submit(self):
        """提交查询"""
        query = self.query_input.toPlainText().strip()
        if query:
            self.query_submitted.emit(query)
            self.hide()


class ComposerHintWidget(QWidget):
    """
    Composer提示框组件

    显示操作提示的横向提示框，包含：
    - 左侧文本提示区
    - 右侧功能按钮区
    """

    up_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """
        初始化提示框组件

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(0)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_CARD, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY, is_dark)
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        text_inverted = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_INVERTED, is_dark
        )

        # 主容器
        self.container = QFrame(self)
        self.container.setObjectName("composerHintContainer")
        self.container.setStyleSheet(f"""
            QFrame#composerHintContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 0px;
            }}
        """)

        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 8, 6, 8)
        self.container_layout.setSpacing(8)

        # 左侧文本提示
        self.hint_label = QLabel('按 "↑↓" 切换模式，按 "ESC" 关闭', self.container)
        self.hint_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 13px;
                font-family: Consolas, 'Microsoft YaHei', monospace;
            }}
        """)
        self.container_layout.addWidget(self.hint_label)

        self.container_layout.addStretch()

        # 右侧向上箭头按钮
        self.up_button = QPushButton("↑", self.container)
        self.up_button.setFixedSize(28, 28)
        self.up_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_color};
                color: {text_inverted};
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color(ThemeManager.Colors.PRIMARY_LIGHT, is_dark)};
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.get_color(ThemeManager.Colors.PRIMARY_DARK, is_dark)};
            }}
        """)
        self.up_button.clicked.connect(self.on_up_button_clicked)
        self.container_layout.addWidget(self.up_button)

        self.main_layout.addWidget(self.container)

        # 设置固定高度，让它看起来像一个横向提示条
        self.setFixedHeight(44)

    def on_up_button_clicked(self):
        """向上按钮点击事件"""
        self.up_button_clicked.emit()


class ComposerDiffWidget(QWidget):
    """
    Composer修改可视化组件（美化版）

    显示AI修改的内容，用柔和红色标记删除的内容，柔和绿色标记新增的内容。
    支持逐处修改的悬停确认功能和流式更新。
    """

    changes_accepted = pyqtSignal(str)
    changes_rejected = pyqtSignal()

    def __init__(self, original_text, modified_text="", parent=None):
        """
        初始化差异显示组件

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本（可选，支持流式更新）
            parent: 父控件
        """
        super().__init__(parent)
        self.original_text = original_text
        self.modified_text = modified_text
        self.differences = []  # 存储差异信息
        self.init_ui()
        if modified_text:
            self.display_diff()

    def init_ui(self):
        """初始化用户界面"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_CARD, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_primary = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        text_secondary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_SECONDARY, is_dark
        )
        text_tertiary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        primary_light = ThemeManager.get_color(
            ThemeManager.Colors.PRIMARY_LIGHT, is_dark
        )

        # 外层容器 - 毛玻璃效果边框
        self.container = QFrame(self)
        self.container.setObjectName("composerDiffContainer")
        self.container.setStyleSheet(f"""
            QFrame#composerDiffContainer {{
                background-color: {bg_color};
                border: 2px solid {primary_color};
                border-radius: 16px;
            }}
        """)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(16)
        self.container_layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.title_label = SubtitleLabel("AI 修改预览", title_widget)
        self.title_label.setStyleSheet(f"""
            color: {primary_color};
            font-size: 20px;
            font-weight: 700;
        """)

        self.subtitle_label = CaptionLabel("发现以下修改建议", title_widget)
        self.subtitle_label.setStyleSheet(f"""
            color: {text_secondary};
            font-size: 13px;
        """)

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        self.container_layout.addWidget(title_widget)

        # 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"""
            QFrame {{
                background-color: {border_color};
                height: 1px;
            }}
        """)
        self.container_layout.addWidget(divider)

        # 内容区域 - 单页显示差异（更简洁）
        self.diff_scroll = QScrollArea()
        self.diff_scroll.setWidgetResizable(True)
        self.diff_scroll.setFrameShape(QFrame.NoFrame)
        self.diff_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeManager.get_color(ThemeManager.Colors.SCROLLBAR_HANDLE, is_dark)};
                min-height: 24px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeManager.get_color(ThemeManager.Colors.SCROLLBAR_HANDLE_HOVER, is_dark)};
            }}
        """)

        self.diff_content = QTextEdit()
        self.diff_content.setReadOnly(True)
        self.diff_content.setMouseTracking(True)
        self.diff_content.installEventFilter(self)
        self.diff_content.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                padding: 16px;
                color: {text_primary};
                font-size: 15px;
                font-family: 'Microsoft YaHei', sans-serif;
                line-height: 1.8;
            }}
        """)

        self.diff_scroll.setWidget(self.diff_content)
        self.container_layout.addWidget(self.diff_scroll, 1)

        # 底部操作区域
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background-color: transparent;")
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(12)

        # 提示信息
        hint_label = CaptionLabel(
            "💡 提示：红色删除线表示移除的内容，绿色高亮表示新增的内容", footer_widget
        )
        hint_label.setStyleSheet(f"""
            color: {text_tertiary};
            font-size: 12px;
            padding: 8px 12px;
            background-color: {ThemeManager.get_color(ThemeManager.Colors.BG_OVERLAY, is_dark)};
            border-radius: 8px;
        """)
        footer_layout.addWidget(hint_label)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.reject_btn = PushButton("取消", footer_widget)
        self.reject_btn.setMinimumWidth(100)

        self.accept_btn = PrimaryPushButton("确认更改", footer_widget)
        self.accept_btn.setMinimumWidth(120)

        button_layout.addStretch()
        button_layout.addWidget(self.reject_btn)
        button_layout.addWidget(self.accept_btn)
        footer_layout.addLayout(button_layout)

        self.container_layout.addWidget(footer_widget)
        self.main_layout.addWidget(self.container)

        # 连接信号
        self.reject_btn.clicked.connect(self.on_reject)
        self.accept_btn.clicked.connect(self.on_accept)

        # 设置合适的大小，允许调整
        self.setMinimumSize(650, 550)
        self.resize(750, 650)

    def display_diff(self):
        """显示原始文本和修改文本的差异"""
        differ = difflib.SequenceMatcher(None, self.original_text, self.modified_text)

        is_dark = isDarkTheme()

        # 先清空文本编辑器内容，避免重复追加
        self.diff_content.clear()

        cursor = self.diff_content.textCursor()
        format = QTextCharFormat()

        # 清空差异列表
        self.differences = []
        diff_index = 0

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            start_pos = cursor.position()

            if tag == "equal":
                format.setForeground(
                    QColor(
                        ThemeManager.get_color(
                            ThemeManager.Colors.TEXT_PRIMARY, is_dark
                        )
                    )
                )
                format.setBackground(QColor("transparent"))
                format.setFontStrikeOut(False)
                cursor.insertText(self.modified_text[j1:j2], format)

            elif tag == "delete":
                # 柔和红色删除线 - 使用主题统一的颜色
                error_color = ThemeManager.get_color(ThemeManager.Colors.ERROR, is_dark)
                error_bg = ThemeManager.get_color(ThemeManager.Colors.ERROR_BG, is_dark)
                format.setForeground(QColor(error_color))
                format.setBackground(QColor(error_bg))
                format.setFontStrikeOut(True)
                text = self.original_text[i1:i2]
                cursor.insertText(text, format)

                # 记录差异位置
                end_pos = cursor.position()
                self.differences.append(
                    {
                        "type": "delete",
                        "start": start_pos,
                        "end": end_pos,
                        "original": text,
                        "modified": "",
                    }
                )
                diff_index += 1
                format.setFontStrikeOut(False)

            elif tag == "insert":
                # 柔和绿色高亮 - 使用主题统一的颜色
                success_color = ThemeManager.get_color(
                    ThemeManager.Colors.SUCCESS, is_dark
                )
                success_bg = ThemeManager.get_color(
                    ThemeManager.Colors.SUCCESS_BG, is_dark
                )
                format.setForeground(QColor(success_color))
                format.setBackground(QColor(success_bg))
                format.setFontStrikeOut(False)
                text = self.modified_text[j1:j2]
                cursor.insertText(text, format)

                # 记录差异位置
                end_pos = cursor.position()
                self.differences.append(
                    {
                        "type": "insert",
                        "start": start_pos,
                        "end": end_pos,
                        "original": "",
                        "modified": text,
                    }
                )
                diff_index += 1

            elif tag == "replace":
                # 先显示删除部分（红色删除线）
                error_color = ThemeManager.get_color(ThemeManager.Colors.ERROR, is_dark)
                error_bg = ThemeManager.get_color(ThemeManager.Colors.ERROR_BG, is_dark)
                format.setForeground(QColor(error_color))
                format.setBackground(QColor(error_bg))
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
                    }
                )
                diff_index += 1

                # 再显示插入部分（绿色高亮）
                success_color = ThemeManager.get_color(
                    ThemeManager.Colors.SUCCESS, is_dark
                )
                success_bg = ThemeManager.get_color(
                    ThemeManager.Colors.SUCCESS_BG, is_dark
                )
                format.setForeground(QColor(success_color))
                format.setBackground(QColor(success_bg))
                format.setFontStrikeOut(False)
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
                    }
                )
                diff_index += 1

    def eventFilter(self, obj, event):
        """事件过滤器"""
        return super().eventFilter(obj, event)

    def on_accept(self):
        """确认修改"""
        self.changes_accepted.emit(self.modified_text)
        self.hide()

    def on_reject(self):
        """拒绝修改"""
        self.changes_rejected.emit()
        self.hide()

    def append_content(self, content: str):
        """
        追加内容到修改后的文本并更新显示（用于流式传输）

        Args:
            content: 要追加的内容
        """
        self.modified_text += content
        self.display_diff()

    def set_modified_text(self, text: str):
        """
        设置修改后的文本并更新显示（用于流式传输）

        Args:
            text: 完整的修改后文本
        """
        self.modified_text = text
        self.display_diff()


class ComposerResponseWidget(QWidget):
    """
    Composer AI回答显示组件

    显示AI的纯文本回答，支持继续追问功能。
    用于query任务类型，当AI返回纯文本回答而非修改建议时使用。
    """

    follow_up_submitted = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, response: str, parent=None):
        """
        初始化回答显示组件

        Args:
            response: AI的回答内容
            parent: 父控件
        """
        super().__init__(parent)
        self.response = response
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_CARD, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_primary = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        text_secondary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_SECONDARY, is_dark
        )
        text_tertiary = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        primary_light = ThemeManager.get_color(
            ThemeManager.Colors.PRIMARY_LIGHT, is_dark
        )
        primary_dark = ThemeManager.get_color(ThemeManager.Colors.PRIMARY_DARK, is_dark)

        self.container = QFrame(self)
        self.container.setObjectName("composerResponseContainer")
        self.container.setStyleSheet(f"""
            QFrame#composerResponseContainer {{
                background-color: {bg_color};
                border: 2px solid {primary_color};
                border-radius: 16px;
            }}
        """)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(16)
        self.container_layout.setContentsMargins(20, 20, 20, 20)

        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        self.title_label = SubtitleLabel("💬 Composer 回答", title_widget)
        self.title_label.setStyleSheet(f"""
            color: {primary_color};
            font-size: 20px;
            font-weight: 700;
        """)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.copy_btn = PushButton("复制", title_widget)
        self.copy_btn.setFixedSize(60, 28)
        self.copy_btn.clicked.connect(self.on_copy)
        title_layout.addWidget(self.copy_btn)

        self.container_layout.addWidget(title_widget)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"""
            QFrame {{
                background-color: {border_color};
                height: 1px;
            }}
        """)
        self.container_layout.addWidget(divider)

        self.response_scroll = QScrollArea()
        self.response_scroll.setWidgetResizable(True)
        self.response_scroll.setFrameShape(QFrame.NoFrame)
        self.response_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeManager.get_color(ThemeManager.Colors.SCROLLBAR_HANDLE, is_dark)};
                min-height: 24px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeManager.get_color(ThemeManager.Colors.SCROLLBAR_HANDLE_HOVER, is_dark)};
            }}
        """)

        self.response_content = QTextEdit()
        self.response_content.setReadOnly(True)
        self.response_content.setPlainText(self.response)
        self.response_content.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                padding: 16px;
                color: {text_primary};
                font-size: 15px;
                font-family: 'Microsoft YaHei', sans-serif;
                line-height: 1.8;
            }}
        """)

        self.response_scroll.setWidget(self.response_content)
        self.container_layout.addWidget(self.response_scroll, 1)

        self.follow_up_widget = QWidget()
        follow_up_layout = QVBoxLayout(self.follow_up_widget)
        follow_up_layout.setContentsMargins(0, 0, 0, 0)
        follow_up_layout.setSpacing(8)

        self.follow_up_input = QTextEdit()
        self.follow_up_input.setPlaceholderText(
            "继续追问... (按 Enter 发送，Shift+Enter 换行)"
        )
        self.follow_up_input.setAcceptRichText(False)
        self.follow_up_input.setMaximumHeight(80)
        self.follow_up_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px;
                color: {text_primary};
                font-size: 14px;
            }}
            QTextEdit::placeholder {{
                color: {text_tertiary};
            }}
        """)
        self.follow_up_input.installEventFilter(self)
        follow_up_layout.addWidget(self.follow_up_input)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.close_btn = PushButton("关闭", self.follow_up_widget)
        self.close_btn.setMinimumWidth(80)

        self.follow_up_btn = PrimaryPushButton("继续追问", self.follow_up_widget)
        self.follow_up_btn.setMinimumWidth(100)
        self.follow_up_btn.setEnabled(False)

        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        button_layout.addWidget(self.follow_up_btn)
        follow_up_layout.addLayout(button_layout)

        self.container_layout.addWidget(self.follow_up_widget)
        self.main_layout.addWidget(self.container)

        self.close_btn.clicked.connect(self.on_close)
        self.follow_up_btn.clicked.connect(self.on_follow_up)
        self.follow_up_input.textChanged.connect(self._on_follow_up_text_changed)

        self.setMinimumSize(600, 500)
        self.resize(700, 600)

    def eventFilter(self, obj, event):
        """
        事件过滤器，用于捕获键盘事件

        Args:
            obj: 事件目标对象
            event: 事件对象

        Returns:
            bool: 是否拦截事件
        """
        if obj == self.follow_up_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() != Qt.ShiftModifier:
                    self.on_follow_up()
                    return True
        return super().eventFilter(obj, event)

    def on_copy(self):
        """复制回答内容到剪贴板"""
        from PyQt5.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self.response)
        self.copy_btn.setText("已复制")
        from PyQt5.QtCore import QTimer

        QTimer.singleShot(1500, lambda: self.copy_btn.setText("复制"))

    def on_follow_up(self):
        """提交追问"""
        query = self.follow_up_input.toPlainText().strip()
        if query:
            self.follow_up_submitted.emit(query)
            self.hide()

    def on_close(self):
        """关闭窗口"""
        self.closed.emit()
        self.hide()

    def _on_follow_up_text_changed(self):
        """
        追问输入框文本变化时更新按钮状态

        根据输入框是否有内容，启用或禁用继续追问按钮
        """
        text = self.follow_up_input.toPlainText().strip()
        self.follow_up_btn.setEnabled(bool(text))

    def append_response(self, new_response: str):
        """
        追加新的回答内容（用于多轮对话）

        Args:
            new_response: 新的回答内容
        """
        self.response += "\n\n" + new_response
        self.response_content.setPlainText(self.response)

    def set_response(self, response: str):
        """
        设置回答内容

        Args:
            response: 回答内容
        """
        self.response = response
        self.response_content.setPlainText(response)
