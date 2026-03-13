# -*- coding: utf-8 -*-
"""
Qt前端模块包

================================================================================
模块功能概述
================================================================================
本包是AI小说生成器的图形用户界面层，基于PyQt5和qfluentwidgets构建。
提供现代化的Fluent Design风格界面，支持Windows Mica/Acrylic特效。

================================================================================
架构设计
================================================================================
采用分层架构设计：
- main_window.py: 主窗口/微内核，负责装配各个功能标签页
- tabs/: 功能标签页模块（图书馆、生成台、项目设定、写作编辑、设置）
- widgets/: 可复用UI组件（Composer、搜索替换、上下文菜单等）
- utils/: UI工具函数（样式、动画、辅助函数等）
- settings/: 设置界面及相关组件
- home/: 首页生成流程相关组件

================================================================================
核心导出
================================================================================
- MainWindow: 主窗口类
- SearchReplaceWidget: 搜索替换组件
- SelectionContextMenu: 文本选择上下文菜单
- ComposerInputWidget: Composer AI输入组件
- ComposerDiffWidget: Composer AI差异对比组件
- ComposerAIWorker: Composer AI后台工作线程

================================================================================
设计决策
================================================================================
- 使用qfluentwidgets实现Fluent Design风格
- 支持亮色/暗色主题切换
- Composer AI业务逻辑与UI分离
- 组件化设计，便于复用和维护

================================================================================
依赖要求
================================================================================
- PyQt5: Qt框架Python绑定
- qfluentwidgets: Fluent Design风格控件库

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from .main_window import MainWindow
from .widgets.composer_widget import (
    ComposerAIWorker,
    ComposerDiffWidget,
    ComposerInputWidget,
)
from .widgets.context_menu_widget import SelectionContextMenu
from .widgets.search_replace_widget import SearchReplaceWidget

__all__ = [
    "MainWindow",
    "SearchReplaceWidget",
    "SelectionContextMenu",
    "ComposerInputWidget",
    "ComposerDiffWidget",
    "ComposerAIWorker",
]
