# -*- coding: utf-8 -*-
"""
进度管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责管理生成流程中的进度显示和状态更新，包括进度条控制、
步骤状态展示、耗时统计等功能。

================================================================================
核心类
================================================================================
- ProgressManager: 进度管理器

================================================================================
核心功能
================================================================================
- show_step_detail: 显示步骤详情对话框
- update_step_progress: 更新步骤进度
- show_completion_message: 显示完成消息
- show_error_message: 显示错误消息

================================================================================
进度显示
================================================================================
- 进度条动画控制
- 步骤完成状态标记
- 耗时统计显示
- 日志信息汇总

================================================================================
设计决策
================================================================================
- 使用MessageBoxBase显示详情对话框
- 优先显示AI输出内容
- 无AI输出时显示状态和日志
- 支持只读模式查看历史记录

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import time

from qfluentwidgets import MessageBoxBase, SubtitleLabel, TextEdit

from ..utils.helpers import get_global_notify


class ProgressManager:
    def __init__(self, home_tab):
        self.home_tab = home_tab

    def _get_step1_data_key(self, step_name: str) -> str:
        """
        获取 Step 1 步骤名称对应的数据键名

        Args:
            step_name: 步骤名称

        Returns:
            str: 数据键名，如果未找到则返回空字符串
        """
        step_name_to_key = {
            "书名生成": "generated_title",
            "核心种子生成": "core_seed_result",
            "角色动力学构建": "character_dynamics_result",
            "初始角色状态生成": "character_state_result",
            "世界观搭建": "world_building_result",
            "情节架构设计": "plot_arch_result",
        }
        return step_name_to_key.get(step_name, "")

    def _get_step2_data_key(self, step_name: str) -> str:
        """
        获取 Step 2 步骤名称对应的数据键名

        Args:
            step_name: 步骤名称

        Returns:
            str: 数据键名，如果未找到则返回空字符串
        """
        step_name_to_key = {
            "生成章节目录": "directory_result",
        }
        return step_name_to_key.get(step_name, "")

    def show_step_detail(self, step_widget):
        """
        显示步骤详情
        如果有AI输出内容，优先显示AI输出；否则显示状态和日志

        Args:
            step_widget: 步骤组件对象
        """
        dialog = MessageBoxBase(self.home_tab.window())
        dialog.titleLabel = SubtitleLabel(f"{step_widget.step_name} - 详情", dialog)
        dialog.textDisplay = TextEdit(dialog)

        # 如果有AI输出，只显示AI输出
        if step_widget.ai_output:
            detail_text = step_widget.ai_output
        else:
            # 没有AI输出时，显示状态和日志
            logs = step_widget.get_logs()
            status_text = ""
            if step_widget.is_completed:
                status_text = "状态: 已完成 ✓"
            elif step_widget.is_active:
                status_text = "状态: 进行中 ●"
            else:
                status_text = "状态: 等待中 ○"

            detail_text = f"{status_text}\n"
            if step_widget.elapsed_time > 0:
                detail_text += f"耗时: {step_widget.elapsed_time:.1f}s\n"
            detail_text += "\n"

            if logs:
                detail_text += "=== 日志 ===\n"
                detail_text += "\n".join(logs)
            else:
                detail_text += "暂无日志信息"

        dialog.textDisplay.setPlainText(detail_text)
        dialog.textDisplay.setReadOnly(True)
        dialog.textDisplay.setMinimumHeight(300)
        dialog.textDisplay.setMinimumWidth(500)
        dialog.viewLayout.addWidget(dialog.titleLabel)
        dialog.viewLayout.addWidget(dialog.textDisplay)
        dialog.yesButton.setText("关闭")
        dialog.cancelButton.setVisible(False)
        dialog.widget.setMinimumWidth(550)
        dialog.exec()

    def retry_step1_step(self, step_index):
        """
        重试Step 1的指定步骤

        Args:
            step_index: 步骤索引（0-based）

        Returns:
            无

        Raises:
            无
        """
        step_names = [
            "书名生成",
            "核心种子生成",
            "角色动力学构建",
            "初始角色状态生成",
            "世界观搭建",
            "情节架构设计",
        ]
        step_name = (
            step_names[step_index]
            if 0 <= step_index < len(step_names)
            else f"步骤{step_index + 1}"
        )
        self.home_tab.log(f"准备重试 Step 1 的步骤: {step_name} (第{step_index + 1}步)")

        if 0 <= step_index < len(self.home_tab.step1ProgressWidgets):
            step_widget = self.home_tab.step1ProgressWidgets[step_index]
            step_widget.reset()
            step_widget.set_visible(True, animate=False)

            self.home_tab.step1ProgressContainer.show()

            completed_indices = [
                i
                for i in range(len(self.home_tab.step1ProgressWidgets))
                if self.home_tab.step1ProgressWidgets[i].is_completed
                and i != step_index
            ]
            self.home_tab.step1ProgressContainer.update_line_state(
                step_index, completed_indices
            )

            self._trigger_step1_retry_from_step(step_index)
        notify = get_global_notify()
        if notify:
            notify.info("提示", f"正在重试: {step_name}")

    def _trigger_step1_retry_from_step(self, step_index):
        """
        从指定步骤开始重新执行Step 1

        Args:
            step_index: 起始步骤索引（0-based）

        Returns:
            无

        Raises:
            无
        """
        import os
        import json

        project_path = self.home_tab.current_project_path
        if not project_path:
            return

        partial_file = os.path.join(project_path, "partial_architecture.json")
        if not os.path.exists(partial_file):
            self.home_tab.log("无法重试：未找到部分架构文件")
            return

        try:
            with open(partial_file, "r", encoding="utf-8") as f:
                partial_data = json.load(f)

            keys_to_remove = [
                "generated_title",
                "core_seed_result",
                "character_dynamics_result",
                "character_state_result",
                "world_building_result",
                "plot_arch_result",
            ]

            for i in range(step_index, len(keys_to_remove)):
                if keys_to_remove[i] in partial_data:
                    del partial_data[keys_to_remove[i]]

            with open(partial_file, "w", encoding="utf-8") as f:
                json.dump(partial_data, f, ensure_ascii=False, indent=2)

            self.home_tab.log(f"已清除从第{step_index + 1}步开始的数据，准备重新生成")

            self._start_step1_from_retry()

        except Exception as e:
            self.home_tab.log(f"重试准备失败: {e}")

    def _start_step1_from_retry(self):
        """
        从重试状态启动Step 1生成

        Args:
            无

        Returns:
            无

        Raises:
            无
        """
        if hasattr(self.home_tab, "generation_flow"):
            self.home_tab.generation_flow.on_step1()

    def on_step1_progress(self, step_name, status_msg, duration):
        """
        处理Step 1的进度更新
        当步骤完成时，从partial_architecture.json中读取该步骤的原始LLM响应并设置到step_widget.ai_output

        Args:
            step_name: 步骤名称
            status_msg: 状态信息
            duration: 耗时
        """
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [{step_name}] {status_msg}"

        if duration > 0.1:
            msg += f" (耗时: {duration:.1f}s)"
        self.home_tab.log(msg)

        if step_name == "初始化":
            self.home_tab.step1ProgressContainer.show()
            return

        step_index_map = {
            "书名生成": 0,
            "核心种子生成": 1,
            "角色动力学构建": 2,
            "初始角色状态生成": 3,
            "世界观搭建": 4,
            "情节架构设计": 5,
        }

        if step_name in step_index_map:
            idx = step_index_map[step_name]
            if 0 <= idx < len(self.home_tab.step1ProgressWidgets):
                step_widget = self.home_tab.step1ProgressWidgets[idx]

                step_widget.add_log(msg)

                if "正在" in status_msg:
                    step_widget.set_visible(True, animate=False)
                    step_widget.set_active(True)

                    for i in range(idx):
                        prev_step = self.home_tab.step1ProgressWidgets[i]
                        prev_step.set_active(False)
                        if not prev_step.is_completed:
                            prev_step.set_completed(True)

                    completed_indices = [
                        i
                        for i in range(len(self.home_tab.step1ProgressWidgets))
                        if self.home_tab.step1ProgressWidgets[i].is_completed
                    ]

                    self.home_tab.step1ProgressContainer.update_line_state(
                        idx, completed_indices
                    )
                elif "完成" in status_msg or "Done" in status_msg:
                    step_widget.set_active(False)
                    step_widget.set_completed(True, auto_expand=True)
                    step_widget.elapsed_time = duration
                    step_widget.timer_label.setText(f"{duration:.1f}s")
                    step_widget.timer_label.show()

                    import json
                    import os

                    partial_file = os.path.join(
                        self.home_tab.current_project_path, "partial_architecture.json"
                    )
                    if os.path.exists(partial_file):
                        try:
                            with open(partial_file, "r", encoding="utf-8") as f:
                                partial_data = json.load(f)

                            result_key_map = {
                                "书名生成": "generated_title",
                                "核心种子生成": "core_seed_result",
                                "角色动力学构建": "character_dynamics_result",
                                "初始角色状态生成": "character_state_result",
                                "世界观搭建": "world_building_result",
                                "情节架构设计": "plot_arch_result",
                            }

                            if step_name in result_key_map:
                                result_key = result_key_map[step_name]
                                if result_key in partial_data:
                                    step_widget.set_ai_output(partial_data[result_key])
                        except Exception as e:
                            self.home_tab.log(f"读取partial_architecture.json失败: {e}")

                    for i in range(idx + 1):
                        prev_step = self.home_tab.step1ProgressWidgets[i]
                        if not prev_step.is_completed:
                            prev_step.set_completed(True)

                    completed_indices = [
                        i
                        for i in range(len(self.home_tab.step1ProgressWidgets))
                        if self.home_tab.step1ProgressWidgets[i].is_completed
                    ]

                    self.home_tab.step1ProgressContainer.update_line_state(
                        -1, completed_indices
                    )

                    from PyQt5.QtCore import QTimer

                    QTimer.singleShot(50, lambda: step_widget.timer_label.show())

                    if hasattr(self.home_tab, "project_status_manager"):
                        try:
                            step_data_key = self._get_step1_data_key(step_name)
                            if step_data_key:
                                self.home_tab.project_status_manager.update_step1_progress(
                                    step_index=idx,
                                    step_name=step_name,
                                    step_time=duration,
                                    step_data_key=step_data_key,
                                    step_data_value="",
                                )
                        except Exception as e:
                            self.home_tab.log(f"保存时间记录失败: {e}")

                elif "失败" in status_msg:
                    step_widget.set_active(False)
                    step_widget.set_cancelled(True)
                    step_widget.timer_label.show()

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
                    self.home_tab.step1ProgressContainer.update_line_state(
                        -1, completed_indices, cancelled_indices
                    )

        if "完成" in status_msg or "Done" in status_msg:
            notify = get_global_notify()
            if notify:
                notify.success(step_name, f"已完成 (耗时 {duration:.1f}s)")

    def retry_step2_step(self, step_index):
        """
        重试Step 2的指定步骤

        Args:
            step_index: 步骤索引（0-based）

        Returns:
            无

        Raises:
            无
        """
        step_names = [
            "章节目录生成",
        ]
        step_name = (
            step_names[step_index]
            if 0 <= step_index < len(step_names)
            else f"步骤{step_index + 1}"
        )
        self.home_tab.log(f"准备重试 Step 2 的步骤: {step_name} (第{step_index + 1}步)")

        if 0 <= step_index < len(self.home_tab.step2ProgressWidgets):
            step_widget = self.home_tab.step2ProgressWidgets[step_index]
            step_widget.reset()
            step_widget.set_visible(True, animate=False)

            self.home_tab.step2ProgressContainer.show()

            completed_indices = [
                i
                for i in range(len(self.home_tab.step2ProgressWidgets))
                if self.home_tab.step2ProgressWidgets[i].is_completed
                and i != step_index
            ]
            self.home_tab.step2ProgressContainer.update_line_state(
                step_index, completed_indices
            )

            self._trigger_step2_retry_from_step(step_index)
        notify = get_global_notify()
        if notify:
            notify.info("提示", f"正在重试: {step_name}")

    def _trigger_step2_retry_from_step(self, step_index):
        """
        从指定步骤开始重新执行Step 2

        Args:
            step_index: 起始步骤索引（0-based）

        Returns:
            无

        Raises:
            无
        """
        import os

        project_path = self.home_tab.current_project_path
        if not project_path:
            return

        dir_file = os.path.join(project_path, "Novel_directory.txt")
        if os.path.exists(dir_file):
            try:
                os.remove(dir_file)
                self.home_tab.log(f"已清除章节目录文件，准备重新生成")
            except Exception as e:
                self.home_tab.log(f"删除章节目录文件失败: {e}")

        self._start_step2_from_retry()

    def _start_step2_from_retry(self):
        """
        从重试状态启动Step 2生成

        Args:
            无

        Returns:
            无

        Raises:
            无
        """
        if hasattr(self.home_tab, "generation_flow"):
            self.home_tab.generation_flow.on_step2()

    def on_step2_progress(self, step_name, status_msg, duration):
        """
        处理Step 2的进度更新
        当步骤完成时，从Novel_directory.txt中读取结果并设置到step_widget.ai_output

        Args:
            step_name: 步骤名称
            status_msg: 状态信息
            duration: 耗时
        """
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [{step_name}] {status_msg}"

        if duration > 0.1:
            msg += f" (耗时: {duration:.1f}s)"
        self.home_tab.log(msg)

        if step_name == "初始化":
            self.home_tab.step2ProgressContainer.show()
            return

        step_index_map = {
            "章节目录生成": 0,
        }

        if step_name in step_index_map:
            idx = step_index_map[step_name]
            if 0 <= idx < len(self.home_tab.step2ProgressWidgets):
                step_widget = self.home_tab.step2ProgressWidgets[idx]

                step_widget.add_log(msg)

                if "正在" in status_msg:
                    step_widget.set_visible(True, animate=False)
                    step_widget.set_active(True)

                    for i in range(idx):
                        prev_step = self.home_tab.step2ProgressWidgets[i]
                        prev_step.set_active(False)
                        if not prev_step.is_completed:
                            prev_step.set_completed(True)

                    completed_indices = [
                        i
                        for i in range(len(self.home_tab.step2ProgressWidgets))
                        if self.home_tab.step2ProgressWidgets[i].is_completed
                    ]

                    self.home_tab.step2ProgressContainer.update_line_state(
                        idx, completed_indices
                    )
                elif "完成" in status_msg or "Done" in status_msg:
                    step_widget.set_active(False)
                    step_widget.set_completed(True, auto_expand=True)
                    step_widget.elapsed_time = duration
                    step_widget.timer_label.setText(f"{duration:.1f}s")
                    step_widget.timer_label.show()

                    import os

                    dir_file = os.path.join(
                        self.home_tab.current_project_path, "Novel_directory.txt"
                    )
                    if os.path.exists(dir_file):
                        try:
                            from core.utils import read_file

                            dir_content = read_file(dir_file)
                            step_widget.set_ai_output(dir_content)
                        except Exception as e:
                            self.home_tab.log(f"读取Novel_directory.txt失败: {e}")

                    for i in range(idx + 1):
                        prev_step = self.home_tab.step2ProgressWidgets[i]
                        if not prev_step.is_completed:
                            prev_step.set_completed(True)

                    completed_indices = [
                        i
                        for i in range(len(self.home_tab.step2ProgressWidgets))
                        if self.home_tab.step2ProgressWidgets[i].is_completed
                    ]

                    self.home_tab.step2ProgressContainer.update_line_state(
                        -1, completed_indices
                    )

                    from PyQt5.QtCore import QTimer

                    QTimer.singleShot(50, lambda: step_widget.timer_label.show())

                    if hasattr(self.home_tab, "project_status_manager"):
                        try:
                            step_data_key = self._get_step2_data_key(step_name)
                            if step_data_key:
                                self.home_tab.project_status_manager.update_step2_progress(
                                    step_index=idx,
                                    step_name=step_name,
                                    step_time=duration,
                                    step_data_key=step_data_key,
                                    step_data_value="",
                                )
                        except Exception as e:
                            self.home_tab.log(f"保存时间记录失败: {e}")

                elif "失败" in status_msg:
                    step_widget.set_active(False)
                    step_widget.set_cancelled(True)
                    step_widget.timer_label.show()

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
                    self.home_tab.step2ProgressContainer.update_line_state(
                        -1, completed_indices, cancelled_indices
                    )

        if "完成" in status_msg or "Done" in status_msg:
            notify = get_global_notify()
            if notify:
                notify.success(step_name, f"已完成 (耗时 {duration:.1f}s)")
        elif "失败" in status_msg:
            notify = get_global_notify()
            if notify:
                notify.error(step_name, status_msg)
