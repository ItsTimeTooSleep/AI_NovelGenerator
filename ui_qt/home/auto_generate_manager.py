# -*- coding: utf-8 -*-
"""
自动生成管理器模块

负责自动生成配置、任务管理和进度跟踪。

主要功能:
- 显示自动生成配置对话框
- 启动/停止自动生成任务
- 跟踪生成进度
- 处理生成回调

使用示例:
    from ui_qt.home import AutoGenerateManager

    auto_gen = AutoGenerateManager(home_tab)
    auto_gen.initialize()
    auto_gen.show_config_dialog()
"""

import os
from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

from core.utils import check_file_has_valid_content

from ..core import BaseManager, EventBus, EventType
from ..utils.auto_generate import (
    AutoGenerateConfigDialog,
    AutoGenerateWorker,
)
from ..utils.generation_handlers import check_project_loaded
from ..utils.helpers import get_global_notify


class AutoGenerateManager(BaseManager):
    """
    自动生成管理器

    负责管理自动生成功能的所有交互，包括：
    - 配置对话框显示
    - 生成任务管理
    - 进度跟踪
    - 回调处理
    """

    def __init__(self, home_tab: QWidget):
        """
        初始化自动生成管理器

        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        super().__init__(home_tab)
        self._auto_generate_worker: Optional[AutoGenerateWorker] = None

    def initialize(self) -> None:
        """
        初始化自动生成管理器

        订阅事件总线，设置初始状态。
        """
        self._subscribe_events()
        self._initialized = True

    def _subscribe_events(self) -> None:
        """
        订阅事件总线事件
        """

    def show_config_dialog(self) -> None:
        """
        显示自动生成配置对话框
        """
        if not check_project_loaded(
            getattr(self.parent, "current_project_path", ""),
            self.parent.window() if hasattr(self.parent, "window") else None,
        ):
            return

        current_project = getattr(self.parent, "current_project", None)
        if not current_project:
            return

        project_status_manager = getattr(self.parent, "project_status_manager", None)
        if project_status_manager:
            if (
                not project_status_manager.is_step1_completed()
                or not project_status_manager.is_step2_completed()
            ):
                notify = get_global_notify()
                if notify:
                    notify.warning("提示", "请先完成第一步和第二步（生成架构和目录）")
                return
        else:
            step_status = current_project.get("step_status", {})
            if not step_status.get("step1_completed", False) or not step_status.get(
                "step2_completed", False
            ):
                notify = get_global_notify()
                if notify:
                    notify.warning("提示", "请先完成第一步和第二步（生成架构和目录）")
                return

        current_chapter = self._get_last_completed_chapter()
        total_plan = int(current_project.get("total_chapters_plan", 100))

        dialog = AutoGenerateConfigDialog(
            current_chapter=current_chapter,
            total_plan=total_plan,
            parent=self.parent.window() if hasattr(self.parent, "window") else None,
        )

        if dialog.exec():
            config = dialog.get_config()
            self.start_generation(config["start_chapter"], config["chapter_count"])

    def _get_last_completed_chapter(self) -> int:
        """
        获取最后一个已完成的章节号

        Returns:
            int: 已完成的章节号，0表示还没有完成任何章节
        """
        project_path = getattr(self.parent, "current_project_path", "")
        if not project_path:
            return 0

        chapters_dir = os.path.join(project_path, "chapters")
        if not os.path.exists(chapters_dir):
            return 0

        max_chapter = 0
        for filename in os.listdir(chapters_dir):
            if filename.startswith("chapter_") and filename.endswith(".txt"):
                try:
                    chapter_num = int(filename.split("_")[1].split(".")[0])
                    chap_file = os.path.join(chapters_dir, filename)
                    if check_file_has_valid_content(chap_file):
                        max_chapter = max(max_chapter, chapter_num)
                except (IndexError, ValueError):
                    continue

        return max_chapter

    def start_generation(self, start_chapter: int, chapter_count: int) -> None:
        """
        开始自动生成

        Args:
            start_chapter: 起始章节号
            chapter_count: 要生成的章节数量
        """
        if hasattr(self.parent, "log"):
            self.parent.log(
                f"开始自动生成：从第 {start_chapter} 章开始，共 {chapter_count} 章"
            )

        if hasattr(self.parent, "rightStack") and hasattr(
            self.parent, "autoGeneratePage"
        ):
            self.parent.rightStack.setCurrentWidget(self.parent.autoGeneratePage)

        if hasattr(self.parent, "autoGeneratePage"):
            self.parent.autoGeneratePage.reset(chapter_count, start_chapter)

        self._auto_generate_worker = AutoGenerateWorker(
            self.parent, start_chapter, chapter_count
        )

        self._connect_worker_signals()

        self._auto_generate_worker.start()

        event_bus = EventBus.get_instance()
        event_bus.publish(
            EventType.GENERATION_STARTED,
            source="AutoGenerateManager",
            start_chapter=start_chapter,
            chapter_count=chapter_count,
        )

    def _connect_worker_signals(self) -> None:
        """
        连接工作线程信号
        """
        if not self._auto_generate_worker:
            return

        self._auto_generate_worker.chapter_started.connect(
            self._on_auto_gen_chapter_started
        )
        self._auto_generate_worker.step_changed.connect(self._on_auto_gen_step_changed)
        self._auto_generate_worker.chapter_completed.connect(
            self._on_auto_gen_chapter_completed
        )
        self._auto_generate_worker.error_occurred.connect(self._on_auto_gen_error)
        self._auto_generate_worker.finished.connect(self._on_auto_gen_finished)

    def stop_generation(self) -> None:
        """
        停止自动生成
        """
        if self._auto_generate_worker and self._auto_generate_worker.isRunning():
            if hasattr(self.parent, "log"):
                self.parent.log("正在停止自动生成...")
            self._auto_generate_worker.cancel()

    def is_running(self) -> bool:
        """
        是否正在运行

        Returns:
            bool: True表示正在运行
        """
        return (
            self._auto_generate_worker is not None
            and self._auto_generate_worker.isRunning()
        )

    def _on_auto_gen_chapter_started(self, chapter_num: int) -> None:
        """
        章节开始生成时的回调

        Args:
            chapter_num: 章节号
        """
        if hasattr(self.parent, "autoGeneratePage"):
            self.parent.autoGeneratePage.update_chapter(chapter_num)
        if hasattr(self.parent, "log"):
            self.parent.log(f"开始生成第 {chapter_num} 章")

    def _on_auto_gen_step_changed(self, step_name: str) -> None:
        """
        步骤变化时的回调

        Args:
            step_name: 步骤名称
        """
        if hasattr(self.parent, "autoGeneratePage"):
            self.parent.autoGeneratePage.update_step(step_name)
        if hasattr(self.parent, "log"):
            self.parent.log(step_name)

    def _on_auto_gen_chapter_completed(self, chapter_num: int) -> None:
        """
        章节完成时的回调

        Args:
            chapter_num: 章节号
        """
        if hasattr(self.parent, "autoGeneratePage"):
            self.parent.autoGeneratePage.add_completed_chapter(chapter_num)
        if hasattr(self.parent, "log"):
            self.parent.log(f"✅ 第 {chapter_num} 章完成")

        if hasattr(self.parent, "check_project_files"):
            self.parent.check_project_files()

    def _on_auto_gen_error(self, error_msg: str) -> None:
        """
        错误发生时的回调

        Args:
            error_msg: 错误信息
        """
        if hasattr(self.parent, "log"):
            self.parent.log(f"❌ 错误：{error_msg}")
        notify = get_global_notify()
        if notify:
            notify.error("错误", error_msg)

        event_bus = EventBus.get_instance()
        event_bus.publish(
            EventType.GENERATION_ERROR,
            source="AutoGenerateManager",
            error_msg=error_msg,
        )

    def _on_auto_gen_finished(self, success: bool) -> None:
        """
        自动生成完成时的回调

        Args:
            success: 是否成功
        """
        if hasattr(self.parent, "autoGeneratePage"):
            self.parent.autoGeneratePage.set_finished(success)

        notify = get_global_notify()
        if success:
            if hasattr(self.parent, "log"):
                self.parent.log("✅ 自动生成完成")
            if notify:
                notify.success("完成", "所有章节已生成完毕")
            event_bus = EventBus.get_instance()
            event_bus.publish(
                EventType.GENERATION_FINISHED,
                source="AutoGenerateManager",
                success=True,
            )
        else:
            if hasattr(self.parent, "log"):
                self.parent.log("自动生成已停止")
            event_bus = EventBus.get_instance()
            event_bus.publish(
                EventType.GENERATION_FINISHED,
                source="AutoGenerateManager",
                success=False,
            )

        QTimer.singleShot(2000, self._return_to_main_page)

    def _return_to_main_page(self) -> None:
        """
        返回主页面
        """
        if hasattr(self.parent, "check_project_files"):
            self.parent.check_project_files()

    def cleanup(self) -> None:
        """
        清理资源

        停止工作线程，取消事件订阅。
        """
        if self._auto_generate_worker and self._auto_generate_worker.isRunning():
            self._auto_generate_worker.cancel()
            self._auto_generate_worker.wait()
