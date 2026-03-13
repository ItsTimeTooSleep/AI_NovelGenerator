# -*- coding: utf-8 -*-
"""
状态定义模块

================================================================================
模块功能概述
================================================================================
本模块定义了生成台功能模块的所有状态枚举，包括：
- 项目状态枚举 (ProjectState)
- 初始化堆栈页面枚举 (InitStackPage)
- 操作堆栈页面枚举 (ActionsStackPage)

================================================================================
状态流转
================================================================================
初始化阶段:
    NO_PROJECT → STEP1_NOT_STARTED → STEP1_IN_PROGRESS → STEP1_COMPLETED
    → STEP2_NOT_STARTED → STEP2_IN_PROGRESS → PROJECT_READY

完整控件阶段:
    PROJECT_READY → STEP3_ACTIVE ↔ STEP4_ACTIVE

查看模式:
    STEP1_COMPLETED → STEP1_REVIEW → STEP2_NOT_STARTED

================================================================================
设计决策
================================================================================
- 使用枚举确保状态类型安全
- 状态名称清晰表达业务含义
- 分离页面枚举与状态枚举，便于独立扩展

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from enum import Enum, auto


class ProjectState(Enum):
    """
    项目状态枚举
    
    定义项目在整个生命周期中的所有可能状态。
    每个状态对应特定的UI配置和用户操作权限。
    
    Attributes:
        NO_PROJECT: 无项目状态，显示项目选择提示
        STEP1_NOT_STARTED: Step 1 未开始，显示开始按钮
        STEP1_IN_PROGRESS: Step 1 进行中，显示进度和停止按钮
        STEP1_COMPLETED: Step 1 已完成，显示继续按钮
        STEP1_REVIEW: Step 1 查看模式，从Step2返回查看架构
        STEP2_NOT_STARTED: Step 2 未开始，显示开始按钮
        STEP2_IN_PROGRESS: Step 2 进行中，显示进度和停止按钮
        PROJECT_READY: 项目已就绪，可进入完整控件模式
        STEP3_ACTIVE: Step 3 活动中，草稿生成界面
        STEP4_ACTIVE: Step 4 活动中，定稿界面
    """
    
    NO_PROJECT = auto()
    
    STEP1_NOT_STARTED = auto()
    STEP1_IN_PROGRESS = auto()
    STEP1_COMPLETED = auto()
    STEP1_REVIEW = auto()
    
    STEP2_NOT_STARTED = auto()
    STEP2_IN_PROGRESS = auto()
    
    PROJECT_READY = auto()
    
    STEP3_ACTIVE = auto()
    STEP4_ACTIVE = auto()


class InitStackPage(Enum):
    """
    初始化堆栈页面枚举
    
    定义 initStack 容器中的所有可用页面。
    用于状态切换时确定显示哪个页面。
    
    Attributes:
        NO_PROJECT: 无项目提示页面
        STEP1: Step 1 主界面（生成架构）
        STEP1_REVIEW: Step 1 查看界面（从Step2返回查看）
        STEP2: Step 2 界面（生成目录）
        READY: 项目已就绪界面
    """
    
    NO_PROJECT = "frameNoProject"
    STEP1 = "frameStep1"
    STEP1_REVIEW = "frameStep1Review"
    STEP2 = "frameStep2"
    READY = "frameInitDone"


class ActionsStackPage(Enum):
    """
    操作堆栈页面枚举
    
    定义 actionsStack 容器中的所有可用页面。
    用于状态切换时确定显示哪个操作界面。
    
    Attributes:
        LOCKED: 锁定状态，显示"请先完成初始化"提示
        STEP3: Step 3 操作界面（生成草稿）
        STEP4: Step 4 操作界面（定稿章节）
    """
    
    LOCKED = "frameActionsLocked"
    STEP3 = "frameStep3Actions"
    STEP4 = "frameStep4Actions"


class LayoutMode(Enum):
    """
    布局模式枚举
    
    定义界面的两种布局模式。
    
    Attributes:
        SIMPLIFIED: 简化布局，用于Step1/Step2阶段
        FULL: 完整布局，用于Step3/Step4阶段
    """
    
    SIMPLIFIED = "simplified"
    FULL = "full"
