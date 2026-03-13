# -*- coding: utf-8 -*-
"""
步骤切换管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责管理首页四步生成流程之间的切换逻辑，控制界面状态转换，
确保用户能够流畅地在各个步骤之间导航。

================================================================================
核心类
================================================================================
- StepManager: 步骤管理器

================================================================================
核心功能
================================================================================
- enter_full_controls: 进入完整控件模式（Step3/Step4）
- enter_step3_actions: 进入Step3操作界面
- enter_step4_actions: 进入Step4操作界面
- go_to_step1/go_to_step2: 步骤跳转方法

================================================================================
步骤流转
================================================================================
初始化模式:
    Step1 → Step1Review → Step2 → 完整控件模式

完整控件模式:
    Step3Actions ↔ Step4Actions

================================================================================
设计决策
================================================================================
- 使用 StateController 统一管理状态切换
- 本模块只负责业务逻辑（如加载文件内容）
- UI状态更新委托给 StateController

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os

from core.utils import read_file

from ..utils.generation_handlers import save_project_params
from .states import ProjectState


class StepManager:
    """
    步骤管理器
    
    负责管理首页四步生成流程之间的切换逻辑。
    使用 StateController 进行状态切换，本模块只处理业务逻辑。
    """
    
    def __init__(self, home_tab):
        """
        初始化步骤管理器
        
        Args:
            home_tab: HomeTab 实例
        """
        self.home_tab = home_tab
    
    def enter_full_controls(self):
        """
        进入完整控件模式
        
        切换到完整布局，显示Step3/Step4操作界面。
        """
        if not self.home_tab.current_project_path:
            return
        
        self.home_tab._entered_full_layout = True
        self.home_tab.state_controller.transition_to(ProjectState.STEP3_ACTIVE)
        save_project_params(self.home_tab)
        self.home_tab.check_project_files()
    
    def enter_step3_actions(self):
        """
        进入Step 3操作界面
        """
        self.home_tab._entered_step4_actions = False
        self.home_tab.state_controller.transition_to(ProjectState.STEP3_ACTIVE)
        
        if hasattr(self.home_tab, "fullScrollArea"):
            self.home_tab.fullScrollArea.verticalScrollBar().setValue(0)
        
        self.home_tab.check_project_files()
    
    def enter_step4_actions(self):
        """
        进入Step 4操作界面
        """
        self.home_tab._entered_step4_actions = True
        self.home_tab.state_controller.transition_to(ProjectState.STEP4_ACTIVE)
        
        if hasattr(self.home_tab, "fullScrollArea"):
            self.home_tab.fullScrollArea.verticalScrollBar().setValue(0)
        
        self.home_tab.check_project_files()
    
    def show_init_steps(self):
        """
        显示初始化步骤界面，跳转到Step 1查看界面
        """
        if not hasattr(self.home_tab, "initStack"):
            return
        
        self.go_to_step1_from_step2()
    
    def go_to_step1(self):
        """
        跳转到Step 1界面，正确显示已完成状态
        """
        if not self.home_tab.current_project_path:
            return
        
        step1_completed = self._check_step1_completed()
        
        if step1_completed:
            self.home_tab.state_controller.transition_to(ProjectState.STEP1_COMPLETED)
            self._load_architecture_to_step1()
        else:
            self.home_tab.state_controller.transition_to(ProjectState.STEP1_NOT_STARTED)
    
    def go_to_step1_from_step2(self):
        """
        从Step 2跳转到Step 1查看界面
        """
        if not self.home_tab.current_project_path:
            return
        
        self.home_tab.state_controller.transition_to(ProjectState.STEP1_REVIEW)
        
        arch_file = os.path.join(
            self.home_tab.current_project_path, "Novel_architecture.txt"
        )
        if os.path.exists(arch_file):
            try:
                text = read_file(arch_file)
                if hasattr(self.home_tab, "step1ReviewTextEdit"):
                    self.home_tab.step1ReviewTextEdit.setPlainText(text)
            except Exception:
                pass
    
    def go_to_step2_from_step1(self):
        """
        从Step 1跳转到Step 2界面
        """
        if not self.home_tab.current_project_path:
            return
        
        self.home_tab.state_controller.transition_to(ProjectState.STEP2_NOT_STARTED)
        self._load_directory_to_step2()
    
    def go_to_ready_from_step2(self):
        """
        从Step 2跳转到项目已就绪界面
        """
        if not self.home_tab.current_project_path:
            return
        
        self.home_tab.state_controller.transition_to(ProjectState.PROJECT_READY)
    
    def go_to_step2_from_step1_review(self):
        """
        从Step 1查看界面跳转到Step 2
        """
        try:
            if hasattr(self.home_tab, "step1ReviewTextEdit"):
                text = self.home_tab.step1ReviewTextEdit.toPlainText()
                if text.strip() and hasattr(self.home_tab, "step1TextEdit"):
                    self.home_tab.step1TextEdit.setPlainText(text)
        except Exception:
            pass
        
        self.go_to_step2_from_step1()
    
    def _check_step1_completed(self) -> bool:
        """
        检查Step 1是否已完成
        
        Returns:
            bool: Step 1是否已完成
        """
        project_status_manager = getattr(self.home_tab, "project_status_manager", None)
        if project_status_manager:
            return project_status_manager.is_step1_completed()
        
        if self.home_tab.current_project and isinstance(
            self.home_tab.current_project, dict
        ):
            step_status = self.home_tab.current_project.get("step_status", {})
            return step_status.get("step1_completed", False)
        
        return False
    
    def _check_step2_completed(self) -> bool:
        """
        检查Step 2是否已完成
        
        Returns:
            bool: Step 2是否已完成
        """
        project_status_manager = getattr(self.home_tab, "project_status_manager", None)
        if project_status_manager:
            return project_status_manager.is_step2_completed()
        
        if self.home_tab.current_project and isinstance(
            self.home_tab.current_project, dict
        ):
            step_status = self.home_tab.current_project.get("step_status", {})
            return step_status.get("step2_completed", False)
        
        return False
    
    def _load_architecture_to_step1(self):
        """
        加载架构内容到Step 1编辑器
        """
        arch_file = os.path.join(
            self.home_tab.current_project_path, "Novel_architecture.txt"
        )
        if os.path.exists(arch_file):
            try:
                text = read_file(arch_file)
                if hasattr(self.home_tab, "step1TextEdit"):
                    self.home_tab.step1TextEdit.setPlainText(text)
            except Exception:
                pass
    
    def _load_directory_to_step2(self):
        """
        加载目录内容到Step 2编辑器
        """
        dir_file = os.path.join(
            self.home_tab.current_project_path, "Novel_directory.txt"
        )
        if os.path.exists(dir_file) and hasattr(self.home_tab, "step2TextEdit"):
            if not self.home_tab.step2TextEdit.toPlainText().strip():
                try:
                    text = read_file(dir_file)
                    self.home_tab.step2TextEdit.setPlainText(text)
                except Exception:
                    pass
