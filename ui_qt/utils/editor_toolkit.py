# -*- coding: utf-8 -*-
"""
AI Novel Generator - 编辑工具包
==============================

本模块提供可复用的编辑功能组件，包括：
- SearchReplaceManager: 搜索替换管理器
- ContextMenuManager: 上下文菜单管理器
- ComposerManager: Composer AI管理器
- EditorToolkit: 集成所有编辑功能的工具包
"""

import threading
from datetime import datetime

from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut, QWidget

from core.config_manager import load_config
from core.llm import create_llm_adapter
from core.tokens_manager import set_token_context, clear_token_context
from core import get_logger
from novel_generator.composer import ComposerPromptBuilder
from ui_qt.utils.notification_manager import NotificationManager, NotificationType

from ..widgets.composer_widget import ComposerInputWidget
from ..widgets.context_menu_widget import SelectionContextMenu
from ..widgets.diff_preview_manager import (
    DiffPreviewManager,
    get_diff_preview_mode_from_config,
)
from ..widgets.search_replace_widget import SearchReplaceWidget
from ..widgets.inline_composer_widget import InlineComposerInputWidget


class ComposerSignals(QObject):
    """
    Composer信号类，用于线程安全的UI更新

    Attributes:
        show_error: 显示错误信号
        show_query_response: 显示查询响应信号
        show_diff_response: 显示差异预览信号
        close_notification: 关闭处理中通知信号
    """

    show_error = pyqtSignal(str)
    show_query_response = pyqtSignal(str)
    show_diff_response = pyqtSignal(
        str, str, int, int
    )  # original_text, modified_text, selection_start, selection_end
    close_notification = pyqtSignal()


class SearchReplaceManager:
    """
    搜索替换功能管理器

    为编辑器提供搜索和替换功能。
    """

    def __init__(self, parent=None):
        """
        初始化搜索替换管理器

        Args:
            parent: 父控件
        """
        self.parent = parent
        self.current_active_editor = None
        self.search_widgets = {}

    def add_editor(self, editor_key: str, editor):
        """
        添加编辑器到管理器

        Args:
            editor_key: 编辑器的唯一标识符
            editor: PlainTextEdit 或 TextEdit 实例
        """
        self.search_widgets[editor_key] = SearchReplaceWidget(editor, self.parent)

    def set_active_editor(self, editor_key: str):
        """
        设置当前活动的编辑器

        Args:
            editor_key: 编辑器的唯一标识符
        """
        self.current_active_editor = editor_key

    def show_search_widget(self, editor_key: str = None):
        """
        显示搜索替换窗口

        Args:
            editor_key: 编辑器的唯一标识符，如果为 None 则使用当前活动编辑器
        """
        key = editor_key or self.current_active_editor
        if not key or key not in self.search_widgets:
            return

        search_widget = self.search_widgets[key]
        editor = None
        # 尝试从父控件获取编辑器
        if hasattr(self.parent, key + "Edit"):
            editor = getattr(self.parent, key + "Edit")
        elif hasattr(self.parent, "editor") and key == "main":
            editor = self.parent.editor
        elif hasattr(self.parent, key):
            editor = getattr(self.parent, key)

        if editor:
            editor_rect = editor.geometry()
            global_pos = editor.mapToGlobal(editor_rect.topRight())
            pos = global_pos
            pos.setX(pos.x() - search_widget.width() - 20)
            pos.setY(pos.y() + 10)
            search_widget.show_at_position(pos)


class ContextMenuManager:
    """
    上下文菜单功能管理器

    为编辑器提供右键上下文菜单功能。
    """

    def __init__(self, parent=None):
        """
        初始化上下文菜单管理器

        Args:
            parent: 父控件
        """
        self.parent = parent
        self.current_active_editor = None
        self.context_menus = {}
        self._signal_handlers = {}
        self._selection_debounce_timer = QTimer()
        self._selection_debounce_timer.setSingleShot(True)
        self._debounce_editor_key = None

    def add_editor(self, editor_key: str, editor, on_selection_changed=None):
        """
        添加编辑器到管理器

        Args:
            editor_key: 编辑器的唯一标识符
            editor: PlainTextEdit 或 TextEdit 实例
            on_selection_changed: 选择变化时的回调函数
        """
        self.context_menus[editor_key] = SelectionContextMenu(editor, self.parent)
        self._connect_context_menu_signals(self.context_menus[editor_key])
        self._selection_debounce_timer.timeout.connect(self._show_debounced_menu)

        if on_selection_changed:
            editor.selectionChanged.connect(lambda: on_selection_changed(editor_key))
        else:
            editor.selectionChanged.connect(
                lambda: self.on_selection_changed(editor_key)
            )

    def set_signal_handlers(self, handlers: dict):
        """
        设置信号处理函数

        Args:
            handlers: 包含回调函数的字典，键为事件名
        """
        self._signal_handlers = handlers

    def _connect_context_menu_signals(self, context_menu):
        """
        连接上下文菜单信号

        Args:
            context_menu: SelectionContextMenu 实例
        """
        context_menu.copy_clicked.connect(self._on_copy)
        context_menu.paste_clicked.connect(self._on_paste)
        context_menu.fix_grammar_clicked.connect(self._on_fix_grammar)
        context_menu.polish_clicked.connect(self._on_polish)
        context_menu.expand_clicked.connect(self._on_expand)
        context_menu.ask_composer_clicked.connect(self._on_ask_composer)

    def set_active_editor(self, editor_key: str):
        """
        设置当前活动的编辑器

        Args:
            editor_key: 编辑器的唯一标识符
        """
        self.current_active_editor = editor_key

    def on_selection_changed(self, editor_key: str):
        """
        文本选择变化时显示上下文菜单（带防抖机制）

        Args:
            editor_key: 编辑器的唯一标识符
        """
        editor = self._get_editor(editor_key)
        if editor:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                self.current_active_editor = editor_key
                self._debounce_editor_key = editor_key
                self._selection_debounce_timer.start(50)
            else:
                self._selection_debounce_timer.stop()
                if (
                    editor_key in self.context_menus
                    and self.context_menus[editor_key].isVisible()
                ):
                    self.context_menus[editor_key].hide()

    def _show_debounced_menu(self):
        """防抖定时器触发后显示菜单"""
        if self._debounce_editor_key:
            self.show_context_menu(self._debounce_editor_key)

    def show_context_menu(self, editor_key: str):
        """
        显示上下文菜单

        Args:
            editor_key: 编辑器的唯一标识符
        """
        if editor_key in self.context_menus:
            editor = self._get_editor(editor_key)
            if editor:
                cursor = editor.textCursor()
                if cursor.hasSelection():
                    self.context_menus[editor_key].show_at_selection()

    def _get_editor(self, editor_key: str):
        """
        获取编辑器实例

        Args:
            editor_key: 编辑器的唯一标识符

        Returns:
            编辑器实例或 None
        """
        if hasattr(self.parent, editor_key + "Edit"):
            return getattr(self.parent, editor_key + "Edit")
        elif hasattr(self.parent, "editor") and editor_key == "main":
            return self.parent.editor
        elif hasattr(self.parent, editor_key):
            return getattr(self.parent, editor_key)
        return None

    def _on_copy(self):
        """复制按钮点击"""
        if "on_copy" in self._signal_handlers:
            self._signal_handlers["on_copy"]()
            return
        editor_key = self.current_active_editor
        editor = self._get_editor(editor_key)
        if editor:
            editor.copy()

    def _on_paste(self):
        """粘贴按钮点击"""
        if "on_paste" in self._signal_handlers:
            self._signal_handlers["on_paste"]()
            return
        editor_key = self.current_active_editor
        editor = self._get_editor(editor_key)
        if editor:
            editor.paste()

    def _on_fix_grammar(self, text):
        """修复语法按钮点击"""
        if "on_fix_grammar" in self._signal_handlers:
            self._signal_handlers["on_fix_grammar"](text)
            return

    def _on_polish(self, text):
        """润色按钮点击"""
        if "on_polish" in self._signal_handlers:
            self._signal_handlers["on_polish"](text)
            return

    def _on_expand(self, text, expand_type):
        """扩展描写按钮点击"""
        if "on_expand" in self._signal_handlers:
            self._signal_handlers["on_expand"](text, expand_type)
            return

    def _on_ask_composer(self, text):
        """询问Composer按钮点击"""
        if "on_ask_composer" in self._signal_handlers:
            self._signal_handlers["on_ask_composer"](text)
            return


class ComposerManager:
    """
    Composer AI功能管理器

    提供 AI 辅助编辑功能。
    """

    def __init__(self, parent=None, project_path: str = ""):
        """
        初始化 Composer 管理器

        Args:
            parent: 父控件
            project_path: 当前项目路径
        """
        self.parent = parent
        self.project_path = project_path
        self.loaded_config = load_config("config.json") or {}
        composer_settings = self.loaded_config.get("composer_settings", {})
        self.ai_level = composer_settings.get("ai_level", "standard")
        self.prompt_builder = ComposerPromptBuilder(
            ai_level=self.ai_level, project_path=self.project_path
        )
        self.ai_worker = None
        self.composer_input = None
        self.inline_composer_input = None
        self.diff_preview_manager = None
        self._signal_handlers = {}
        self._notify = NotificationManager(parent)
        self._processing_notification = None
        self._logger = get_logger()
        self._editor_viewport = None

        self._signals = ComposerSignals()
        self._signals.show_error.connect(self._on_show_error)
        self._signals.show_query_response.connect(self._on_show_query_response)
        self._signals.show_diff_response.connect(self._on_show_diff_response)
        self._signals.close_notification.connect(self._on_close_notification)

    def set_project_path(self, project_path: str):
        """
        设置项目路径

        Args:
            project_path: 项目路径
        """
        self.project_path = project_path
        self.prompt_builder = ComposerPromptBuilder(
            ai_level=self.ai_level, project_path=self.project_path
        )

    def set_signal_handlers(self, handlers: dict):
        """
        设置信号处理函数

        Args:
            handlers: 包含回调函数的字典
        """
        self._signal_handlers = handlers

    def ask_composer(self, text: str):
        """
        询问 Composer（使用嵌入式输入框）

        Args:
            text: 选中文本
        """
        editor = self._get_current_editor()
        if not editor:
            return

        # 清理现有的嵌入式输入框
        if self.inline_composer_input is not None:
            self.inline_composer_input.collapse()
            self.inline_composer_input.deleteLater()
            self.inline_composer_input = None

        # 获取编辑器的 viewport，输入框将作为其子控件以跟随滚动
        editor_viewport = editor.viewport()

        self.inline_composer_input = InlineComposerInputWidget(
            text, self.ai_level, editor_viewport, editor
        )
        self.inline_composer_input.query_submitted.connect(
            lambda query: self.process_ai_task("query", text, query)
        )
        self.inline_composer_input.ai_level_changed.connect(self.on_ai_level_changed)
        self.inline_composer_input.closed.connect(self._on_inline_composer_closed)

        cursor = editor.textCursor()
        if cursor.hasSelection():
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            # 使用新的嵌入方法：在选中文本前插入空行
            self.inline_composer_input.show_embedded_at_selection(
                selection_start, selection_end
            )

    def _on_inline_composer_closed(self):
        """嵌入式输入框关闭时的回调"""
        pass

    def cleanup_composer(self):
        """清理composer相关组件（当页面切换时调用）"""
        if hasattr(self, "composer_input") and self.composer_input:
            self.composer_input.close()
            self.composer_input.deleteLater()
            self.composer_input = None
        if hasattr(self, "inline_composer_input") and self.inline_composer_input:
            self.inline_composer_input.collapse()
            self.inline_composer_input.deleteLater()
            self.inline_composer_input = None
        if hasattr(self, "diff_preview_manager") and self.diff_preview_manager:
            self.diff_preview_manager.cleanup()
            self.diff_preview_manager = None

    def _get_current_editor(self):
        """
        获取当前编辑器实例

        Returns:
            编辑器实例或 None
        """
        if hasattr(self.parent, "editor"):
            return self.parent.editor
        elif hasattr(self.parent, "mainEdit"):
            return self.parent.mainEdit
        return None

    def on_ai_level_changed(self, new_level):
        """
        处理AI等级变化

        Args:
            new_level: 新的AI等级
        """
        self.ai_level = new_level
        self.loaded_config["composer_settings"]["ai_level"] = new_level
        from core.config_manager import save_config

        save_config(self.loaded_config, "config.json")
        self.prompt_builder = ComposerPromptBuilder(
            ai_level=self.ai_level, project_path=self.project_path
        )

    def process_ai_task(self, task_type: str, text: str, extra_param: str = ""):
        """
        处理 AI 任务

        Args:
            task_type: 任务类型 (grammar/polish/expand/query)
            text: 选中文本
            extra_param: 额外参数（如扩展类型或用户查询）
        """
        if "on_process_task" in self._signal_handlers:
            self._signal_handlers["on_process_task"](task_type, text, extra_param)
            return

        self._processing_notification = self._notify.info(
            "", "正在处理...", duration=-1
        )
        self._logger.debug("composer", f"开始处理AI任务: {task_type}")
        _ = self.prompt_builder.build_prompt(
            task_type=task_type, selected_text=text, user_query=extra_param
        )
        self.process_ai_request(task_type, text, extra_param)

    def process_ai_request(self, task_type: str, original_text: str, extra_param: str):
        """
        调用 LLM 处理 AI 任务（异步执行）

        Args:
            task_type: 任务类型
            original_text: 原始文本
            extra_param: 额外参数
        """
        # 保存当前选区位置，以便异步处理完成后能正确定位
        editor = self._get_current_editor()
        if editor:
            cursor = editor.textCursor()
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
        else:
            selection_start = None
            selection_end = None

        def call_llm():
            try:
                self._logger.debug("composer", "开始创建LLM适配器")
                llm_adapter = self._create_llm_adapter()
                if not llm_adapter:
                    self._logger.error("composer", "LLM配置未找到")
                    self._signals.show_error.emit("LLM配置未找到，请先配置模型")
                    self._signals.close_notification.emit()
                    return

                self._logger.debug("composer", "LLM适配器创建成功，开始构建提示词")
                prompt = self.prompt_builder.build_prompt(
                    task_type=task_type,
                    selected_text=original_text,
                    user_query=extra_param,
                )
                self._logger.debug("composer", f"提示词构建完成，长度: {len(prompt)}")

                task_name_map = {
                    "grammar": "修复语法",
                    "polish": "润色",
                    "expand": "扩展描写",
                    "query": "询问Composer",
                }
                task_name = task_name_map.get(task_type, task_type)
                if task_type == "expand" and extra_param:
                    expand_type_map = {
                        "psychological": "心理描写",
                        "expression": "神态描写",
                        "action": "动作描写",
                        "environment": "环境描写",
                        "dialogue": "对话补充",
                    }
                    task_name = (
                        f"{task_name} - {expand_type_map.get(extra_param, extra_param)}"
                    )

                set_token_context(step_name=f"Composer - {task_name}")

                try:
                    self._logger.debug("composer", "开始调用LLM")
                    response = llm_adapter.invoke(prompt)
                    self._logger.debug(
                        "composer",
                        f"LLM调用完成，响应长度: {len(response) if response else 0}",
                    )
                finally:
                    clear_token_context()

                if response:
                    if task_type == "query":
                        self._signals.show_query_response.emit(response)
                    else:
                        self._signals.show_diff_response.emit(
                            original_text, response, selection_start, selection_end
                        )
                    self._signals.close_notification.emit()
                else:
                    self._logger.error("composer", "未获取到响应")
                    self._signals.show_error.emit("AI处理失败，未获取到响应")
                    self._signals.close_notification.emit()
            except Exception as e:
                self._logger.error("composer", f"AI处理出错: {str(e)}")
                self._signals.show_error.emit(f"AI处理出错: {str(e)}")
                self._signals.close_notification.emit()

        threading.Thread(target=call_llm, daemon=True).start()

    def _create_llm_adapter(self):
        """
        创建 LLM 适配器实例

        Returns:
            LLM适配器实例，如果配置不存在则返回 None
        """
        llm_configs = self.loaded_config.get("llm_configs", {})

        if not llm_configs:
            return None

        config_name = next(iter(llm_configs))
        config = llm_configs[config_name]

        return create_llm_adapter(
            interface_format=config.get("interface_format", ""),
            base_url=config.get("base_url", ""),
            model_name=config.get("model_name", ""),
            api_key=config.get("api_key", ""),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
            timeout=config.get("timeout", 600),
        )

    def _on_show_error(self, message):
        """
        在主线程显示错误消息（信号槽）

        Args:
            message: 错误消息
        """
        self._notify.error("", message)

    def _on_close_notification(self):
        """关闭处理中的通知（信号槽）"""
        if self._processing_notification:
            try:
                self._processing_notification.close()
                self._processing_notification = None
            except Exception:
                self._processing_notification = None

    def _on_show_query_response(self, response):
        """
        在主线程显示查询响应（信号槽）

        Args:
            response: 查询响应内容
        """
        content = response[:200] + "..." if len(response) > 200 else response
        self._notify.success("Composer回复", content, duration=5000)

    def _on_show_diff_response(
        self, original_text, modified_text, selection_start, selection_end
    ):
        """
        在主线程显示差异预览（信号槽）

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置
            selection_end: 选区结束位置
        """
        self.show_diff_preview(
            original_text, modified_text, selection_start, selection_end
        )

    def _show_error(self, message):
        """在主线程显示错误消息"""
        self._signals.show_error.emit(message)

    def _show_query_response(self, response):
        """在主线程显示查询响应"""
        self._signals.show_query_response.emit(response)

    def _show_diff_response(
        self, original_text, modified_text, selection_start=None, selection_end=None
    ):
        """
        在主线程显示差异预览

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置（可选）
            selection_end: 选区结束位置（可选）
        """
        # 确保参数不为None，使用默认值0
        if selection_start is None:
            selection_start = 0
        if selection_end is None:
            selection_end = 0
        self._signals.show_diff_response.emit(
            original_text, modified_text, selection_start, selection_end
        )

    def show_diff_preview(
        self,
        original_text: str,
        modified_text: str,
        selection_start: int = None,
        selection_end: int = None,
    ):
        """
        在编辑器中显示差异预览

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置（可选）
            selection_end: 选区结束位置（可选）
        """
        editor = self._get_current_editor()
        if not editor:
            return

        diff_mode = get_diff_preview_mode_from_config(self.loaded_config)

        if self.diff_preview_manager:
            self.diff_preview_manager.cleanup()

        self.diff_preview_manager = DiffPreviewManager(editor, self.parent, diff_mode)
        self.diff_preview_manager.changes_accepted.connect(self._apply_changes)
        self.diff_preview_manager.changes_rejected.connect(self._reject_changes)
        self.diff_preview_manager.show_diff(
            original_text, modified_text, selection_start, selection_end
        )

    def _apply_changes(self, modified_text: str):
        """
        应用修改

        Args:
            modified_text: 修改后的文本
        """
        if "on_apply_changes" in self._signal_handlers:
            self._signal_handlers["on_apply_changes"](modified_text)
            return

        self._notify.success("", "修改已应用")

    def _reject_changes(self):
        """拒绝修改"""
        if "on_reject_changes" in self._signal_handlers:
            self._signal_handlers["on_reject_changes"]()
            return

        self._notify.info("", "修改已取消")


class EditorToolkit(QWidget):
    """
    集成编辑工具包

    整合搜索替换、上下文菜单和 Composer 功能。
    """

    def __init__(self, parent=None, project_path: str = ""):
        """
        初始化编辑工具包

        Args:
            parent: 父控件
            project_path: 当前项目路径
        """
        super().__init__(parent)
        self.search_manager = SearchReplaceManager(parent)
        self.context_menu_manager = ContextMenuManager(parent)
        self.composer_manager = ComposerManager(parent, project_path)
        self.current_active_editor = None
        self.search_shortcut = None

    def init_shortcuts(self):
        """初始化快捷键"""
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.parent())
        self.search_shortcut.activated.connect(self.show_search_widget)

    def add_editor(self, editor_key: str, editor, on_selection_changed=None):
        """
        添加编辑器到工具包

        Args:
            editor_key: 编辑器的唯一标识符
            editor: PlainTextEdit 或 TextEdit 实例
            on_selection_changed: 选择变化时的回调函数
        """
        self.search_manager.add_editor(editor_key, editor)
        self.context_menu_manager.add_editor(editor_key, editor, on_selection_changed)

    def set_active_editor(self, editor_key: str):
        """
        设置当前活动的编辑器

        Args:
            editor_key: 编辑器的唯一标识符
        """
        self.current_active_editor = editor_key
        self.search_manager.set_active_editor(editor_key)
        self.context_menu_manager.set_active_editor(editor_key)

    def show_search_widget(self, editor_key: str = None):
        """
        显示搜索替换窗口

        Args:
            editor_key: 编辑器的唯一标识符
        """
        self.search_manager.show_search_widget(editor_key)

    def set_project_path(self, project_path: str):
        """
        设置项目路径

        Args:
            project_path: 项目路径
        """
        self.composer_manager.set_project_path(project_path)

    def set_composer_handlers(self, handlers: dict):
        """
        设置 Composer 信号处理函数

        Args:
            handlers: 包含回调函数的字典
        """
        self.composer_manager.set_signal_handlers(handlers)

    def set_context_menu_handlers(self, handlers: dict):
        """
        设置上下文菜单信号处理函数

        Args:
            handlers: 包含回调函数的字典
        """
        self.context_menu_manager.set_signal_handlers(handlers)


__all__ = [
    "SearchReplaceManager",
    "ContextMenuManager",
    "ComposerManager",
    "EditorToolkit",
]
