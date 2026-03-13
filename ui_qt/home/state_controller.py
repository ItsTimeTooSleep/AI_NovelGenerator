# -*- coding: utf-8 -*-
"""
状态控制器模块

================================================================================
模块功能概述
================================================================================
本模块负责统一管理项目状态转换和UI更新，包括：
- 状态定义与配置
- 状态转换逻辑
- UI组件自动更新
- 状态变化通知

================================================================================
核心类
================================================================================
- UIComponentConfig: UI组件配置数据类
- StateConfig: 状态配置数据类
- StateController: 状态控制器

================================================================================
使用方式
================================================================================
    from ui_qt.home import StateController, ProjectState

    # 初始化
    state_controller = StateController(home_tab)
    
    # 切换状态
    state_controller.transition_to(ProjectState.STEP1_COMPLETED)
    
    # 添加监听器
    state_controller.add_state_change_listener(on_state_changed)

================================================================================
设计决策
================================================================================
- 配置驱动：所有UI配置通过数据类定义，便于维护
- 单一职责：状态控制器只负责状态转换和UI更新
- 观察者模式：支持状态变化监听，解耦业务逻辑

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .states import ActionsStackPage, InitStackPage, LayoutMode, ProjectState


@dataclass
class UIComponentConfig:
    """
    UI组件配置数据类
    
    定义在特定状态下，各个UI组件应该如何显示。
    
    Attributes:
        visible: 是否可见
        enabled: 是否启用
        text: 按钮文本（可选）
        show_progress: 是否显示进度（用于进度容器）
    """
    
    visible: bool = True
    enabled: bool = True
    text: Optional[str] = None
    show_progress: bool = False


@dataclass
class StateConfig:
    """
    状态配置数据类
    
    定义一个状态对应的所有UI配置，包括：
    - 显示名称
    - 堆栈页面
    - 布局模式
    - 组件配置
    - 日志面板配置
    
    Attributes:
        name: 状态内部名称
        display_name: 状态显示名称（用于日志）
        init_stack_page: initStack 页面
        actions_stack_page: actionsStack 页面
        layout_mode: 布局模式
        components: 组件配置字典
        log_panel_visible: 日志面板是否可见
        log_toggle_visible: 日志切换按钮是否可见
    """
    
    name: str
    display_name: str
    init_stack_page: InitStackPage
    actions_stack_page: ActionsStackPage
    layout_mode: LayoutMode
    components: Dict[str, UIComponentConfig] = field(default_factory=dict)
    log_panel_visible: bool = True
    log_toggle_visible: bool = True


class StateController:
    """
    状态控制器
    
    统一管理项目状态转换和UI更新。
    
    核心功能:
    - 管理当前状态
    - 执行状态转换
    - 自动更新UI组件
    - 通知状态变化监听器
    
    使用示例:
        controller = StateController(home_tab)
        controller.transition_to(ProjectState.STEP1_COMPLETED)
    """
    
    _STATE_CONFIGS: Dict[ProjectState, StateConfig] = {
        ProjectState.NO_PROJECT: StateConfig(
            name="no_project",
            display_name="无项目",
            init_stack_page=InitStackPage.NO_PROJECT,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step1Btn": UIComponentConfig(visible=False),
                "step2Btn": UIComponentConfig(visible=False),
                "continueToStep2Btn": UIComponentConfig(visible=False),
                "continueToReadyBtn": UIComponentConfig(visible=False),
                "continueToStep3Btn": UIComponentConfig(visible=False),
            },
        ),
        
        ProjectState.STEP1_NOT_STARTED: StateConfig(
            name="step1_not_started",
            display_name="Step 1 未开始",
            init_stack_page=InitStackPage.STEP1,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step1Btn": UIComponentConfig(visible=True, enabled=True, text="开始 Step 1"),
                "step1ProgressContainer": UIComponentConfig(visible=False),
                "stopStep1Btn": UIComponentConfig(visible=False),
                "continueToStep2Btn": UIComponentConfig(visible=False),
                "step1TextEdit": UIComponentConfig(visible=False),
                "step1ToStep2Arrow": UIComponentConfig(visible=False),
                "skipStep1Btn": UIComponentConfig(visible=True),
            },
        ),
        
        ProjectState.STEP1_IN_PROGRESS: StateConfig(
            name="step1_in_progress",
            display_name="Step 1 进行中",
            init_stack_page=InitStackPage.STEP1,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step1Btn": UIComponentConfig(visible=False),
                "step1ProgressContainer": UIComponentConfig(visible=True),
                "stopStep1Btn": UIComponentConfig(visible=True),
                "continueToStep2Btn": UIComponentConfig(visible=False),
                "step1ToStep2Arrow": UIComponentConfig(visible=False),
                "skipStep1Btn": UIComponentConfig(visible=False),
            },
        ),
        
        ProjectState.STEP1_COMPLETED: StateConfig(
            name="step1_completed",
            display_name="Step 1 已完成",
            init_stack_page=InitStackPage.STEP1,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step1Btn": UIComponentConfig(visible=False),
                "step1ProgressContainer": UIComponentConfig(visible=False),
                "stopStep1Btn": UIComponentConfig(visible=False),
                "continueToStep2Btn": UIComponentConfig(visible=True),
                "step1TextEdit": UIComponentConfig(visible=True),
                "step1ToStep2Arrow": UIComponentConfig(visible=True),
                "skipStep1Btn": UIComponentConfig(visible=False),
            },
        ),
        
        ProjectState.STEP1_REVIEW: StateConfig(
            name="step1_review",
            display_name="Step 1 查看",
            init_stack_page=InitStackPage.STEP1_REVIEW,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step1ReviewToStep2Arrow": UIComponentConfig(visible=True),
            },
        ),
        
        ProjectState.STEP2_NOT_STARTED: StateConfig(
            name="step2_not_started",
            display_name="Step 2 未开始",
            init_stack_page=InitStackPage.STEP2,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step2Btn": UIComponentConfig(visible=True, enabled=True, text="开始 Step 2"),
                "step2ProgressContainer": UIComponentConfig(visible=False),
                "stopStep2Btn": UIComponentConfig(visible=False),
                "continueToReadyBtn": UIComponentConfig(visible=False),
                "step2TextEdit": UIComponentConfig(visible=False),
                "step2ToStep1Arrow": UIComponentConfig(visible=True),
                "skipStep2Btn": UIComponentConfig(visible=True),
                "step2HintLabel": UIComponentConfig(visible=True),
            },
        ),
        
        ProjectState.STEP2_IN_PROGRESS: StateConfig(
            name="step2_in_progress",
            display_name="Step 2 进行中",
            init_stack_page=InitStackPage.STEP2,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "step2Btn": UIComponentConfig(visible=False),
                "step2ProgressContainer": UIComponentConfig(visible=True),
                "stopStep2Btn": UIComponentConfig(visible=True),
                "continueToReadyBtn": UIComponentConfig(visible=False),
                "step2ToStep1Arrow": UIComponentConfig(visible=False),
                "skipStep2Btn": UIComponentConfig(visible=False),
                "step2HintLabel": UIComponentConfig(visible=False),
            },
        ),
        
        ProjectState.PROJECT_READY: StateConfig(
            name="project_ready",
            display_name="项目已就绪",
            init_stack_page=InitStackPage.READY,
            actions_stack_page=ActionsStackPage.LOCKED,
            layout_mode=LayoutMode.SIMPLIFIED,
            components={
                "continueToStep3Btn": UIComponentConfig(visible=True),
            },
        ),
        
        ProjectState.STEP3_ACTIVE: StateConfig(
            name="step3_active",
            display_name="Step 3 活动中",
            init_stack_page=InitStackPage.READY,
            actions_stack_page=ActionsStackPage.STEP3,
            layout_mode=LayoutMode.FULL,
            log_panel_visible=False,
            log_toggle_visible=False,
            components={
                "initCard": UIComponentConfig(visible=False),
                "step3Btn": UIComponentConfig(visible=True, enabled=True, text="Step 3. 重新生成草稿"),
                "continueToStep4Btn": UIComponentConfig(visible=True),
                "stopChapterStreamBtn": UIComponentConfig(visible=False),
                "regenerateBtn": UIComponentConfig(visible=True),
            },
        ),
        
        ProjectState.STEP4_ACTIVE: StateConfig(
            name="step4_active",
            display_name="Step 4 活动中",
            init_stack_page=InitStackPage.READY,
            actions_stack_page=ActionsStackPage.STEP4,
            layout_mode=LayoutMode.FULL,
            log_panel_visible=False,
            log_toggle_visible=False,
            components={
                "initCard": UIComponentConfig(visible=False),
                "step4Btn": UIComponentConfig(visible=True, enabled=True, text="Step 4. 定稿章节"),
                "regenerateBtn": UIComponentConfig(visible=False),
            },
        ),
    }
    
    def __init__(self, home_tab):
        """
        初始化状态控制器
        
        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        self.home_tab = home_tab
        self._current_state: ProjectState = ProjectState.NO_PROJECT
        self._state_change_listeners: List[Callable[[ProjectState, ProjectState], None]] = []
    
    @property
    def current_state(self) -> ProjectState:
        """
        获取当前状态
        
        Returns:
            ProjectState: 当前状态
        """
        return self._current_state
    
    def add_state_change_listener(
        self, listener: Callable[[ProjectState, ProjectState], None]
    ) -> None:
        """
        添加状态变化监听器
        
        Args:
            listener: 监听器函数，接收 (old_state, new_state) 参数
        """
        self._state_change_listeners.append(listener)
    
    def remove_state_change_listener(
        self, listener: Callable[[ProjectState, ProjectState], None]
    ) -> None:
        """
        移除状态变化监听器
        
        Args:
            listener: 要移除的监听器函数
        """
        if listener in self._state_change_listeners:
            self._state_change_listeners.remove(listener)
    
    def transition_to(self, new_state: ProjectState, **kwargs) -> bool:
        """
        切换到新状态
        
        执行状态转换，自动更新所有相关UI组件。
        
        Args:
            new_state: 目标状态
            **kwargs: 额外参数
                - chapter_num: 章节号，用于更新章节标题
                - silent: 是否静默切换（不记录日志）
        
        Returns:
            bool: 切换是否成功
        """
        if new_state == self._current_state:
            return True
        
        config = self._STATE_CONFIGS.get(new_state)
        if not config:
            return False
        
        old_state = self._current_state
        self._current_state = new_state
        
        self._apply_init_stack(config.init_stack_page)
        self._apply_actions_stack(config.actions_stack_page)
        self._apply_layout(config.layout_mode)
        self._apply_components(config.components)
        self._apply_log_panel(config.log_panel_visible, config.log_toggle_visible)
        
        if "chapter_num" in kwargs:
            self._update_chapter_title(kwargs["chapter_num"])
        
        silent = kwargs.get("silent", False)
        if not silent:
            self.home_tab.log(f"📍 状态切换: {config.display_name}")
        
        for listener in self._state_change_listeners:
            try:
                listener(old_state, new_state)
            except Exception:
                pass
        
        return True
    
    def _apply_init_stack(self, page: InitStackPage) -> None:
        """
        应用 initStack 页面
        
        Args:
            page: 目标页面
        """
        if not hasattr(self.home_tab, "initStack"):
            return
        widget = getattr(self.home_tab, page.value, None)
        if widget:
            self.home_tab.initStack.setCurrentWidget(widget)
    
    def _apply_actions_stack(self, page: ActionsStackPage) -> None:
        """
        应用 actionsStack 页面
        
        Args:
            page: 目标页面
        """
        if not hasattr(self.home_tab, "actionsStack"):
            return
        widget = getattr(self.home_tab, page.value, None)
        if widget:
            self.home_tab.actionsStack.setCurrentWidget(widget)
    
    def _apply_layout(self, mode: LayoutMode) -> None:
        """
        应用布局模式
        
        Args:
            mode: 布局模式
        """
        if not hasattr(self.home_tab, "layout_manager"):
            return
        if mode == LayoutMode.SIMPLIFIED:
            self.home_tab.layout_manager._apply_simplified_layout()
        elif mode == LayoutMode.FULL:
            self.home_tab.layout_manager._apply_full_layout()
    
    def _apply_components(self, components: Dict[str, UIComponentConfig]) -> None:
        """
        应用组件配置
        
        Args:
            components: 组件配置字典
        """
        for component_name, config in components.items():
            if not hasattr(self.home_tab, component_name):
                continue
            component = getattr(self.home_tab, component_name)
            
            component.setVisible(config.visible)
            component.setEnabled(config.enabled)
            
            if config.text and hasattr(component, "setText"):
                component.setText(config.text)
    
    def _apply_log_panel(self, visible: bool, toggle_visible: bool) -> None:
        """
        应用日志面板配置
        
        Args:
            visible: 日志面板是否可见
            toggle_visible: 切换按钮是否可见
        """
        if hasattr(self.home_tab, "log_panel_manager"):
            self.home_tab.log_panel_manager.set_visible_in_step3(toggle_visible)
    
    def _update_chapter_title(self, chapter_num: int) -> None:
        """
        更新章节标题
        
        Args:
            chapter_num: 章节号
        """
        if hasattr(self.home_tab, "step3Title"):
            self.home_tab.step3Title.setText(f"第{chapter_num}章·生成草稿")
    
    def get_state_config(self, state: ProjectState) -> Optional[StateConfig]:
        """
        获取状态配置
        
        Args:
            state: 状态枚举值
        
        Returns:
            Optional[StateConfig]: 状态配置，如果不存在则返回 None
        """
        return self._STATE_CONFIGS.get(state)
    
    def is_in_full_mode(self) -> bool:
        """
        检查是否处于完整控件模式
        
        Returns:
            bool: 是否处于完整控件模式
        """
        return self._current_state in (
            ProjectState.STEP3_ACTIVE,
            ProjectState.STEP4_ACTIVE,
        )
    
    def is_step4_active(self) -> bool:
        """
        检查是否处于 Step 4 活动状态
        
        Returns:
            bool: 是否处于 Step 4 活动状态
        """
        return self._current_state == ProjectState.STEP4_ACTIVE
