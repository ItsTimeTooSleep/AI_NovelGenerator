# ui_qt/character_tab.py
# -*- coding: utf-8 -*-
"""
角色状态 Tab
"""

from datetime import datetime
import os
import re

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import CardWidget, PlainTextEdit

from core.utils import read_file, save_string_to_txt
from ui_qt.utils.helpers import get_global_notify

from ..utils.editor_toolkit import EditorToolkit
from ..utils.helpers import BaseProjectInterface
from ..utils.styles import Styles
from ..widgets.placeholder_widget import EmptyState, PlaceholderWidget


class RolesInterface(BaseProjectInterface):
    """
    角色状态界面

    Args:
        parent: 父控件
    """

    CHARACTER_STATE_FILE = "character_state.txt"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        self.card = CardWidget(self.view)
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setContentsMargins(12, 12, 12, 12)
        self.cardLayout.setSpacing(12)

        self.splitter = QSplitter(Qt.Horizontal)

        self.rolesListContainer = QWidget()
        self.rolesListLayout = QVBoxLayout(self.rolesListContainer)
        self.rolesListLayout.setContentsMargins(0, 0, 0, 0)

        self.rolesList = QListWidget(self.rolesListContainer)
        self.rolesList.setStyleSheet(Styles.QListWidget)
        self.rolesList.setMinimumWidth(180)

        self.rolesPlaceholder = None

        self.rolesListLayout.addWidget(self.rolesList)
        self.splitter.addWidget(self.rolesListContainer)

        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(10)

        self.editorStack = QStackedWidget(self.rightWidget)
        self.rightLayout.addWidget(self.editorStack)

        self.roleEditor = PlainTextEdit(self.editorStack)
        self.roleEditor.setStyleSheet(Styles.PlainTextEdit)
        self.editorStack.addWidget(self.roleEditor)

        self.placeholderContainer = QWidget(self.editorStack)
        self.placeholderLayout = QVBoxLayout(self.placeholderContainer)
        self.placeholderLayout.setContentsMargins(0, 0, 0, 0)
        self.editorPlaceholder = None
        self.editorStack.addWidget(self.placeholderContainer)

        self.splitter.addWidget(self.rightWidget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        self.cardLayout.addWidget(self.splitter)
        self.vBoxLayout.addWidget(self.card)

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save)

        self.editor_toolkit = EditorToolkit(self)
        self.editor_toolkit.add_editor(
            "role", self.roleEditor, self.on_editor_selection_changed
        )
        self.editor_toolkit.init_shortcuts()

        self._setup_editor_toolkit_handlers()

        self.rolesList.itemClicked.connect(self.on_role_selected)
        self.roleEditor.textChanged.connect(self.on_text_changed)

        self.character_state_content = ""
        self.character_blocks = {}
        self.current_role_name = None

        self.load_roles()

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
        self.roleEditor.copy()

    def _on_paste(self):
        self.roleEditor.paste()

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
        cursor = self.roleEditor.textCursor()
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
        filepath = self.get_filepath()
        if filepath and self.current_role_name:
            edited_content = self.roleEditor.toPlainText()
            self.character_blocks[self.current_role_name] = edited_content
            full_content = self._rebuild_full_content()
            character_state_file = os.path.join(filepath, self.CHARACTER_STATE_FILE)
            save_string_to_txt(full_content, character_state_file)
            self.character_state_content = full_content
            self.show_save_toast()

    def show_save_toast(self):
        now = datetime.now().strftime("%H:%M:%S")
        notify = get_global_notify()
        if notify:
            notify.success("", f"{now} 已保存")

    def _parse_character_state(self, content: str) -> dict:
        """
        解析 character_state.txt 内容，提取角色块

        Args:
            content: 文件内容

        Returns:
            dict: {角色名: 角色内容块}
        """
        blocks = {}
        lines = content.split("\n")
        current_name = None
        current_block = []
        in_new_characters = False

        main_char_pattern = re.compile(r"^([^（\n]+)(?:（[^）]+）)?：$")

        for line in lines:
            if line.strip() == "新出场角色：":
                if current_name and current_block:
                    blocks[current_name] = "\n".join(current_block).strip()
                current_name = "新出场角色"
                current_block = [line]
                in_new_characters = True
                continue

            if in_new_characters:
                current_block.append(line)
            else:
                match = main_char_pattern.match(line)
                if match:
                    if current_name and current_block:
                        blocks[current_name] = "\n".join(current_block).strip()
                    current_name = match.group(1).strip()
                    current_block = [line]
                elif current_name:
                    current_block.append(line)

        if current_name and current_block:
            blocks[current_name] = "\n".join(current_block).strip()

        return blocks

    def _rebuild_full_content(self) -> str:
        """
        重建完整文件内容

        Returns:
            str: 完整的文件内容
        """
        parts = []
        for name, block in self.character_blocks.items():
            if name == "新出场角色":
                continue
            parts.append(block)

        if "新出场角色" in self.character_blocks:
            parts.append(self.character_blocks["新出场角色"])

        return "\n\n".join(parts)

    def load_roles(self):
        self.rolesList.clear()

        if self.rolesPlaceholder:
            self.rolesPlaceholder.deleteLater()
            self.rolesPlaceholder = None
        if self.editorPlaceholder:
            self.editorPlaceholder.deleteLater()
            self.editorPlaceholder = None

        filepath = self.get_filepath()

        if filepath:
            self.editor_toolkit.set_project_path(filepath)

        if not filepath:
            empty_state = EmptyState.no_project()
            self.rolesPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.rolesListContainer,
            )
            self.rolesList.hide()
            self.rolesListLayout.addWidget(self.rolesPlaceholder)
            self.editorPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.placeholderContainer,
            )
            self.placeholderLayout.addWidget(self.editorPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
            return

        character_state_file = os.path.join(filepath, self.CHARACTER_STATE_FILE)

        if not os.path.exists(character_state_file):
            empty_state = EmptyState.character_state()
            self.rolesPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.rolesListContainer,
            )
            self.rolesList.hide()
            self.rolesListLayout.addWidget(self.rolesPlaceholder)
            self.editorPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.placeholderContainer,
            )
            self.placeholderLayout.addWidget(self.editorPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
            return

        self.character_state_content = read_file(character_state_file)
        self.character_blocks = self._parse_character_state(
            self.character_state_content
        )

        if not self.character_blocks:
            empty_state = EmptyState.character_state()
            self.rolesPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.rolesListContainer,
            )
            self.rolesList.hide()
            self.rolesListLayout.addWidget(self.rolesPlaceholder)
            self.editorStack.setCurrentWidget(self.placeholderContainer)
        else:
            self.rolesList.show()
            for name in self.character_blocks.keys():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, name)
                self.rolesList.addItem(item)
            self.editorStack.setCurrentWidget(self.roleEditor)

            if self.character_blocks:
                first_name = list(self.character_blocks.keys())[0]
                self._select_role(first_name)

    def _select_role(self, name: str):
        """
        选择并显示指定角色的内容

        Args:
            name: 角色名
        """
        if name in self.character_blocks:
            self.current_role_name = name
            self.roleEditor.setPlainText(self.character_blocks[name])
            self.editorStack.setCurrentWidget(self.roleEditor)

    def on_role_selected(self, item):
        name = item.data(Qt.UserRole)
        self._select_role(name)


__all__ = ["RolesInterface"]
