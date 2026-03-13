# -*- coding: utf-8 -*-
"""
首页模块包

================================================================================
模块功能概述
================================================================================
本包实现了AI小说生成器首页（生成台）的完整功能，采用模块化设计将功能拆分到多个子模块。
首页是用户进行小说创作的主要工作区域，包含四步生成流程和Composer AI辅助功能。

================================================================================
模块结构
================================================================================
- states: 状态定义枚举
- state_controller: 状态控制器
- step1_widget: Step1界面组件（小说架构生成）
- step2_widget: Step2界面组件（章节蓝图生成）
- step3_widget: Step3界面组件（章节草稿生成）
- step4_widget: Step4界面组件（章节定稿处理）
- step_manager: 步骤切换管理器
- layout_manager: 布局管理器
- progress_manager: 进度管理器
- streaming_manager: 流式输出管理器
- autosave_manager: 自动保存管理器
- generation_flow: 生成流程管理器
- composer_features: Composer AI功能
- common_components: 通用UI组件
- ui_builder: UI构建器

================================================================================
四步生成流程
================================================================================
Step 1: 小说架构生成
    - 核心种子、角色动力学、世界观、情节架构
Step 2: 章节蓝图生成
    - 生成所有章节的定位、作用、悬念等元信息
Step 3: 章节草稿生成
    - 基于蓝图生成章节正文内容
Step 4: 章节定稿处理
    - 更新摘要、角色状态，向量入库

================================================================================
状态管理
================================================================================
使用 StateController 统一管理状态切换：
- ProjectState: 项目状态枚举
- InitStackPage: 初始化堆栈页面
- ActionsStackPage: 操作堆栈页面
- LayoutMode: 布局模式

================================================================================
设计决策
================================================================================
- 采用模块化设计，每个功能独立封装
- 使用 StateController 统一管理状态切换
- 支持断点续传，中断后可从上次位置继续
- 自动保存机制，防止数据丢失
- 流式输出支持，实时显示生成进度

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from .auto_generate_manager import AutoGenerateManager
from .autosave_manager import AutosaveManager
from .chapter_loader import ChapterLoader
from .common_components import CommonComponents
from .composer_features import ComposerFeatures
from .generation_flow import GenerationFlowManager
from .layout_manager import LayoutManager
from .log_panel_manager import LogPanelManager
from .progress_manager import ProgressManager
from .project_state_manager import ProjectStateManager
from .project_status_data import ChapterStatus, ProjectStatusManager
from .state_controller import StateController
from .states import ActionsStackPage, InitStackPage, LayoutMode, ProjectState
from .step1_widget import Step1Widget
from .step2_widget import Step2Widget
from .step3_widget import Step3Widget
from .step4_widget import Step4Widget
from .step_manager import StepManager
from .streaming_manager import StreamingManager
from .ui_builder import UIBuilder

__all__ = [
    "LayoutManager",
    "StepManager",
    "AutosaveManager",
    "ProgressManager",
    "StreamingManager",
    "UIBuilder",
    "GenerationFlowManager",
    "CommonComponents",
    "Step1Widget",
    "Step2Widget",
    "Step3Widget",
    "Step4Widget",
    "ComposerFeatures",
    "LogPanelManager",
    "ChapterLoader",
    "ProjectStateManager",
    "AutoGenerateManager",
    "ProjectStatusManager",
    "ChapterStatus",
    "StateController",
    "ProjectState",
    "InitStackPage",
    "ActionsStackPage",
    "LayoutMode",
]
