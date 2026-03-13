# -*- coding: utf-8 -*-
"""
流式传输管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责管理文本的流式显示，支持两种模式：
- 真实流式模式：直接处理来自API的实时流式数据
- 模拟流式模式：将完整文本分块逐步显示

================================================================================
核心类
================================================================================
- StreamingManager: 流式传输管理器

================================================================================
核心功能
================================================================================
- start_real_stream: 启动真实流式显示（直接追加文本）
- _start_stream: 启动模拟流式显示（分块显示已有文本）
- stop_active_stream: 停止当前流式传输

================================================================================
设计决策
================================================================================
- 支持两种流式模式，根据场景灵活选择
- 真实流式用于API实时响应，模拟流式用于已有文本展示
- 集成自动保存功能，流式完成后触发保存

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from PyQt5.QtCore import QTimer

from core.config_manager import load_config


class StreamingManager:
    """
    流式传输管理器

    负责管理文本的流式显示，支持真实流式和模拟流式两种模式。
    """

    def __init__(self, home_tab):
        """
        初始化StreamingManager

        Args:
            home_tab: HomeTab主窗口实例
        """
        self.home_tab = home_tab
        self.streamTimer = QTimer(self.home_tab)
        self.streamTimer.timeout.connect(self._update_stream)
        self._stream_target = None
        self._stream_text = ""
        self._stream_pos = 0
        self._streaming = False
        self._stream_stop_btn = None
        self._stream_chunk_size = 8
        self._stream_interval = 25
        self._real_streaming = False
        self._stream_on_complete = None

    def _set_widget_text(self, widget, text: str):
        """
        设置控件文本

        Args:
            widget: 目标控件
            text: 要设置的文本
        """
        if hasattr(widget, "setPlainText"):
            widget.setPlainText(text)
        elif hasattr(widget, "setText"):
            widget.setText(text)

    def _append_to_widget(self, widget, text: str):
        """
        向控件追加文本

        Args:
            widget: 目标控件
            text: 要追加的文本
        """
        if hasattr(widget, "textCursor"):
            cursor = widget.textCursor()
            cursor.movePosition(cursor.End)
            widget.setTextCursor(cursor)
            widget.insertPlainText(text)
        elif hasattr(widget, "setPlainText"):
            existing = widget.toPlainText() if hasattr(widget, "toPlainText") else ""
            widget.setPlainText(existing + text)
        elif hasattr(widget, "setText"):
            existing = widget.text() if hasattr(widget, "text") else ""
            widget.setText(existing + text)

        if hasattr(widget, "verticalScrollBar"):
            sb = widget.verticalScrollBar()
            sb.setValue(sb.maximum())

    def start_real_stream(self, target_widget, stop_button=None):
        """
        启动真实流式模式（用于API实时响应）

        Args:
            target_widget: 目标显示控件
            stop_button: 停止按钮（可选）

        Returns:
            callable: 用于追加文本的回调函数
        """
        if not target_widget:
            return None

        self.home_tab.loaded_config = (
            load_config(self.home_tab.config_file) or self.home_tab.loaded_config
        )
        self.home_tab.streaming_enabled = self.home_tab.loaded_config.get(
            "streaming_enabled", True
        )

        self._stream_target = target_widget
        self._stream_stop_btn = stop_button
        self._real_streaming = True
        self._streaming = False

        if hasattr(target_widget, "clear"):
            target_widget.clear()
        if hasattr(target_widget, "setReadOnly"):
            target_widget.setReadOnly(True)
        target_widget.show()

        if stop_button:
            stop_button.setVisible(True)
            stop_button.setEnabled(True)

        def append_chunk(text: str):
            """追加流式文本块的回调函数"""
            if not self._real_streaming:
                return
            self._append_to_widget(target_widget, text)

        return append_chunk

    def finish_real_stream(self):
        """
        完成真实流式传输
        """
        self._real_streaming = False

        if self._stream_stop_btn:
            self._stream_stop_btn.hide()
        if hasattr(self._stream_target, "setReadOnly"):
            self._stream_target.setReadOnly(False)

        if hasattr(self.home_tab, "autosave_manager"):
            if (
                hasattr(self.home_tab, "step1TextEdit")
                and self._stream_target is self.home_tab.step1TextEdit
            ):
                self.home_tab.autosave_manager._schedule_step1_autosave(
                    self.home_tab.step1TextEdit
                )
            elif (
                hasattr(self.home_tab, "step2TextEdit")
                and self._stream_target is self.home_tab.step2TextEdit
            ):
                self.home_tab.autosave_manager._schedule_step2_autosave()

    def _start_stream(
        self,
        target_widget,
        text: str,
        stop_button=None,
        interval: int = 25,
        chunk_size: int = 8,
        on_complete=None,
    ):
        """
        启动模拟流式模式（用于已有文本的分块显示）

        Args:
            target_widget: 目标显示控件
            text: 要显示的完整文本
            stop_button: 停止按钮（可选）
            interval: 更新间隔（毫秒）
            chunk_size: 每次显示的字符数
            on_complete: 流式显示完成后的回调函数（可选）
        """
        if not target_widget:
            return

        self.home_tab.loaded_config = (
            load_config(self.home_tab.config_file) or self.home_tab.loaded_config
        )
        self.home_tab.streaming_enabled = self.home_tab.loaded_config.get(
            "streaming_enabled", True
        )

        if not text:
            if stop_button:
                stop_button.hide()
            return

        if not self.home_tab.streaming_enabled:
            if hasattr(target_widget, "clear"):
                target_widget.clear()
            self._set_widget_text(target_widget, text)
            if hasattr(target_widget, "setReadOnly"):
                target_widget.setReadOnly(False)
            if stop_button:
                stop_button.hide()
            return

        self._stream_target = target_widget
        self._stream_text = text
        self._stream_pos = 0
        self._streaming = True
        self._real_streaming = False
        self._stream_stop_btn = stop_button
        self._stream_chunk_size = max(1, chunk_size)
        self._stream_interval = max(10, interval)
        self._stream_on_complete = on_complete

        if hasattr(target_widget, "clear"):
            target_widget.clear()
        if hasattr(target_widget, "setReadOnly"):
            target_widget.setReadOnly(True)
        target_widget.show()

        if stop_button:
            stop_button.setVisible(True)
            stop_button.setEnabled(True)

        self.streamTimer.start(self._stream_interval)

    def _update_stream(self):
        """
        更新模拟流式显示（定时器回调）
        """
        if not self._streaming or not self._stream_target:
            self.streamTimer.stop()
            return

        if self._stream_pos >= len(self._stream_text):
            self._streaming = False
            self.streamTimer.stop()
            if self._stream_stop_btn:
                self._stream_stop_btn.hide()
            if hasattr(self._stream_target, "setReadOnly"):
                self._stream_target.setReadOnly(False)

            if hasattr(self.home_tab, "autosave_manager"):
                if (
                    hasattr(self.home_tab, "step1TextEdit")
                    and self._stream_target is self.home_tab.step1TextEdit
                ):
                    self.home_tab.autosave_manager._schedule_step1_autosave(
                        self.home_tab.step1TextEdit
                    )
                elif (
                    hasattr(self.home_tab, "step2TextEdit")
                    and self._stream_target is self.home_tab.step2TextEdit
                ):
                    self.home_tab.autosave_manager._schedule_step2_autosave()

            if self._stream_on_complete:
                self._stream_on_complete()
                self._stream_on_complete = None

            return

        end_pos = min(
            len(self._stream_text), self._stream_pos + self._stream_chunk_size
        )
        new_text = self._stream_text[self._stream_pos : end_pos]
        self._stream_pos = end_pos

        if not new_text:
            return

        target = self._stream_target
        if hasattr(target, "textCursor"):
            cursor = target.textCursor()
            cursor.movePosition(cursor.End)
            target.setTextCursor(cursor)
            target.insertPlainText(new_text)
        elif hasattr(target, "setPlainText"):
            existing = target.toPlainText() if hasattr(target, "toPlainText") else ""
            target.setPlainText(existing + new_text)
        elif hasattr(target, "setText"):
            existing = target.text() if hasattr(target, "text") else ""
            target.setText(existing + new_text)

        if hasattr(target, "verticalScrollBar"):
            sb = target.verticalScrollBar()
            sb.setValue(sb.maximum())

    def stop_active_stream(self):
        """
        停止当前活动的流式传输
        """
        if self._streaming:
            self._streaming = False
            self.streamTimer.stop()
        if self._real_streaming:
            self._real_streaming = False

        if self._stream_stop_btn:
            self._stream_stop_btn.hide()

        if hasattr(self.home_tab, "step1ProgressWidgets"):
            for step_widget in self.home_tab.step1ProgressWidgets:
                if step_widget.is_active and not step_widget.is_completed:
                    step_widget.set_cancelled(True)

            completed_indices = [
                i
                for i in range(len(self.home_tab.step1ProgressWidgets))
                if self.home_tab.step1ProgressWidgets[i].is_completed
            ]
            cancelled_indices = [
                i
                for i in range(len(self.home_tab.step1ProgressWidgets))
                if self.home_tab.step1ProgressWidgets[i].is_cancelled
            ]
            if hasattr(self.home_tab, "step1ProgressContainer"):
                self.home_tab.step1ProgressContainer.update_line_state(
                    -1, completed_indices, cancelled_indices
                )

        if hasattr(self.home_tab, "step2ProgressWidgets"):
            for step_widget in self.home_tab.step2ProgressWidgets:
                if step_widget.is_active and not step_widget.is_completed:
                    step_widget.set_cancelled(True)

            completed_indices = [
                i
                for i in range(len(self.home_tab.step2ProgressWidgets))
                if self.home_tab.step2ProgressWidgets[i].is_completed
            ]
            cancelled_indices = [
                i
                for i in range(len(self.home_tab.step2ProgressWidgets))
                if self.home_tab.step2ProgressWidgets[i].is_cancelled
            ]
            if hasattr(self.home_tab, "step2ProgressContainer"):
                self.home_tab.step2ProgressContainer.update_line_state(
                    -1, completed_indices, cancelled_indices
                )

        if (
            hasattr(self.home_tab, "worker")
            and self.home_tab.worker
            and self.home_tab.worker.isRunning()
        ):
            self.home_tab.worker.cancel()

        self.home_tab.log("⏹ 已终止当前生成")

    def is_streaming(self) -> bool:
        """
        检查是否正在进行流式传输

        Returns:
            bool: 是否正在流式传输
        """
        return self._streaming or self._real_streaming
