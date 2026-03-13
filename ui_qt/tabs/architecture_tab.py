# ui_qt/architecture_tab.py
# -*- coding: utf-8 -*-
"""
小说架构 Tab
"""

from datetime import datetime
import os

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import CardWidget, PlainTextEdit

from core.utils import read_file, save_string_to_txt
from ui_qt.utils.helpers import get_global_notify

from ..utils.editor_toolkit import EditorToolkit
from ..utils.helpers import BaseProjectInterface
from ..utils.styles import Styles
from ..widgets.placeholder_widget import EmptyState, PlaceholderWidget


class ArchitectureInterface(BaseProjectInterface):
    """
    小说架构界面

    Args:
        parent: 父控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 更紧凑的布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        # 卡片容器
        self.card = CardWidget(self.view)
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setContentsMargins(16, 16, 16, 16)
        self.cardLayout.setSpacing(12)

        # 编辑器容器（使用 StackedWidget 切换编辑器和占位符）
        self.editorStack = QStackedWidget(self.card)
        self.cardLayout.addWidget(self.editorStack)

        # 编辑器
        self.editor = PlainTextEdit(self.editorStack)
        self.editor.setStyleSheet(Styles.PlainTextEdit)
        self.editorStack.addWidget(self.editor)

        # 占位符容器
        self.placeholderContainer = QWidget(self.editorStack)
        self.placeholderLayout = QVBoxLayout(self.placeholderContainer)
        self.placeholderLayout.setContentsMargins(0, 0, 0, 0)
        self.editorPlaceholder = None
        self.editorStack.addWidget(self.placeholderContainer)

        self.vBoxLayout.addWidget(self.card)

        # 自动保存定时器
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save)

        # 初始化编辑工具包
        self.editor_toolkit = EditorToolkit(self)
        self.editor_toolkit.add_editor(
            "main", self.editor, self.on_editor_selection_changed
        )
        self.editor_toolkit.init_shortcuts()

        # 设置编辑工具包的回调
        self._setup_editor_toolkit_handlers()

        # 连接文本变化信号
        self.editor.textChanged.connect(self.on_text_changed)

        self.load_architecture()

    def _setup_editor_toolkit_handlers(self):
        """设置编辑工具包的回调函数"""
        context_menu_handlers = {
            "on_copy": self._on_copy,
            "on_paste": self._on_paste,
            "on_fix_grammar": self._on_fix_grammar,
            "on_polish": self._on_polish,
            "on_expand": self._on_expand,
            "on_ask_composer": self._on_ask_composer,
        }
        self.editor_toolkit.set_context_menu_handlers(context_menu_handlers)

        composer_handlers = {
            "on_process_task": self._process_ai_task,
            "on_apply_changes": self._apply_changes,
        }
        self.editor_toolkit.set_composer_handlers(composer_handlers)

    def on_editor_selection_changed(self, editor_key: str):
        """编辑器选择变化时的回调"""
        self.editor_toolkit.set_active_editor(editor_key)
        self.editor_toolkit.context_menu_manager.on_selection_changed(editor_key)

    def _on_copy(self):
        """复制按钮点击"""
        self.editor.copy()

    def _on_paste(self):
        """粘贴按钮点击"""
        self.editor.paste()

    def _on_fix_grammar(self, text):
        """修复语法按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task("grammar", text)

    def _on_polish(self, text):
        """润色按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task("polish", text)

    def _on_expand(self, text, expand_type):
        """扩展描写按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task(
            "expand", text, expand_type
        )

    def _on_ask_composer(self, text):
        """询问Composer按钮点击"""
        self.editor_toolkit.composer_manager.ask_composer(text)

    def _process_ai_task(self, task_type: str, text: str, extra_param: str = ""):
        """处理 AI 任务"""
        self.editor_toolkit.composer_manager.process_ai_task(
            task_type, text, extra_param
        )

    def _apply_changes(self, modified_text: str):
        """应用修改到编辑器"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(modified_text)
            cursor.endEditBlock()
            notify = get_global_notify()
            if notify:
                notify.success("", "修改已应用")

    def on_text_changed(self):
        """文本变化时重置自动保存定时器"""
        self.auto_save_timer.start(1500)

    def auto_save(self):
        """自动保存"""
        if (
            hasattr(self, "current_file")
            and self.current_file
            and os.path.exists(self.current_file)
        ):
            content = self.editor.toPlainText()
            save_string_to_txt(content, self.current_file)
            self.show_save_toast()

    def show_save_toast(self):
        """显示保存提示"""
        now = datetime.now().strftime("%H:%M:%S")
        notify = get_global_notify()
        if notify:
            notify.success("", f"{now} 已保存")

    def load_architecture(self):
        """加载小说架构"""
        # 移除旧的占位符
        if self.editorPlaceholder:
            self.editorPlaceholder.deleteLater()
            self.editorPlaceholder = None

        filepath = self.get_filepath()

        # 更新编辑工具包的项目路径
        if filepath:
            self.editor_toolkit.set_project_path(filepath)

        if not filepath:
            # 显示未选择项目占位符
            empty_state = EmptyState.no_project()
            self.editorPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.placeholderContainer,
            )
            self.placeholderLayout.addWidget(self.editorPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
            self.current_file = None
            return

        target_file = os.path.join(filepath, "Novel_architecture.txt")

        if os.path.exists(target_file):
            try:
                content = read_file(target_file)
                if content.strip():
                    self.editor.setPlainText(content)
                    self.editor.setReadOnly(False)
                    self.editorStack.setCurrentWidget(self.editor)
                    self.current_file = target_file
                else:
                    # 显示架构占位符
                    empty_state = EmptyState.architecture()
                    empty_state["description"] = (
                        "架构文件存在但内容为空，请在「生成台」中重新执行 Step 1。"
                    )
                    self.editorPlaceholder = PlaceholderWidget(
                        empty_state["icon"],
                        empty_state["title"],
                        empty_state["description"],
                        self.placeholderContainer,
                    )
                    self.placeholderLayout.addWidget(self.editorPlaceholder)
                    self.editorStack.setCurrentWidget(self.placeholderContainer)
                    self.current_file = target_file
            except Exception:
                # 显示架构占位符
                empty_state = EmptyState.architecture()
                empty_state["description"] = (
                    "读取架构文件失败，请在「生成台」中重新执行 Step 1。"
                )
                self.editorPlaceholder = PlaceholderWidget(
                    empty_state["icon"],
                    empty_state["title"],
                    empty_state["description"],
                    self.placeholderContainer,
                )
                self.placeholderLayout.addWidget(self.editorPlaceholder)
                self.editorStack.setCurrentWidget(self.placeholderContainer)
                self.current_file = target_file
        else:
            # 显示架构占位符
            empty_state = EmptyState.architecture()
            self.editorPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.placeholderContainer,
            )
            self.placeholderLayout.addWidget(self.editorPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
            self.current_file = None


__all__ = ["ArchitectureInterface"]
