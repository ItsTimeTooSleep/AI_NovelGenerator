# -*- coding: utf-8 -*-
"""
布局管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责管理首页的界面布局，实现简化布局和完整布局之间的切换。
根据当前步骤状态自动调整界面元素的显示和排列。

================================================================================
核心类
================================================================================
- LayoutManager: 布局管理器

================================================================================
核心功能
================================================================================
- _apply_simplified_layout: 应用简化布局（Step1/Step2）
- _apply_full_layout: 应用完整布局（Step3/Step4）
- _clear_layout: 清理布局中的所有组件

================================================================================
布局模式
================================================================================
简化布局模式（Step1/Step2）:
    └── 居中显示初始化卡片，隐藏左右面板
完整布局模式（Step3/Step4）:
    ├── 左侧：章节列表和日志面板
    └── 右侧：编辑器和操作按钮

================================================================================
设计决策
================================================================================
- 使用AlignTop确保内容靠上对齐
- 使用Maximum策略控制卡片高度
- 切换布局时清理旧组件，避免内存泄漏
- 日志面板可折叠，优化屏幕空间利用

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy


class LayoutManager:
    def __init__(self, home_tab):
        self.home_tab = home_tab

    def _apply_simplified_layout(self):
        self.home_tab.fullLayout.removeWidget(self.home_tab.initCard)
        while self.home_tab.centerLayout.count():
            item = self.home_tab.centerLayout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())

        # 使用 AlignTop 确保卡片靠上对齐，防止垂直居中导致的空白问题
        self.home_tab.centerLayout.setAlignment(Qt.AlignTop)
        self.home_tab.centerLayout.addWidget(self.home_tab.initCard, 1)
        self.home_tab.initCard.setParent(self.home_tab.centerContainer)
        self.home_tab.initCard.show()
        # 不要设置最大宽度，让卡片自然填充
        # self.home_tab.initCard.setMaximumWidth(16777215)
        # 使用 Expanding 策略让卡片填充可用宽度
        self.home_tab.initCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.home_tab.initCard.setMaximumHeight(16777215)
        self.home_tab.initLayout.setContentsMargins(16, 0, 16, 12)
        self.home_tab.leftPanel.hide()
        self.home_tab.rightStack.setCurrentIndex(0)
        self.home_tab._guide_mode = True
        self.home_tab._log_panel_expanded = False
        if self.home_tab.logOutput.parent() == self.home_tab.leftPanel:
            self.home_tab.leftLayout.removeWidget(self.home_tab.logOutput)
            self.home_tab.logOutput.setParent(self.home_tab.logPanel)
            self.home_tab.logOutput.setMaximumHeight(16777215)
            self.home_tab.logPanelLayout.addWidget(self.home_tab.logOutput, 1)
        # 在Step 1和Step 2时显示日志栏和箭头开关
        self.home_tab.log_panel_manager.set_visible_in_step3(True)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())

    def _apply_full_layout(self):
        import logging
        logging.info("[DEBUG] LayoutManager._apply_full_layout 开始执行")
        
        try:
            logging.info("[DEBUG] 清理 centerLayout 中的所有组件")
            while self.home_tab.centerLayout.count():
                item = self.home_tab.centerLayout.takeAt(0)
                if item.widget():
                    logging.info(f"[DEBUG] 移除组件: {item.widget().objectName()}")
                    item.widget().setParent(None)
                elif item.layout():
                    logging.info("[DEBUG] 清理子布局")
                    self._clear_layout(item.layout())
            
            logging.info("[DEBUG] 设置 initCard 最大宽度")
            self.home_tab.initCard.setMaximumWidth(16777215)
            
            logging.info("[DEBUG] 设置 initCard 样式")
            self.home_tab.initCard.setStyleSheet("")
            
            logging.info("[DEBUG] 设置 initLayout 边距")
            self.home_tab.initLayout.setContentsMargins(6, 6, 6, 6)
            
            logging.info("[DEBUG] 隐藏 initCard")
            self.home_tab.initCard.hide()
            
            logging.info("[DEBUG] 显示 leftPanel")
            self.home_tab.leftPanel.show()
            
            logging.info("[DEBUG] 设置 rightStack 当前索引为 1")
            self.home_tab.rightStack.setCurrentIndex(1)
            
            logging.info("[DEBUG] 设置 _guide_mode 为 False")
            self.home_tab._guide_mode = False
            
            logging.info("[DEBUG] 设置 _log_panel_expanded 为 False")
            self.home_tab._log_panel_expanded = False
            
            if self.home_tab.logOutput.parent() == self.home_tab.logPanel:
                logging.info("[DEBUG] 移动 logOutput 到 leftPanel")
                self.home_tab.logPanelLayout.removeWidget(self.home_tab.logOutput)
                self.home_tab.logOutput.setParent(self.home_tab.leftPanel)
                self.home_tab.logOutput.setMaximumHeight(200)
                self.home_tab.leftLayout.addWidget(self.home_tab.logOutput, 1)
            
            # 在Step Three时隐藏日志栏和箭头开关
            logging.info("[DEBUG] 调用 log_panel_manager.set_visible_in_step3(False)")
            self.home_tab.log_panel_manager.set_visible_in_step3(False)
            
            logging.info("[DEBUG] LayoutManager._apply_full_layout 执行成功")
        except Exception as e:
            logging.error(f"[DEBUG] LayoutManager._apply_full_layout 执行失败: {e}")
            import traceback
            logging.error(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
