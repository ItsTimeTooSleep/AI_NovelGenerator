# ui_qt/directory_tab.py
# -*- coding: utf-8 -*-
"""
目录结构 Tab
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


class DirectoryInterface(BaseProjectInterface):
    """
    目录结构界面

    Args:
        parent: 父控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        self.card = CardWidget(self.view)
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setContentsMargins(16, 16, 16, 16)
        self.cardLayout.setSpacing(12)

        self.editorStack = QStackedWidget(self.card)
        self.cardLayout.addWidget(self.editorStack)

        self.editor = PlainTextEdit(self.editorStack)
        self.editor.setStyleSheet(Styles.PlainTextEdit)
        self.editorStack.addWidget(self.editor)

        self.placeholderContainer = QWidget(self.editorStack)
        self.placeholderLayout = QVBoxLayout(self.placeholderContainer)
        self.placeholderLayout.setContentsMargins(0, 0, 0, 0)
        self.editorPlaceholder = None
        self.editorStack.addWidget(self.placeholderContainer)

        self.vBoxLayout.addWidget(self.card)

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save)

        self.editor_toolkit = EditorToolkit(self)
        self.editor_toolkit.add_editor(
            "main", self.editor, self.on_editor_selection_changed
        )
        self.editor_toolkit.init_shortcuts()

        self._setup_editor_toolkit_handlers()

        self.editor.textChanged.connect(self.on_text_changed)

        self.load_directory()

    def _setup_editor_toolkit_handlers(self):
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
        self.editor_toolkit.set_active_editor(editor_key)
        self.editor_toolkit.context_menu_manager.on_selection_changed(editor_key)

    def _on_copy(self):
        self.editor.copy()

    def _on_paste(self):
        self.editor.paste()

    def _on_fix_grammar(self, text):
        self.editor_toolkit.composer_manager.process_ai_task("grammar", text)

    def _on_polish(self, text):
        self.editor_toolkit.composer_manager.process_ai_task("polish", text)

    def _on_expand(self, text, expand_type):
        self.editor_toolkit.composer_manager.process_ai_task(
            "expand", text, expand_type
        )

    def _on_ask_composer(self, text):
        self.editor_toolkit.composer_manager.ask_composer(text)

    def _process_ai_task(self, task_type: str, text: str, extra_param: str = ""):
        self.editor_toolkit.composer_manager.process_ai_task(
            task_type, text, extra_param
        )

    def _apply_changes(self, modified_text: str):
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
        self.auto_save_timer.start(1500)

    def auto_save(self):
        if (
            hasattr(self, "current_file")
            and self.current_file
            and os.path.exists(self.current_file)
        ):
            content = self.editor.toPlainText()
            save_string_to_txt(content, self.current_file)
            self.show_save_toast()

    def show_save_toast(self):
        now = datetime.now().strftime("%H:%M:%S")
        notify = get_global_notify()
        if notify:
            notify.success("", f"{now} 已保存")

    def load_directory(self):
        if self.editorPlaceholder:
            self.editorPlaceholder.deleteLater()
            self.editorPlaceholder = None

        filepath = self.get_filepath()

        if filepath:
            self.editor_toolkit.set_project_path(filepath)

        if not filepath:
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

        target_file = os.path.join(filepath, "Novel_directory.txt")
        if not os.path.exists(target_file):
            target_file = os.path.join(filepath, "Novel_blueprint.txt")

        if os.path.exists(target_file):
            try:
                content = read_file(target_file)
                if content.strip():
                    self.editor.setPlainText(content)
                    self.editor.setReadOnly(False)
                    self.editorStack.setCurrentWidget(self.editor)
                    self.current_file = target_file
                else:
                    empty_state = EmptyState.directory()
                    empty_state["description"] = (
                        "目录文件存在但内容为空，请在「生成台」中重新执行 Step 2。"
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
                empty_state = EmptyState.directory()
                empty_state["description"] = (
                    "读取目录文件失败，请在「生成台」中重新执行 Step 2。"
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
            empty_state = EmptyState.directory()
            self.editorPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.placeholderContainer,
            )
            self.placeholderLayout.addWidget(self.editorPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
            self.current_file = None


__all__ = ["DirectoryInterface"]
