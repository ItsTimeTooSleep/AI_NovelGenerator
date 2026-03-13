# -*- coding: utf-8 -*-
"""
项目状态管理器模块

================================================================================
模块功能概述
================================================================================
负责项目状态检查、文件状态验证和UI状态更新。
使用 StateController 统一管理状态切换。

主要功能:
- 项目文件状态检查
- 架构/目录文件验证
- UI状态更新（通过 StateController）
- 跳过按钮可见性控制
- 部分架构加载

================================================================================
使用示例
================================================================================
    from ui_qt.home import ProjectStateManager

    state_manager = ProjectStateManager(home_tab)
    state_manager.initialize()
    state_manager.check_project_files()
    status = state_manager.get_project_status()

================================================================================
设计决策
================================================================================
- 使用 StateController 统一管理状态切换
- 本模块只负责业务逻辑（如加载文件内容）
- UI状态更新委托给 StateController

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json
import os
from typing import Any, Dict, Tuple

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

from core.config_manager import load_config
from core.utils import check_file_has_valid_content, read_file

from ..core import BaseManager, EventBus, EventType
from .states import ProjectState


class ProjectStateManager(BaseManager):
    """
    项目状态管理器

    负责管理项目的所有状态检查和UI更新，包括：
    - 项目文件状态检查
    - 架构/目录文件验证
    - UI状态更新
    - 跳过按钮控制
    """

    def __init__(self, home_tab: QWidget):
        """
        初始化项目状态管理器

        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        super().__init__(home_tab)
        self.loaded_config: Dict[str, Any] = {}

    def initialize(self) -> None:
        """
        初始化项目状态管理器

        加载配置，订阅事件。
        """
        self._load_config()
        self._subscribe_events()
        self._initialized = True

    def _load_config(self) -> None:
        """
        加载配置文件
        """
        config_file = "config.json"
        self.loaded_config = load_config(config_file) or {}

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
            event: 事件对象，包含 project_data
        """
        project_data = event.data.get("project_data", {})
        self.set_project(project_data)

    def set_project(self, project_data: Dict[str, Any]) -> None:
        """
        设置项目数据

        Args:
            project_data: 项目数据字典
        """
        if hasattr(self.parent, "autosave_manager"):
            self.parent.autosave_manager.set_loading(True)

        if hasattr(self.parent, "chapter_loader"):
            self.parent.chapter_loader._is_loading_chapter = True

        if hasattr(self.parent, "current_project"):
            self.parent.current_project = project_data
        if hasattr(self.parent, "current_project_path"):
            self.parent.current_project_path = project_data.get("path", "")
        if hasattr(self.parent, "_entered_full_layout"):
            self.parent._entered_full_layout = project_data.get(
                "entered_full_layout", False
            )
        if hasattr(self.parent, "_entered_step4_actions"):
            self.parent._entered_step4_actions = False

        if hasattr(self.parent, "project_status_manager"):
            self.parent.project_status_manager.set_project(project_data.get("path", ""))

        self._reset_all_ui_states()
        self._update_ui_for_project(project_data)

        QTimer.singleShot(100, self._finish_loading)

    def _finish_loading(self) -> None:
        """
        完成项目加载后的处理

        检查项目文件状态，并关闭自动保存的加载模式。
        """
        self.check_project_files()
        if hasattr(self.parent, "autosave_manager"):
            self.parent.autosave_manager.set_loading(False)
        if hasattr(self.parent, "chapter_loader"):
            self.parent.chapter_loader._is_loading_chapter = False

    def _reset_all_ui_states(self) -> None:
        """
        重置所有UI状态，确保切换项目时界面是干净的
        """
        parent = self.parent

        if hasattr(parent, "_reset_step1_progress_widgets"):
            parent._reset_step1_progress_widgets()

        if hasattr(parent, "_reset_step2_progress_widgets"):
            parent._reset_step2_progress_widgets()

        if hasattr(parent, "_reset_init_buttons"):
            parent._reset_init_buttons()

        if hasattr(parent, "step1TextEdit"):
            parent.step1TextEdit.clear()
            parent.step1TextEdit.hide()

        if hasattr(parent, "step1ReviewTextEdit"):
            parent.step1ReviewTextEdit.clear()

        if hasattr(parent, "step2TextEdit"):
            parent.step2TextEdit.clear()
            parent.step2TextEdit.hide()

        if hasattr(parent, "editor"):
            parent.editor.clear()

        if hasattr(parent, "logOutput"):
            parent.logOutput.clear()

        if hasattr(parent, "guidanceEdit"):
            parent.guidanceEdit.clear()

        if hasattr(parent, "charactersInvolvedEdit"):
            parent.charactersInvolvedEdit.clear()

        if hasattr(parent, "keyItemsEdit"):
            parent.keyItemsEdit.clear()

        if hasattr(parent, "sceneLocationEdit"):
            parent.sceneLocationEdit.clear()

        if hasattr(parent, "timeConstraintEdit"):
            parent.timeConstraintEdit.clear()

        if hasattr(parent, "currChapterSpin"):
            parent.currChapterSpin.setValue(1)

        if hasattr(parent, "initStack") and hasattr(parent, "frameNoProject"):
            parent.initStack.setCurrentWidget(parent.frameNoProject)

        if hasattr(parent, "actionsStack") and hasattr(parent, "frameActionsLocked"):
            parent.actionsStack.setCurrentWidget(parent.frameActionsLocked)

        if hasattr(parent, "layout_manager"):
            parent.layout_manager._apply_simplified_layout()

        if hasattr(parent, "rightStack"):
            parent.rightStack.setCurrentIndex(0)

    def _update_ui_for_project(self, project_data: Dict[str, Any]) -> None:
        """
        更新项目相关的UI

        Args:
            project_data: 项目数据字典
        """
        if hasattr(self.parent, "bookTitleLabel"):
            self.parent.bookTitleLabel.setText(project_data.get("name", "未命名"))

        if hasattr(self.parent, "currChapterSpin"):
            self.parent.currChapterSpin.setValue(
                int(project_data.get("current_chapter", 1))
            )

        if hasattr(self.parent, "guidanceEdit"):
            self.parent.guidanceEdit.setText(project_data.get("user_guidance", ""))

        if hasattr(self.parent, "charactersInvolvedEdit"):
            self.parent.charactersInvolvedEdit.setText(
                project_data.get("characters_involved", "")
            )

        if hasattr(self.parent, "keyItemsEdit"):
            self.parent.keyItemsEdit.setText(project_data.get("key_items", ""))

        if hasattr(self.parent, "sceneLocationEdit"):
            self.parent.sceneLocationEdit.setText(
                project_data.get("scene_location", "")
            )

        if hasattr(self.parent, "timeConstraintEdit"):
            self.parent.timeConstraintEdit.setText(
                project_data.get("time_constraint", "")
            )

        if hasattr(self.parent, "log"):
            self.parent.log(f"已加载项目: {project_data.get('name')}")

    def check_project_files(self) -> None:
        """
        检查项目文件状态并更新UI显示

        这是核心方法，负责：
        - 检查架构和目录文件是否存在
        - 验证步骤完成状态
        - 通过 StateController 更新UI状态
        - 加载部分架构数据
        """
        self.update_skip_buttons_visibility()

        has_arch, has_dir, step1_completed, step2_completed = self._get_file_status()

        self._determine_and_apply_state(
            has_arch, has_dir, step1_completed, step2_completed
        )

        self._update_step_navigation(step1_completed, step2_completed)

        self._update_chapter_ui(step1_completed, step2_completed)

    def _determine_and_apply_state(
        self,
        has_arch: bool,
        has_dir: bool,
        step1_completed: bool,
        step2_completed: bool,
    ) -> None:
        """
        根据文件状态确定并应用目标状态

        Args:
            has_arch: 是否有架构文件
            has_dir: 是否有目录文件
            step1_completed: Step1是否完成
            step2_completed: Step2是否完成
        """
        project_path = getattr(self.parent, "current_project_path", "")
        entered_full_layout = getattr(self.parent, "_entered_full_layout", False)
        entered_step4 = getattr(self.parent, "_entered_step4_actions", False)

        if not project_path:
            target_state = ProjectState.NO_PROJECT
        elif not step1_completed:
            partial_arch_path = os.path.join(project_path, "partial_architecture.json")
            if os.path.exists(partial_arch_path):
                target_state = ProjectState.STEP1_IN_PROGRESS
                self._load_partial_architecture(partial_arch_path, has_arch)
            else:
                target_state = ProjectState.STEP1_NOT_STARTED
        elif not step2_completed:
            target_state = ProjectState.STEP2_NOT_STARTED
            self._load_directory_content(has_dir)
        elif not entered_full_layout:
            target_state = ProjectState.PROJECT_READY
        else:
            if entered_step4:
                target_state = ProjectState.STEP4_ACTIVE
            else:
                target_state = ProjectState.STEP3_ACTIVE

        self.parent.state_controller.transition_to(target_state, silent=True)

    def _load_directory_content(self, has_dir: bool) -> None:
        """
        加载目录内容到编辑器

        Args:
            has_dir: 是否有目录文件
        """
        if not has_dir or not hasattr(self.parent, "step2TextEdit"):
            return

        if self.parent.step2TextEdit.toPlainText().strip():
            return

        project_path = getattr(self.parent, "current_project_path", "")
        if not project_path:
            return

        dir_path = os.path.join(project_path, "Novel_directory.txt")
        try:
            text = read_file(dir_path)
            self.parent.step2TextEdit.setPlainText(text)
            self.parent.step2TextEdit.show()
        except Exception:
            pass

    def _get_file_status(self) -> Tuple[bool, bool, bool, bool]:
        """
        获取文件状态

        Returns:
            Tuple[bool, bool, bool, bool]: (has_arch, has_dir, step1_completed, step2_completed)
        """
        has_arch = False
        has_dir = False
        step1_completed = False
        step2_completed = False

        project_status_manager = getattr(self.parent, "project_status_manager", None)
        if project_status_manager:
            step1_completed = project_status_manager.is_step1_completed()
            step2_completed = project_status_manager.is_step2_completed()

        project_path = getattr(self.parent, "current_project_path", "")
        if project_path:
            arch_path = os.path.join(project_path, "Novel_architecture.txt")
            dir_path = os.path.join(project_path, "Novel_directory.txt")

            has_arch = self._check_file_with_content(arch_path)
            has_dir = self._check_file_with_content(dir_path)

        return has_arch, has_dir, step1_completed, step2_completed

    def _check_file_with_content(self, file_path: str) -> bool:
        """
        检查文件是否存在且有有效内容（排除提示文本）

        Args:
            file_path: 文件路径

        Returns:
            bool: True表示文件存在且有有效内容
        """
        return check_file_has_valid_content(file_path)

    def _load_partial_architecture(
        self, partial_arch_path: str, has_arch: bool
    ) -> None:
        """
        加载部分架构数据

        Args:
            partial_arch_path: 部分架构文件路径
            has_arch: 是否有完整架构文件
        """
        try:
            with open(partial_arch_path, "r", encoding="utf-8") as f:
                partial_data = json.load(f)

            step_index_map = {
                "generated_title": 0,
                "core_seed_result": 1,
                "character_dynamics_result": 2,
                "character_state_result": 3,
                "world_building_result": 4,
                "plot_arch_result": 5,
            }

            if hasattr(self.parent, "step1ProgressContainer"):
                self.parent.step1ProgressContainer.show()

            step_name_map = {
                "generated_title": "书名生成",
                "core_seed_result": "核心种子生成",
                "character_dynamics_result": "角色动力学构建",
                "character_state_result": "初始角色状态生成",
                "world_building_result": "世界观搭建",
                "plot_arch_result": "情节架构设计",
            }

            project_status_manager = getattr(
                self.parent, "project_status_manager", None
            )
            step1_times = {}
            if project_status_manager:
                step1_times = project_status_manager.get_step1_steps_time()

            completed_indices = []
            for key, idx in step_index_map.items():
                if key in partial_data and hasattr(self.parent, "step1ProgressWidgets"):
                    if idx < len(self.parent.step1ProgressWidgets):
                        step_widget = self.parent.step1ProgressWidgets[idx]
                        if not step_widget.is_completed:
                            step_widget.set_completed(True)
                        step_widget.set_visible(True)
                        if key in partial_data:
                            step_widget.set_ai_output(partial_data[key])
                        step_name = step_name_map.get(key, "")
                        if step_name in step1_times:
                            step_widget.elapsed_time = step1_times[step_name]
                            step_widget.timer_label.setText(
                                f"{step_widget.elapsed_time:.1f}s"
                            )
                            step_widget.timer_label.show()
                        completed_indices.append(idx)

            if hasattr(self.parent, "step1ProgressContainer"):
                self.parent.step1ProgressContainer.update_line_state(
                    -1, completed_indices
                )

            self._load_architecture_to_editor(has_arch)

        except Exception as e:
            if hasattr(self.parent, "log"):
                self.parent.log(f"加载部分架构失败: {e}")

    def _load_architecture_to_editor(self, has_arch: bool) -> None:
        """
        加载架构到编辑器

        Args:
            has_arch: 是否有架构文件
        """
        if not has_arch or not hasattr(self.parent, "step1TextEdit"):
            return

        if self.parent.step1TextEdit.toPlainText().strip():
            return

        project_path = getattr(self.parent, "current_project_path", "")
        if not project_path:
            return

        arch_path = os.path.join(project_path, "Novel_architecture.txt")
        try:
            text = read_file(arch_path)
            self.parent.step1TextEdit.setPlainText(text)
            self.parent.step1TextEdit.show()
        except Exception:
            pass

    def _update_step_navigation(
        self, step1_completed: bool, step2_completed: bool
    ) -> None:
        """
        更新步骤导航

        Args:
            step1_completed: Step1是否完成
            step2_completed: Step2是否完成
        """
        can_switch = bool(
            getattr(self.parent, "current_project_path", "") and step1_completed
        )

        if hasattr(self.parent, "step1ToStep2Arrow"):
            self.parent.step1ToStep2Arrow.setVisible(can_switch)
        if hasattr(self.parent, "step2ToStep1Arrow"):
            self.parent.step2ToStep1Arrow.setVisible(can_switch)

    def _update_chapter_ui(self, step1_completed: bool, step2_completed: bool) -> None:
        """
        更新章节UI

        Args:
            step1_completed: Step1是否完成
            step2_completed: Step2是否完成
        """
        project_path = getattr(self.parent, "current_project_path", "")
        if not (project_path and step1_completed and step2_completed):
            return

        if not hasattr(self.parent, "step3Title"):
            return

        if not hasattr(self.parent, "currChapterSpin"):
            return

        chap_num = self.parent.currChapterSpin.value()
        self.parent.step3Title.setText(f"第{chap_num}章·生成草稿")

        chap_file = os.path.join(project_path, "chapters", f"chapter_{chap_num}.txt")
        chapter_has_content = self._check_file_with_content(chap_file)

        project_status_manager = getattr(self.parent, "project_status_manager", None)
        is_finalized = False
        if project_status_manager:
            is_finalized = project_status_manager.is_finalized(chap_num)

        if chapter_has_content:
            if hasattr(self.parent, "step3Btn"):
                self.parent.step3Btn.setText("Step 3. 重新生成草稿")
            if hasattr(self.parent, "continueToStep4Btn"):
                entered_full = getattr(self.parent, "_entered_full_layout", False)
                entered_step4 = getattr(self.parent, "_entered_step4_actions", False)
                if entered_full and not entered_step4 and not is_finalized:
                    self.parent.continueToStep4Btn.show()
                else:
                    self.parent.continueToStep4Btn.hide()
            if hasattr(self.parent, "chapter_loader"):
                self.parent.chapter_loader.load_chapter(chap_num)
        else:
            if hasattr(self.parent, "step3Btn"):
                self.parent.step3Btn.setText("Step 3. 生成草稿")
            if hasattr(self.parent, "editor"):
                self.parent.editor.clear()
            if hasattr(self.parent, "continueToStep4Btn"):
                self.parent.continueToStep4Btn.hide()
            if hasattr(self.parent, "chapter_loader"):
                self.parent.chapter_loader._set_editor_text(
                    f"第{chap_num}章还未生成，请先生成草稿"
                )

    def update_skip_buttons_visibility(self) -> None:
        """
        根据开发者模式更新跳过按钮的可见性

        注意：每次调用时重新加载配置，确保获取最新的开发者模式设置
        """
        self._load_config()
        developer_mode = self.loaded_config.get("developer_mode", False)

        if hasattr(self.parent, "skipStep1Btn"):
            if developer_mode:
                self.parent.skipStep1Btn.show()
            else:
                self.parent.skipStep1Btn.hide()

        if hasattr(self.parent, "skipStep2Btn"):
            if developer_mode:
                self.parent.skipStep2Btn.show()
            else:
                self.parent.skipStep2Btn.hide()

    def _on_skip_step1(self) -> None:
        """
        处理跳过 Step 1 的逻辑

        创建一个空的架构文件并标记 Step 1 为已完成，然后自动切换到 Step 2
        """
        from PyQt5.QtWidgets import QMessageBox

        project_path = getattr(self.parent, "current_project_path", "")
        if not project_path:
            return

        reply = QMessageBox.question(
            self.parent,
            "确认跳过",
            "确定要跳过 Step 1 吗？\n\n这将创建一个空的架构文件并标记为已完成。\n你可以稍后手动编辑架构内容。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        arch_path = os.path.join(project_path, "Novel_architecture.txt")
        try:
            with open(arch_path, "w", encoding="utf-8") as f:
                f.write(
                    "# 小说架构\n\n（此架构文件通过开发者模式跳过创建，请手动编辑）\n"
                )

            if hasattr(self.parent, "project_status_manager"):
                self.parent.project_status_manager.mark_step1_completed()

            if hasattr(self.parent, "log"):
                self.parent.log("已跳过 Step 1，创建了空架构文件")

            self.check_project_files()

            if hasattr(self.parent, "step_manager"):
                self.parent.step_manager.go_to_step2_from_step1()

        except Exception as e:
            if hasattr(self.parent, "log"):
                self.parent.log(f"跳过 Step 1 失败: {e}")

    def _on_skip_step2(self) -> None:
        """
        处理跳过 Step 2 的逻辑

        创建一个空的目录文件并标记 Step 2 为已完成，然后自动切换到项目已就绪界面
        """
        from PyQt5.QtWidgets import QMessageBox

        project_path = getattr(self.parent, "current_project_path", "")
        if not project_path:
            return

        has_arch, _, _, _ = self._get_file_status()
        if not has_arch:
            QMessageBox.warning(
                self.parent,
                "无法跳过",
                "请先完成或跳过 Step 1（小说架构）后再跳过 Step 2。",
            )
            return

        reply = QMessageBox.question(
            self.parent,
            "确认跳过",
            "确定要跳过 Step 2 吗？\n\n这将创建一个空的目录文件并标记为已完成。\n你可以稍后手动编辑目录内容。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        dir_path = os.path.join(project_path, "Novel_directory.txt")
        try:
            with open(dir_path, "w", encoding="utf-8") as f:
                f.write(
                    "# 章节目录\n\n（此目录文件通过开发者模式跳过创建，请手动编辑）\n"
                )

            if hasattr(self.parent, "project_status_manager"):
                self.parent.project_status_manager.mark_step2_completed()

            if hasattr(self.parent, "log"):
                self.parent.log("已跳过 Step 2，创建了空目录文件")

            self.check_project_files()

            if hasattr(self.parent, "initStack") and hasattr(
                self.parent, "frameInitDone"
            ):
                self.parent.initStack.setCurrentWidget(self.parent.frameInitDone)

        except Exception as e:
            if hasattr(self.parent, "log"):
                self.parent.log(f"跳过 Step 2 失败: {e}")

    def get_project_status(self) -> Dict[str, Any]:
        """
        获取项目状态

        Returns:
            Dict[str, Any]: 项目状态字典
        """
        has_arch, has_dir, step1_completed, step2_completed = self._get_file_status()
        return {
            "has_architecture": has_arch,
            "has_directory": has_dir,
            "step1_completed": step1_completed,
            "step2_completed": step2_completed,
            "project_path": getattr(self.parent, "current_project_path", ""),
        }

    def has_architecture(self) -> bool:
        """
        检查是否有架构文件

        Returns:
            bool: True表示有架构文件
        """
        has_arch, _, _, _ = self._get_file_status()
        return has_arch

    def has_directory(self) -> bool:
        """
        检查是否有目录文件

        Returns:
            bool: True表示有目录文件
        """
        _, has_dir, _, _ = self._get_file_status()
        return has_dir

    def cleanup(self) -> None:
        """
        清理资源

        取消事件订阅。
        """
        event_bus = EventBus.get_instance()
        event_bus.unsubscribe(EventType.PROJECT_LOADED, self._on_project_loaded)
