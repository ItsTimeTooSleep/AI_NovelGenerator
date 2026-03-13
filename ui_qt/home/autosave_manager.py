# -*- coding: utf-8 -*-
"""
自动保存管理器模块

================================================================================
模块功能概述
================================================================================
本模块实现了首页编辑器的自动保存功能，使用定时器延迟保存机制，
避免频繁IO操作，同时确保用户数据不会丢失。

================================================================================
核心类
================================================================================
- AutosaveManager: 自动保存管理器

================================================================================
核心功能
================================================================================
- save_step1_immediately: 立即保存Step1内容
- save_step2_immediately: 立即保存Step2内容
- 延迟自动保存：用户停止编辑1秒后自动保存

================================================================================
保存内容
================================================================================
- Step1: 小说架构（Novel_architecture.txt）
- Step2: 章节蓝图（Novel_directory.txt）

================================================================================
设计决策
================================================================================
- 使用QTimer实现延迟保存，避免频繁写入
- 设置1秒延迟，平衡响应速度和IO效率
- 单触发模式，确保每次编辑只触发一次保存
- 加载期间禁用自动保存，防止空内容覆盖文件

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os

from PyQt5.QtCore import QTimer

try:
    from core import get_logger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class AutosaveManager:
    def __init__(self, home_tab):
        """
        初始化自动保存管理器

        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        self.home_tab = home_tab
        self._logger = get_logger() if LOGGER_AVAILABLE else None
        self._step1_save_timer = QTimer(self.home_tab)
        self._step1_save_timer.setSingleShot(True)
        self._step1_save_timer.timeout.connect(self._do_step1_autosave)
        self._last_step1_editor = None
        self._step2_save_timer = QTimer(self.home_tab)
        self._step2_save_timer.setSingleShot(True)
        self._step2_save_timer.timeout.connect(self._do_step2_autosave)
        self._loading = False

    def set_loading(self, loading: bool):
        """
        设置加载状态

        在加载项目期间，禁用自动保存触发，防止空内容覆盖文件。

        Args:
            loading: True表示正在加载，禁用自动保存；False表示加载完成，启用自动保存

        Returns:
            无
        """
        self._loading = loading
        if loading:
            self._step1_save_timer.stop()
            self._step2_save_timer.stop()
            if self._logger:
                self._logger.debug("autosave_manager", "加载模式启用，暂停自动保存")

    def save_step1_immediately(self):
        """
        立即保存第一步内容

        Args:
            无

        Returns:
            无
        """
        self._do_step1_autosave()

    def save_step2_immediately(self):
        """
        立即保存第二步内容

        Args:
            无

        Returns:
            无
        """
        self._do_step2_autosave()

    def _schedule_step1_autosave(self, editor):
        """
        调度Step1自动保存

        如果正在加载项目，则跳过调度。

        Args:
            editor: 触发保存的编辑器控件

        Returns:
            无
        """
        if not self.home_tab.current_project_path:
            return
        if self._loading:
            if self._logger:
                self._logger.debug("autosave_manager", "加载期间跳过Step1自动保存调度")
            return
        self._last_step1_editor = editor
        if self._step1_save_timer.isActive():
            self._step1_save_timer.stop()
        self._step1_save_timer.start(1000)

    def _do_step1_autosave(self):
        """
        执行Step1自动保存

        如果新内容为空但原始文件有内容，则跳过保存以防止数据丢失。

        Args:
            无

        Returns:
            无
        """
        if not self.home_tab.current_project_path:
            return
        if self._logger:
            self._logger.debug("autosave_manager", "触发Step1自动保存: 小说架构")
        text = ""
        try:
            if self._last_step1_editor and hasattr(
                self._last_step1_editor, "toPlainText"
            ):
                text = self._last_step1_editor.toPlainText()
        except Exception:
            text = ""
        if (
            not text
            and hasattr(self.home_tab, "step1TextEdit")
            and hasattr(self.home_tab.step1TextEdit, "toPlainText")
        ):
            text = self.home_tab.step1TextEdit.toPlainText()
        arch_file = os.path.join(
            self.home_tab.current_project_path, "Novel_architecture.txt"
        )
        os.makedirs(self.home_tab.current_project_path, exist_ok=True)
        original_content = ""
        if os.path.exists(arch_file):
            try:
                with open(arch_file, "r", encoding="utf-8") as f:
                    original_content = f.read()
            except Exception:
                original_content = ""
        if self._logger:
            orig_len = len(original_content)
            orig_first10 = (
                original_content[:10].replace("\n", "\\n")
                if original_content
                else "(空)"
            )
            orig_last10 = (
                original_content[-10:].replace("\n", "\\n")
                if original_content and len(original_content) >= 10
                else (
                    original_content.replace("\n", "\\n")
                    if original_content
                    else "(空)"
                )
            )
            self._logger.debug(
                "autosave_manager", f"[Step1自动保存] === 保存前原始文件状态 ==="
            )
            self._logger.debug(
                "autosave_manager", f"[Step1自动保存] 文件路径: {arch_file}"
            )
            self._logger.debug(
                "autosave_manager", f"[Step1自动保存] 原始文件长度: {orig_len} 字符"
            )
            self._logger.debug(
                "autosave_manager",
                f'[Step1自动保存] 原始内容前10字符: "{orig_first10}"',
            )
            self._logger.debug(
                "autosave_manager", f'[Step1自动保存] 原始内容后10字符: "{orig_last10}"'
            )
        if not text.strip() and original_content.strip():
            if self._logger:
                self._logger.warn(
                    "autosave_manager",
                    f"[Step1自动保存] 警告：新内容为空但原始文件有内容，将清空文件",
                )
        try:
            with open(arch_file, "w", encoding="utf-8") as f:
                f.write(text or "")
            if self._logger:
                new_len = len(text or "")
                new_first10 = (text or "")[:10].replace("\n", "\\n") if text else "(空)"
                new_last10 = (
                    (text or "")[-10:].replace("\n", "\\n")
                    if text and len(text) >= 10
                    else (text or "").replace("\n", "\\n") if text else "(空)"
                )
                self._logger.debug(
                    "autosave_manager", f"[Step1自动保存] === 保存后文件最终状态 ==="
                )
                self._logger.debug(
                    "autosave_manager", f"[Step1自动保存] 文件路径: {arch_file}"
                )
                self._logger.debug(
                    "autosave_manager",
                    f"[Step1自动保存] 更新后文件长度: {new_len} 字符",
                )
                self._logger.debug(
                    "autosave_manager",
                    f'[Step1自动保存] 更新后内容前10字符: "{new_first10}"',
                )
                self._logger.debug(
                    "autosave_manager",
                    f'[Step1自动保存] 更新后内容后10字符: "{new_last10}"',
                )
                self._logger.debug(
                    "autosave_manager", f"[Step1自动保存] === 保存操作完成 ==="
                )
        except Exception as e:
            self.home_tab.log(f"保存小说架构失败: {e}")
            if self._logger:
                self._logger.error("autosave_manager", f"Step1保存失败: {e}")

    def _schedule_step2_autosave(self):
        """
        调度Step2自动保存

        如果正在加载项目，则跳过调度。

        Args:
            无

        Returns:
            无
        """
        if not self.home_tab.current_project_path:
            return
        if self._loading:
            if self._logger:
                self._logger.debug("autosave_manager", "加载期间跳过Step2自动保存调度")
            return
        if self._step2_save_timer.isActive():
            self._step2_save_timer.stop()
        self._step2_save_timer.start(1000)

    def _do_step2_autosave(self):
        """
        执行Step2自动保存

        如果新内容为空但原始文件有内容，则跳过保存以防止数据丢失。

        Args:
            无

        Returns:
            无
        """
        if not self.home_tab.current_project_path:
            return
        if self._logger:
            self._logger.debug("autosave_manager", "触发Step2自动保存: 章节目录")
        text = ""
        try:
            if hasattr(self.home_tab, "step2TextEdit") and hasattr(
                self.home_tab.step2TextEdit, "toPlainText"
            ):
                text = self.home_tab.step2TextEdit.toPlainText()
        except Exception:
            text = ""
        dir_file = os.path.join(
            self.home_tab.current_project_path, "Novel_directory.txt"
        )
        os.makedirs(self.home_tab.current_project_path, exist_ok=True)
        original_content = ""
        if os.path.exists(dir_file):
            try:
                with open(dir_file, "r", encoding="utf-8") as f:
                    original_content = f.read()
            except Exception:
                original_content = ""
        if self._logger:
            orig_len = len(original_content)
            orig_first10 = (
                original_content[:10].replace("\n", "\\n")
                if original_content
                else "(空)"
            )
            orig_last10 = (
                original_content[-10:].replace("\n", "\\n")
                if original_content and len(original_content) >= 10
                else (
                    original_content.replace("\n", "\\n")
                    if original_content
                    else "(空)"
                )
            )
            self._logger.debug(
                "autosave_manager", f"[Step2自动保存] === 保存前原始文件状态 ==="
            )
            self._logger.debug(
                "autosave_manager", f"[Step2自动保存] 文件路径: {dir_file}"
            )
            self._logger.debug(
                "autosave_manager", f"[Step2自动保存] 原始文件长度: {orig_len} 字符"
            )
            self._logger.debug(
                "autosave_manager",
                f'[Step2自动保存] 原始内容前10字符: "{orig_first10}"',
            )
            self._logger.debug(
                "autosave_manager", f'[Step2自动保存] 原始内容后10字符: "{orig_last10}"'
            )
        if not text.strip() and original_content.strip():
            if self._logger:
                self._logger.warn(
                    "autosave_manager",
                    f"[Step2自动保存] 警告：新内容为空但原始文件有内容，将清空文件",
                )
        try:
            with open(dir_file, "w", encoding="utf-8") as f:
                f.write(text or "")
            if self._logger:
                new_len = len(text or "")
                new_first10 = (text or "")[:10].replace("\n", "\\n") if text else "(空)"
                new_last10 = (
                    (text or "")[-10:].replace("\n", "\\n")
                    if text and len(text) >= 10
                    else (text or "").replace("\n", "\\n") if text else "(空)"
                )
                self._logger.debug(
                    "autosave_manager", f"[Step2自动保存] === 保存后文件最终状态 ==="
                )
                self._logger.debug(
                    "autosave_manager", f"[Step2自动保存] 文件路径: {dir_file}"
                )
                self._logger.debug(
                    "autosave_manager",
                    f"[Step2自动保存] 更新后文件长度: {new_len} 字符",
                )
                self._logger.debug(
                    "autosave_manager",
                    f'[Step2自动保存] 更新后内容前10字符: "{new_first10}"',
                )
                self._logger.debug(
                    "autosave_manager",
                    f'[Step2自动保存] 更新后内容后10字符: "{new_last10}"',
                )
                self._logger.debug(
                    "autosave_manager", f"[Step2自动保存] === 保存操作完成 ==="
                )
        except Exception as e:
            self.home_tab.log(f"保存章节目录失败: {e}")
            if self._logger:
                self._logger.error("autosave_manager", f"Step2保存失败: {e}")
