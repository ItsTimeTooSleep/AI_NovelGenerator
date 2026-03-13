# -*- coding: utf-8 -*-
"""
章节加载器模块

负责章节内容的加载、保存和编辑器自动保存功能。

主要功能:
- 章节内容加载
- 加载状态管理
- 编辑器自动保存
- 加载中的UI提示

使用示例:
    from ui_qt.home import ChapterLoader

    loader = ChapterLoader(home_tab)
    loader.initialize()
    content = loader.load_chapter(5)
    loader.save_chapter(5, "New content")
"""

import os
from typing import Optional

from PyQt5.QtWidgets import QWidget

from core.utils import read_file

from ..core import BaseManager, EventBus, EventType


class ChapterLoader(BaseManager):
    """
    章节加载器

    负责管理章节的加载、保存和相关状态。
    """

    def __init__(self, home_tab: QWidget):
        """
        初始化章节加载器

        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        super().__init__(home_tab)
        self._is_loading_chapter: bool = False
        self._chapter_load_timer: Optional[object] = None
        self._loading_chapter_num: Optional[int] = None

    def initialize(self) -> None:
        """
        初始化章节加载器

        订阅事件总线，设置初始状态。
        """
        self._subscribe_events()
        self._initialized = True

    def _subscribe_events(self) -> None:
        """
        订阅事件总线事件
        """
        event_bus = EventBus.get_instance()
        event_bus.subscribe(EventType.PROJECT_LOADED, self._on_project_loaded)

    def _on_project_loaded(self, event) -> None:
        """
        处理项目加载事件

        Args:
            event: 事件对象
        """

    def load_chapter(self, chapter_num: int) -> Optional[str]:
        """
        加载指定章节的内容

        Args:
            chapter_num: 章节号

        Returns:
            Optional[str]: 章节内容，如果加载失败返回None
        """
        self._is_loading_chapter = True
        self.show_loading_indicator(chapter_num)

        content = self._load_chapter_content(chapter_num)

        self._is_loading_chapter = False
        return content

    def _load_chapter_content(self, chapter_num: int) -> Optional[str]:
        """
        加载章节内容（内部方法）

        Args:
            chapter_num: 章节号

        Returns:
            Optional[str]: 章节内容
        """
        if not hasattr(self.parent, "current_project_path"):
            self._set_editor_text("没有打开的项目")
            return None

        project_path = self.parent.current_project_path
        if not project_path:
            self._set_editor_text("没有打开的项目")
            return None

        chap_file = os.path.join(project_path, "chapters", f"chapter_{chapter_num}.txt")

        if not os.path.exists(chap_file):
            self._set_editor_text(f"第{chapter_num}章还未生成，请先生成草稿")
            return None

        try:
            text = read_file(chap_file)
            if text and text.strip():
                self._set_editor_text(text)
                return text
            else:
                self._set_editor_text(f"第{chapter_num}章内容为空")
                return None
        except Exception as e:
            error_msg = f"加载失败: {str(e)}"
            self._set_editor_text(error_msg)
            self._log(error_msg)
            return None

    def save_chapter(self, chapter_num: int, content: str) -> bool:
        """
        保存章节内容

        Args:
            chapter_num: 章节号
            content: 要保存的内容

        Returns:
            bool: 是否保存成功
        """
        if self._is_loading_chapter:
            return False

        if not hasattr(self.parent, "current_project_path"):
            return False

        project_path = self.parent.current_project_path
        if not project_path:
            return False

        chapters_dir = os.path.join(project_path, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)

        chap_file = os.path.join(chapters_dir, f"chapter_{chapter_num}.txt")

        try:
            with open(chap_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            self._log(f"保存章节失败: {e}")
            return False

    def show_loading_indicator(self, chapter_num: int) -> None:
        """
        显示加载中的提示

        Args:
            chapter_num: 章节号
        """
        if not getattr(self.parent, "_entered_full_layout", False):
            return

        self._set_editor_text(f"正在加载第{chapter_num}章...")

    def on_chapter_spin_changed(self, chapter_num: int) -> None:
        """
        章节选择器变化时的处理

        Args:
            chapter_num: 新的章节号
        """
        self._loading_chapter_num = chapter_num
        self.load_chapter(chapter_num)

        event_bus = EventBus.get_instance()
        event_bus.publish(
            EventType.CHAPTER_CHANGED, source="ChapterLoader", chapter_num=chapter_num
        )

    def on_editor_content_changed(self) -> None:
        """
        编辑器内容变化时的处理函数

        用于自动保存章节内容。
        """
        if self._is_loading_chapter:
            return

        if not hasattr(self.parent, "current_project_path"):
            return

        if not self.parent.current_project_path:
            return

        if not getattr(self.parent, "_entered_full_layout", False):
            return

        if not hasattr(self.parent, "currChapterSpin"):
            return

        chap_num = self.parent.currChapterSpin.value()

        if not hasattr(self.parent, "editor"):
            return

        text = self.parent.editor.toPlainText()

        self.save_chapter(chap_num, text)

    def _set_editor_text(self, text: str, suppress_autosave: bool = True) -> None:
        """
        设置编辑器文本

        Args:
            text: 要设置的文本
            suppress_autosave: 是否阻止自动保存，默认为True
        """
        if hasattr(self.parent, "editor"):
            should_manage_flag = suppress_autosave and not self._is_loading_chapter
            if should_manage_flag:
                self._is_loading_chapter = True
            try:
                self.parent.editor.setPlainText(text)
            finally:
                if should_manage_flag:
                    self._is_loading_chapter = False

    def _log(self, message: str) -> None:
        """
        输出日志

        Args:
            message: 日志消息
        """
        if hasattr(self.parent, "log"):
            self.parent.log(message)

    @property
    def is_loading(self) -> bool:
        """
        是否正在加载章节

        Returns:
            bool: True表示正在加载
        """
        return self._is_loading_chapter

    def cleanup(self) -> None:
        """
        清理资源

        取消事件订阅。
        """
        event_bus = EventBus.get_instance()
        event_bus.unsubscribe(EventType.PROJECT_LOADED, self._on_project_loaded)
