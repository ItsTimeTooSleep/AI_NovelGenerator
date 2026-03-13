# -*- coding: utf-8 -*-
"""
Composer AI功能模块

================================================================================
模块功能概述
================================================================================
本模块负责管理首页中Composer AI相关的所有功能，包括：
- 搜索替换功能
- 文本选择上下文菜单
- Composer AI交互（语法修正、润色、扩写、问答）
- 快捷键绑定

================================================================================
核心类
================================================================================
- ComposerFeatures: Composer AI功能管理器

================================================================================
核心功能
================================================================================
- init_search_replace: 初始化搜索替换功能
- init_context_menu: 初始化上下文菜单
- init_composer_ai: 初始化Composer AI组件
- setup_shortcuts: 设置快捷键

================================================================================
Composer AI任务类型
================================================================================
- grammar: 语法修正
- polish: 文本润色
- expand: 内容扩写
- query: 问题查询

================================================================================
设计决策
================================================================================
- 每个编辑器独立管理搜索替换组件
- 上下文菜单支持选中文本操作
- AI处理结果通过差异对比展示
- 支持快捷键快速调用功能

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import re
import threading
from datetime import datetime

from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut, QApplication

from core.llm import create_llm_adapter
from core.tokens_manager import set_token_context, clear_token_context
from novel_generator.composer import ComposerPromptBuilder
from ui_qt.utils.notification_manager import NotificationManager, NotificationType

from ..widgets.composer_widget import ComposerInputWidget, ComposerResponseWidget
from ..widgets.context_menu_widget import SelectionContextMenu
from ..widgets.search_replace_widget import SearchReplaceWidget
from ..widgets.diff_preview_manager import (
    DiffPreviewManager,
    get_diff_preview_mode_from_config,
)
from ..widgets.overlay_manager import OverlayManager
from ..widgets.inline_composer_widget import InlineComposerInputWidget

SUGGESTION_PATTERN = re.compile(r"\[SUGGESTION\](.*?)\[/SUGGESTION\]", re.DOTALL)


def parse_suggestion_response(response: str):
    """
    解析AI响应，提取SUGGESTION标签内容

    Args:
        response: AI的原始响应

    Returns:
        tuple: (is_suggestion, content)
            - is_suggestion: 是否包含SUGGESTION标签
            - content: 如果是suggestion，返回标签内的内容；否则返回原始响应
    """
    match = SUGGESTION_PATTERN.search(response)
    if match:
        return True, match.group(1).strip()
    return False, response


def strip_suggestion_tags(text: str) -> str:
    """
    去除文本中的SUGGESTION标签

    Args:
        text: 可能包含SUGGESTION标签的文本

    Returns:
        str: 去除标签后的纯文本内容
    """
    if not text:
        return text

    match = SUGGESTION_PATTERN.search(text)
    if match:
        return match.group(1).strip()

    text = text.replace("[SUGGESTION]", "").replace("[/SUGGESTION]", "")
    return text.strip()


class ComposerSignals(QObject):
    """
    Composer信号类，用于线程安全的UI更新

    Attributes:
        show_error: 显示错误信号
        show_query_response: 显示查询响应信号
        show_diff_response: 显示差异预览信号
        append_diff_content: 追加差异内容信号（流式传输）
        close_notification: 关闭处理中通知信号
        log_message: 日志消息信号（线程安全）
    """

    show_error = pyqtSignal(str)
    show_query_response = pyqtSignal(str)
    show_diff_response = pyqtSignal(
        str, str, int, int
    )  # original_text, modified_text, selection_start, selection_end
    append_diff_content = pyqtSignal(str)  # content to append
    close_notification = pyqtSignal()
    log_message = pyqtSignal(str)


class ComposerFeatures:
    """
    Composer AI 功能管理器

    负责管理搜索替换、上下文菜单、Composer AI 等功能。
    """

    def __init__(self, home_tab):
        """
        初始化 ComposerFeatures

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab
        self.current_active_editor = None
        self.search_widgets = {}
        self.context_menus = {}
        self.ai_worker = None
        self.prompt_builder = None
        self.ai_level = "standard"
        self.composer_input = None
        self.diff_preview_manager = None
        self.response_widget = None
        self._notify = NotificationManager(home_tab)
        self._processing_notification = None
        self._conversation_context = ""
        self._current_selected_text = ""

        # 流式传输相关变量
        self._streaming_mode = False
        self._detected_suggestion = False
        self._accumulated_response = ""
        self._suggestion_content = ""

        self._signals = ComposerSignals()
        self._signals.show_error.connect(self._on_show_error)
        self._signals.show_query_response.connect(self._on_show_query_response)
        self._signals.show_diff_response.connect(self._on_show_diff_response)
        self._signals.append_diff_content.connect(self._on_append_diff_content)
        self._signals.close_notification.connect(self._on_close_notification)
        self._signals.log_message.connect(self._on_log_message)

    def init_search_replace(self):
        """
        初始化搜索替换功能
        """
        self.current_active_editor = None
        self.search_widgets = {}
        if hasattr(self.home_tab, "step1TextEdit"):
            self.search_widgets["step1"] = SearchReplaceWidget(
                self.home_tab.step1TextEdit, self.home_tab
            )
        if hasattr(self.home_tab, "step1ReviewTextEdit"):
            self.search_widgets["step1Review"] = SearchReplaceWidget(
                self.home_tab.step1ReviewTextEdit, self.home_tab
            )
        if hasattr(self.home_tab, "step2TextEdit"):
            self.search_widgets["step2"] = SearchReplaceWidget(
                self.home_tab.step2TextEdit, self.home_tab
            )
        if hasattr(self.home_tab, "editor"):
            self.search_widgets["main"] = SearchReplaceWidget(
                self.home_tab.editor, self.home_tab
            )

    def init_context_menu(self):
        """
        初始化选择上下文菜单
        """
        self.current_active_editor = None
        self.context_menus = {}
        if hasattr(self.home_tab, "step1TextEdit"):
            self.context_menus["step1"] = SelectionContextMenu(
                self.home_tab.step1TextEdit, self.home_tab
            )
            self._connect_context_menu_signals(self.context_menus["step1"])
            self.home_tab.step1TextEdit.selectionChanged.connect(
                lambda: self.on_selection_changed("step1")
            )
        if hasattr(self.home_tab, "step1ReviewTextEdit"):
            self.context_menus["step1Review"] = SelectionContextMenu(
                self.home_tab.step1ReviewTextEdit, self.home_tab
            )
            self._connect_context_menu_signals(self.context_menus["step1Review"])
            self.home_tab.step1ReviewTextEdit.selectionChanged.connect(
                lambda: self.on_selection_changed("step1Review")
            )
        if hasattr(self.home_tab, "step2TextEdit"):
            self.context_menus["step2"] = SelectionContextMenu(
                self.home_tab.step2TextEdit, self.home_tab
            )
            self._connect_context_menu_signals(self.context_menus["step2"])
            self.home_tab.step2TextEdit.selectionChanged.connect(
                lambda: self.on_selection_changed("step2")
            )
        if hasattr(self.home_tab, "editor"):
            self.context_menus["main"] = SelectionContextMenu(
                self.home_tab.editor, self.home_tab
            )
            self._connect_context_menu_signals(self.context_menus["main"])
            self.home_tab.editor.selectionChanged.connect(
                lambda: self.on_selection_changed("main")
            )

    def _connect_context_menu_signals(self, context_menu):
        """
        连接上下文菜单信号

        Args:
            context_menu: 上下文菜单对象
        """
        context_menu.copy_clicked.connect(self.on_copy)
        context_menu.paste_clicked.connect(self.on_paste)
        context_menu.fix_grammar_clicked.connect(self.on_fix_grammar)
        context_menu.polish_clicked.connect(self.on_polish)
        context_menu.expand_clicked.connect(self.on_expand)
        context_menu.ask_composer_clicked.connect(self.on_ask_composer)

    def init_composer(self):
        """
        初始化 Composer AI 功能
        """
        composer_settings = self.home_tab.loaded_config.get("composer_settings", {})
        self.ai_level = composer_settings.get("ai_level", "standard")
        self.prompt_builder = ComposerPromptBuilder(
            ai_level=self.ai_level, project_path=self.home_tab.current_project_path
        )
        self.ai_worker = None

    def init_shortcuts(self):
        """
        初始化快捷键
        """
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.home_tab)
        self.search_shortcut.activated.connect(self.show_search_widget)

    def get_current_active_editor(self):
        """
        获取当前活动的编辑器

        Returns:
            str: 当前活动编辑器的键名，或 None
        """
        if hasattr(self.home_tab, "initStack"):
            current_widget = self.home_tab.initStack.currentWidget()
            if (
                current_widget == getattr(self.home_tab, "frameStep1", None)
                and hasattr(self.home_tab, "step1TextEdit")
                and self.home_tab.step1TextEdit.isVisible()
            ):
                return "step1"
            elif current_widget == getattr(
                self.home_tab, "frameStep1Review", None
            ) and hasattr(self.home_tab, "step1ReviewTextEdit"):
                return "step1Review"
            elif (
                current_widget == getattr(self.home_tab, "frameStep2", None)
                and hasattr(self.home_tab, "step2TextEdit")
                and self.home_tab.step2TextEdit.isVisible()
            ):
                return "step2"
        if hasattr(self.home_tab, "editor") and self.home_tab.editor.isVisible():
            return "main"
        return None

    def _get_current_editor(self):
        """
        获取当前活动的编辑器对象

        Returns:
            编辑器对象，或 None
        """
        editor_key = self.get_current_active_editor()
        if not editor_key:
            return None
        if editor_key == "step1":
            return self.home_tab.step1TextEdit
        elif editor_key == "step1Review":
            return self.home_tab.step1ReviewTextEdit
        elif editor_key == "step2":
            return self.home_tab.step2TextEdit
        elif editor_key == "main":
            return self.home_tab.editor
        return None

    def show_search_widget(self):
        """
        显示搜索替换窗口
        """
        editor_key = self.get_current_active_editor()
        if not editor_key or editor_key not in self.search_widgets:
            return

        search_widget = self.search_widgets[editor_key]
        editor = None
        if editor_key == "step1":
            editor = self.home_tab.step1TextEdit
        elif editor_key == "step1Review":
            editor = self.home_tab.step1ReviewTextEdit
        elif editor_key == "step2":
            editor = self.home_tab.step2TextEdit
        elif editor_key == "main":
            editor = self.home_tab.editor

        if editor:
            editor_rect = editor.geometry()
            global_pos = editor.mapToGlobal(editor_rect.topRight())
            pos = global_pos
            pos.setX(pos.x() - search_widget.width() - 20)
            pos.setY(pos.y() + 10)
            search_widget.show_at_position(pos)

    def on_selection_changed(self, editor_key):
        """
        文本选择变化时显示上下文菜单

        Args:
            editor_key: 编辑器键名
        """
        editor = None
        if editor_key == "step1":
            editor = self.home_tab.step1TextEdit
        elif editor_key == "step1Review":
            editor = self.home_tab.step1ReviewTextEdit
        elif editor_key == "step2":
            editor = self.home_tab.step2TextEdit
        elif editor_key == "main":
            editor = self.home_tab.editor

        if editor:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                self.current_active_editor = editor_key
                QTimer.singleShot(300, lambda: self.show_context_menu(editor_key))
            else:
                if (
                    editor_key in self.context_menus
                    and self.context_menus[editor_key].isVisible()
                ):
                    self.context_menus[editor_key].hide()

    def show_context_menu(self, editor_key):
        """
        显示上下文菜单

        Args:
            editor_key: 编辑器键名
        """
        if editor_key in self.context_menus:
            editor = None
            if editor_key == "step1":
                editor = self.home_tab.step1TextEdit
            elif editor_key == "step1Review":
                editor = self.home_tab.step1ReviewTextEdit
            elif editor_key == "step2":
                editor = self.home_tab.step2TextEdit
            elif editor_key == "main":
                editor = self.home_tab.editor

            if editor:
                cursor = editor.textCursor()
                if cursor.hasSelection():
                    self.context_menus[editor_key].show_at_selection()

    def on_copy(self):
        """
        复制按钮点击
        """
        editor_key = self.get_current_active_editor()
        if editor_key:
            if editor_key == "step1":
                self.home_tab.step1TextEdit.copy()
            elif editor_key == "step1Review":
                self.home_tab.step1ReviewTextEdit.copy()
            elif editor_key == "step2":
                self.home_tab.step2TextEdit.copy()
            elif editor_key == "main":
                self.home_tab.editor.copy()

    def on_paste(self):
        """
        粘贴按钮点击
        """
        editor_key = self.get_current_active_editor()
        if editor_key:
            if editor_key == "step1":
                self.home_tab.step1TextEdit.paste()
            elif editor_key == "step1Review":
                self.home_tab.step1ReviewTextEdit.paste()
            elif editor_key == "step2":
                self.home_tab.step2TextEdit.paste()
            elif editor_key == "main":
                self.home_tab.editor.paste()

    def on_fix_grammar(self, text):
        """
        修复语法按钮点击

        Args:
            text: 选中文本
        """
        self.process_ai_task("grammar", text)

    def on_polish(self, text):
        """
        润色按钮点击

        Args:
            text: 选中文本
        """
        self.process_ai_task("polish", text)

    def on_expand(self, text, expand_type):
        """
        扩展描写按钮点击

        Args:
            text: 选中文本
            expand_type: 扩展类型
        """
        self.process_ai_task("expand", text, expand_type)

    def on_ask_composer(self, text):
        """
        询问 Composer 按钮点击（使用嵌入式输入框）

        Args:
            text: 选中文本
        """
        print(
            f"[DEBUG] on_ask_composer called with text: {text[:50] if text else 'None'}..."
        )
        self._current_selected_text = text
        self._conversation_context = ""

        editor = self._get_current_editor()
        print(f"[DEBUG] editor: {editor}")
        if not editor:
            print("[DEBUG] ERROR: editor is None, returning")
            return

        # 清理现有的嵌入式输入框
        if hasattr(self, "inline_composer_input") and self.inline_composer_input:
            print("[DEBUG] Cleaning up existing inline_composer_input")
            self.inline_composer_input.collapse()
            self.inline_composer_input.deleteLater()
            self.inline_composer_input = None

        # 获取编辑器的 viewport，输入框将作为其子控件以跟随滚动
        editor_viewport = editor.viewport()
        print(f"[DEBUG] editor_viewport: {editor_viewport}")

        print(
            f"[DEBUG] Creating InlineComposerInputWidget with ai_level={self.ai_level}"
        )
        self.inline_composer_input = InlineComposerInputWidget(
            text, self.ai_level, editor_viewport, editor
        )
        self.inline_composer_input.query_submitted.connect(
            lambda query: self.process_ai_task("query", text, query)
        )
        self.inline_composer_input.ai_level_changed.connect(self.on_ai_level_changed)
        self.inline_composer_input.closed.connect(self._on_inline_composer_closed)

        cursor = editor.textCursor()
        print(f"[DEBUG] cursor.hasSelection(): {cursor.hasSelection()}")
        if cursor.hasSelection():
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            print(f"[DEBUG] selection: start={selection_start}, end={selection_end}")

            # 使用新的嵌入方法：在选中文本前插入空行
            self.inline_composer_input.show_embedded_at_selection(
                selection_start, selection_end
            )
        else:
            print("[DEBUG] ERROR: No selection in cursor")

    def _on_inline_composer_closed(self):
        """嵌入式输入框关闭时的回调"""
        pass

    def _get_current_editor(self):
        """
        获取当前活动的编辑器

        Returns:
            当前编辑器实例或 None
        """
        if not self.current_active_editor:
            if hasattr(self.home_tab, "editor"):
                return self.home_tab.editor
            return None

        editor_map = {
            "step1": "step1TextEdit",
            "step1Review": "step1ReviewTextEdit",
            "step2": "step2TextEdit",
            "main": "editor",
        }

        editor_attr = editor_map.get(self.current_active_editor)
        if editor_attr and hasattr(self.home_tab, editor_attr):
            return getattr(self.home_tab, editor_attr)

        if hasattr(self.home_tab, "editor"):
            return self.home_tab.editor
        return None

    def cleanup_composer(self):
        """
        清理 composer 相关组件（当页面切换时调用）
        """
        if hasattr(self, "context_menus"):
            for menu in self.context_menus.values():
                if menu.isVisible():
                    menu.hide()

        if hasattr(self, "composer_input") and self.composer_input:
            OverlayManager.hide_widget(
                self.home_tab, self.composer_input, "composer_input"
            )
            self.composer_input.deleteLater()
            self.composer_input = None

        if hasattr(self, "inline_composer_input") and self.inline_composer_input:
            self.inline_composer_input.collapse()
            self.inline_composer_input.deleteLater()
            self.inline_composer_input = None

        if hasattr(self, "diff_preview_manager") and self.diff_preview_manager:
            self.diff_preview_manager.cleanup()
            self.diff_preview_manager = None

        if hasattr(self, "response_widget") and self.response_widget:
            OverlayManager.hide_widget(
                self.home_tab, self.response_widget, "composer_response"
            )
            self.response_widget.deleteLater()
            self.response_widget = None

    def on_ai_level_changed(self, new_level):
        """
        处理 AI 等级变化

        Args:
            new_level: 新的 AI 等级
        """
        self.ai_level = new_level
        self.home_tab.loaded_config["composer_settings"]["ai_level"] = new_level
        from core.config_manager import save_config

        save_config(self.home_tab.loaded_config, "config.json")
        self.prompt_builder = ComposerPromptBuilder(
            ai_level=self.ai_level, project_path=self.home_tab.current_project_path
        )

    def process_ai_task(self, task_type, text, extra_param=""):
        """
        处理 AI 任务

        Args:
            task_type: 任务类型 (grammar/polish/expand/query)
            text: 选中文本
            extra_param: 额外参数（如扩展类型或用户查询）
        """
        from datetime import datetime

        task_name_map = {
            "grammar": "修复语法",
            "polish": "润色",
            "expand": "扩展描写",
            "query": "询问Composer",
        }
        task_name = task_name_map.get(task_type, task_type)

        if extra_param:
            if task_type == "expand":
                expand_type_map = {
                    "psychological": "心理描写",
                    "expression": "神态描写",
                    "action": "动作描写",
                    "environment": "环境描写",
                    "dialogue": "对话补充",
                }
                expand_name = expand_type_map.get(extra_param, extra_param)
                self.home_tab.log(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] {task_name} - {expand_name}: {text[:100]}{'...' if len(text) > 100 else ''}"
                )
            else:
                self.home_tab.log(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] {task_name} - {extra_param}: {text[:100]}{'...' if len(text) > 100 else ''}"
                )
        else:
            self.home_tab.log(
                f"[{datetime.now().strftime('%H:%M:%S')}] [AI] {task_name}: {text[:100]}{'...' if len(text) > 100 else ''}"
            )

        # 显示处理中通知并保存引用
        self._processing_notification = self._notify.info(
            "", "正在处理...", duration=-1
        )
        self.home_tab.log(
            f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 开始处理任务: {task_name}"
        )

        # 构建并测试提示词
        prompt = self.prompt_builder.build_prompt(
            task_type=task_type, selected_text=text, user_query=extra_param
        )
        self.home_tab.log(
            f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 提示词构建完成，长度: {len(prompt)}"
        )

        self.process_ai_request(task_type, text, extra_param)

    def process_ai_request(self, task_type, original_text, extra_param):
        """
        调用 LLM 处理 AI 任务（异步执行，支持流式传输）

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

        # 检查是否启用流式传输
        streaming_enabled = self.home_tab.loaded_config.get("streaming_enabled", True)

        def call_llm():
            try:
                self._signals.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 开始创建LLM适配器"
                )
                llm_adapter = self._create_llm_adapter()
                if not llm_adapter:
                    self._signals.log_message.emit(
                        f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 错误: LLM配置未找到"
                    )
                    self._signals.show_error.emit("LLM配置未找到，请先配置模型")
                    self._signals.close_notification.emit()
                    return

                self._signals.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] LLM适配器创建成功，开始构建提示词"
                )
                prompt = self.prompt_builder.build_prompt(
                    task_type=task_type,
                    selected_text=original_text,
                    user_query=extra_param,
                    conversation_context=(
                        self._conversation_context if task_type == "query" else ""
                    ),
                )
                self._signals.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 提示词构建完成，开始调用LLM"
                )

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
                    if streaming_enabled and task_type != "query":
                        # 流式传输模式（仅用于非query任务）
                        self._process_streaming_request(
                            llm_adapter,
                            prompt,
                            task_type,
                            original_text,
                            selection_start,
                            selection_end,
                        )
                    else:
                        # 非流式传输模式
                        response = llm_adapter.invoke(prompt)
                        self._signals.log_message.emit(
                            f"[{datetime.now().strftime('%H:%M:%S')}] [AI] LLM调用完成，响应长度: {len(response) if response else 0}"
                        )

                        if response:
                            if task_type == "query":
                                self._signals.show_query_response.emit(response)
                            else:
                                # 确保参数不为None，使用默认值0
                                start = (
                                    selection_start
                                    if selection_start is not None
                                    else 0
                                )
                                end = selection_end if selection_end is not None else 0
                                self._signals.show_diff_response.emit(
                                    original_text, response, start, end
                                )
                            self._signals.close_notification.emit()
                        else:
                            self._signals.log_message.emit(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 错误: 未获取到响应"
                            )
                            self._signals.show_error.emit("AI处理失败，未获取到响应")
                            self._signals.close_notification.emit()
                finally:
                    clear_token_context()
            except Exception as e:
                self._signals.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 错误: {str(e)}"
                )
                self._signals.show_error.emit(f"AI处理出错: {str(e)}")
                self._signals.close_notification.emit()

        threading.Thread(target=call_llm, daemon=True).start()

    def _process_streaming_request(
        self,
        llm_adapter,
        prompt,
        task_type,
        original_text,
        selection_start,
        selection_end,
    ):
        """
        处理流式传输请求

        Args:
            llm_adapter: LLM适配器
            prompt: 提示词
            task_type: 任务类型
            original_text: 原始文本
            selection_start: 选区开始位置
            selection_end: 选区结束位置
        """
        from core.llm import StreamChunk

        full_response = ""
        detected_suggestion = False
        suggestion_started = False
        suggestion_content = ""
        diff_initialized = False

        def on_chunk(chunk: StreamChunk):
            nonlocal full_response, detected_suggestion, suggestion_started, suggestion_content, diff_initialized

            if chunk.content:
                full_response += chunk.content

                if not detected_suggestion:
                    if "[SUGGESTION]" in full_response:
                        detected_suggestion = True
                        suggestion_started = True
                        start_idx = full_response.find("[SUGGESTION]") + len(
                            "[SUGGESTION]"
                        )
                        suggestion_content = full_response[start_idx:]
                        if "[/SUGGESTION]" in suggestion_content:
                            end_idx = suggestion_content.find("[/SUGGESTION]")
                            suggestion_content = suggestion_content[:end_idx]
                        start = selection_start if selection_start is not None else 0
                        end = selection_end if selection_end is not None else 0
                        self._signals.show_diff_response.emit(
                            original_text, suggestion_content, start, end
                        )
                        diff_initialized = True
                elif suggestion_started:
                    suggestion_content += chunk.content
                    if "[/SUGGESTION]" in suggestion_content:
                        end_idx = suggestion_content.find("[/SUGGESTION]")
                        suggestion_content = suggestion_content[:end_idx]
                    if diff_initialized:
                        self._signals.show_diff_response.emit(
                            original_text,
                            suggestion_content,
                            selection_start if selection_start is not None else 0,
                            selection_end if selection_end is not None else 0,
                        )

        for chunk in llm_adapter.invoke_stream(prompt, on_chunk):
            if chunk.is_done:
                break

        self._signals.log_message.emit(
            f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 流式传输完成，响应长度: {len(full_response)}"
        )
        self._signals.close_notification.emit()

    def _create_llm_adapter(self):
        """
        创建 LLM 适配器实例

        Returns:
            LLM适配器实例，如果配置不存在则返回 None
        """
        loaded_config = self.home_tab.loaded_config
        llm_configs = loaded_config.get("llm_configs", {})

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

    def _on_log_message(self, message):
        """
        在主线程输出日志消息（信号槽）

        Args:
            message: 日志消息
        """
        self.home_tab.log(message)

    def _on_close_notification(self):
        """关闭处理中的通知（信号槽）"""
        if self._processing_notification:
            try:
                self._processing_notification.close()
                self._processing_notification = None
                self.home_tab.log(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 处理中通知已关闭"
                )
            except Exception as e:
                self.home_tab.log(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [AI] 关闭通知出错: {str(e)}"
                )
                self._processing_notification = None

    def _on_show_query_response(self, response):
        """
        在主线程显示查询响应（信号槽）

        Args:
            response: 查询响应内容
        """
        if self.response_widget and self.response_widget.isVisible():
            self.response_widget.append_response(response)
            self.response_widget.show()
        else:
            self._show_response_widget(response)

    def _show_response_widget(self, response: str):
        """
        显示Composer回答窗口

        Args:
            response: AI的回答内容
        """
        if self.response_widget:
            OverlayManager.hide_widget(
                self.home_tab, self.response_widget, "composer_response"
            )
            self.response_widget.deleteLater()

        self.response_widget = ComposerResponseWidget(response, self.home_tab)
        self.response_widget.follow_up_submitted.connect(self._on_follow_up_submitted)
        self.response_widget.closed.connect(self._on_response_closed)

        OverlayManager.show_widget(
            self.home_tab, self.response_widget, "composer_response"
        )

    def _on_follow_up_submitted(self, query: str):
        """
        处理继续追问

        Args:
            query: 用户追问内容
        """
        if self.response_widget:
            previous_response = self.response_widget.response
            self._conversation_context += (
                f"\n\nComposer之前的回答：\n{previous_response}\n\n用户追问：{query}"
            )
        self.process_ai_task("query", self._current_selected_text, query)

    def _on_response_closed(self):
        """处理回答窗口关闭"""
        self._conversation_context = ""

    def _on_show_diff_response(
        self, original_text, modified_text, selection_start, selection_end
    ):
        """
        在主线程显示差异预览（信号槽）

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本（可能包含SUGGESTION标签）
            selection_start: 选区开始位置（生成台不使用）
            selection_end: 选区结束位置（生成台不使用）
        """
        modified_text = strip_suggestion_tags(modified_text)
        if self.diff_preview_manager and self.diff_preview_manager.is_showing_diff():
            self.diff_preview_manager.set_modified_text(modified_text)
        else:
            self.show_diff_preview(
                original_text, modified_text, selection_start, selection_end
            )

    def _on_append_diff_content(self, content: str):
        """
        在主线程追加差异内容（流式传输时的信号槽）

        Args:
            content: 要追加的内容
        """
        if self.diff_preview_manager:
            self.diff_preview_manager.append_content(content)

    def show_diff_preview(
        self, original_text, modified_text, selection_start=None, selection_end=None
    ):
        """
        显示差异预览

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
            selection_start: 选区开始位置（可选）
            selection_end: 选区结束位置（可选）
        """
        editor = self._get_current_editor()
        if not editor:
            return

        diff_mode = get_diff_preview_mode_from_config(self.home_tab.loaded_config)

        if self.diff_preview_manager:
            self.diff_preview_manager.cleanup()

        self.diff_preview_manager = DiffPreviewManager(editor, self.home_tab, diff_mode)
        self.diff_preview_manager.changes_accepted.connect(self.apply_changes)
        self.diff_preview_manager.changes_rejected.connect(self.reject_changes)
        self.diff_preview_manager.show_diff(
            original_text, modified_text, selection_start, selection_end
        )

    def apply_changes(self, modified_text):
        """
        应用修改

        Args:
            modified_text: 修改后的文本
        """
        editor_key = self.get_current_active_editor()
        if not editor_key:
            return

        editor = None
        if editor_key == "step1":
            editor = self.home_tab.step1TextEdit
        elif editor_key == "step1Review":
            editor = self.home_tab.step1ReviewTextEdit
        elif editor_key == "step2":
            editor = self.home_tab.step2TextEdit
        elif editor_key == "main":
            editor = self.home_tab.editor

        if editor:
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(modified_text)
            cursor.endEditBlock()

            self._notify.success("", "修改已应用")

    def reject_changes(self):
        """
        拒绝修改
        """
        self._notify.info("", "修改已取消")
