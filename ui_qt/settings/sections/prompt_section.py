# -*- coding: utf-8 -*-
"""
AI Novel Generator - Prompt编辑设置分区
=============================
"""

import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
)

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 导入所有prompt定义
from core import prompt_definitions
from core.config_manager import save_config
from ui_qt.utils.styles import Styles

from ..base import BaseSettingsSection


class PromptSection(BaseSettingsSection):
    """
    Prompt编辑设置分区

    提供所有system prompt的编辑和管理功能
    """

    # 信号：恢复默认按钮状态变化
    restore_defaults_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        """
        初始化Prompt编辑设置分区

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 保存原始默认prompt
        self.default_prompts = self._get_default_prompts()

        # 初始化当前编辑的prompt
        self.current_prompts = self._load_prompts_from_config()

        # 是否有编辑过的prompt
        self.has_edited = self._check_has_edited()

        # 构建UI
        self._build_ui()

    def _get_default_prompts(self):
        """
        获取所有默认的prompt定义，按分类组织

        Returns:
            dict: 分类后的prompt字典
        """
        return {
            "摘要和知识库": {
                "当前章节摘要生成": prompt_definitions.summarize_recent_chapters_prompt,
                "知识库相关性检索": prompt_definitions.knowledge_search_prompt,
                "知识库内容过滤": prompt_definitions.knowledge_filter_prompt,
            },
            "核心设定": {
                "核心种子设定": prompt_definitions.core_seed_prompt,
                "角色动力学设定": prompt_definitions.character_dynamics_prompt,
                "世界构建矩阵": prompt_definitions.world_building_prompt,
                "情节架构": prompt_definitions.plot_architecture_prompt,
                "章节目录生成": prompt_definitions.chapter_blueprint_prompt,
                "分块章节目录": prompt_definitions.chunked_chapter_blueprint_prompt,
            },
            "状态更新": {
                "前文摘要更新": prompt_definitions.summary_prompt,
                "创建角色状态": prompt_definitions.create_character_state_prompt,
                "更新角色状态": prompt_definitions.update_character_state_prompt,
            },
            "章节写作": {
                "第一章草稿": prompt_definitions.first_chapter_draft_prompt,
                "后续章节草稿": prompt_definitions.next_chapter_draft_prompt,
            },
            "其他": {
                "角色导入分析": prompt_definitions.Character_Import_Prompt,
            },
        }

    def _load_prompts_from_config(self):
        """
        从配置文件加载prompt

        Returns:
            dict: 加载的prompt字典
        """
        # 总是从默认值开始
        result = self._deep_copy_prompts(self.default_prompts)

        # 如果配置中有custom_prompts，则合并
        if "custom_prompts" in self.loaded_config:
            custom_prompts = self.loaded_config["custom_prompts"]
            for category, items in custom_prompts.items():
                if category in result:
                    for name, content in items.items():
                        if name in result[category]:
                            result[category][name] = content

        return result

    def _deep_copy_prompts(self, prompts):
        """
        深拷贝prompt字典

        Args:
            prompts: 要拷贝的prompt字典

        Returns:
            dict: 拷贝后的prompt字典
        """
        result = {}
        for category, items in prompts.items():
            result[category] = {}
            for name, content in items.items():
                result[category][name] = content
        return result

    def _check_has_edited(self):
        """
        检查是否有编辑过的prompt

        Returns:
            bool: 是否有编辑
        """
        for category, items in self.current_prompts.items():
            for name, content in items.items():
                if (
                    category in self.default_prompts
                    and name in self.default_prompts[category]
                ):
                    if content != self.default_prompts[category][name]:
                        return True
        return False

    def _build_ui(self):
        """
        构建UI界面
        """
        # 标题
        titleLabel = SubtitleLabel("Prompt编辑", self.view)
        self.vBoxLayout.addWidget(titleLabel)

        # 说明
        descLabel = BodyLabel(
            "集中管理和编辑所有AI生成小说时使用的系统提示词", self.view
        )
        self.vBoxLayout.addWidget(descLabel)

        # 添加一些间距
        self.vBoxLayout.addSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal, self.view)
        splitter.setObjectName("promptSplitter")
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # 左侧：分类和prompt列表
        leftWidget = QWidget(splitter)
        leftWidget.setMinimumWidth(250)
        leftLayout = QVBoxLayout(leftWidget)
        leftLayout.setContentsMargins(0, 0, 0, 0)

        # 分类选择 - 使用ComboBox
        categoryLabel = BodyLabel("选择分类：", leftWidget)
        leftLayout.addWidget(categoryLabel)
        self.categoryCombo = ComboBox(leftWidget)
        self.categoryCombo.currentTextChanged.connect(self._switch_category)
        leftLayout.addWidget(self.categoryCombo)

        # prompt列表区域 - 使用滚动区域
        self.promptListScroll = QScrollArea(leftWidget)
        self.promptListScroll.setWidgetResizable(True)
        self.promptListScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.promptListScroll.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )
        self.promptListScroll.viewport().setStyleSheet("background-color: transparent;")

        self.promptListWidget = QWidget()
        self.promptListLayout = QVBoxLayout(self.promptListWidget)
        self.promptListLayout.setContentsMargins(0, 10, 0, 0)
        self.promptListLayout.setSpacing(5)

        self.promptListScroll.setWidget(self.promptListWidget)
        leftLayout.addWidget(self.promptListScroll)

        # 右侧：编辑区域
        rightWidget = QWidget(splitter)
        rightLayout = QVBoxLayout(rightWidget)
        rightLayout.setContentsMargins(0, 0, 0, 0)

        # prompt名称标签
        self.promptNameLabel = StrongBodyLabel("选择一个prompt进行编辑", rightWidget)
        rightLayout.addWidget(self.promptNameLabel)

        # 编辑区域
        self.promptEdit = QTextEdit(rightWidget)
        self.promptEdit.setPlaceholderText("在此编辑prompt内容...")
        self.promptEdit.setAcceptRichText(False)
        self.promptEdit.setMinimumHeight(400)
        self.promptEdit.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 8px;
            }}
            {Styles.ScrollBar}
        """)
        rightLayout.addWidget(self.promptEdit)

        # 按钮区域
        buttonLayout = QHBoxLayout()
        self.saveButton = PrimaryPushButton("保存修改", rightWidget)
        self.saveButton.clicked.connect(self._save_current_prompt)
        self.saveButton.setEnabled(False)
        buttonLayout.addWidget(self.saveButton)

        self.cancelButton = PushButton("取消", rightWidget)
        self.cancelButton.clicked.connect(self._cancel_edit)
        self.cancelButton.setEnabled(False)
        buttonLayout.addWidget(self.cancelButton)

        buttonLayout.addStretch()

        rightLayout.addLayout(buttonLayout)

        # 将widget添加到分割器
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)

        self.vBoxLayout.addWidget(splitter)

        # 初始化分类导航
        self._init_categories()

        # 连接信号
        self.promptEdit.textChanged.connect(self._on_text_changed)

    def _init_categories(self):
        """
        初始化分类导航
        """
        categories = list(self.current_prompts.keys())
        if categories:
            # 添加分类到ComboBox
            for category in categories:
                self.categoryCombo.addItem(category)
            # 默认显示第一个分类
            self.categoryCombo.setCurrentIndex(0)
            self._switch_category(categories[0])

    def _switch_category(self, category):
        """
        切换到指定分类

        Args:
            category: 分类名称
        """
        self.current_category = category

        # 清空prompt列表
        while self.promptListLayout.count():
            item = self.promptListLayout.takeAt(0)
            if item.widget():
                widget = item.widget()
                self.promptListLayout.removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()

        # 添加该分类下的prompt
        if category in self.current_prompts:
            prompts_in_category = self.current_prompts[category]
            for name in prompts_in_category.keys():
                btn = PushButton(name, self.promptListWidget)
                btn.setObjectName(f"promptBtn_{name}")
                btn.clicked.connect(lambda checked, n=name: self._select_prompt(n))
                self.promptListLayout.addWidget(btn)

        self.promptListLayout.addStretch()

    def _select_prompt(self, name):
        """
        选择一个prompt进行编辑

        Args:
            name: prompt名称
        """
        self.current_prompt_name = name
        self.promptNameLabel.setText(name)

        if (
            self.current_category in self.current_prompts
            and name in self.current_prompts[self.current_category]
        ):
            self.original_content = self.current_prompts[self.current_category][name]
            self.promptEdit.setPlainText(self.original_content)
            self.saveButton.setEnabled(False)
            self.cancelButton.setEnabled(False)

    def _on_text_changed(self):
        """
        当编辑区域内容变化时的处理
        """
        if hasattr(self, "original_content"):
            current_text = self.promptEdit.toPlainText()
            has_changes = current_text != self.original_content
            self.saveButton.setEnabled(has_changes)
            self.cancelButton.setEnabled(has_changes)

    def _save_current_prompt(self):
        """
        保存当前编辑的prompt
        """
        if not hasattr(self, "current_prompt_name") or not hasattr(
            self, "current_category"
        ):
            return

        current_text = self.promptEdit.toPlainText()
        self.current_prompts[self.current_category][
            self.current_prompt_name
        ] = current_text
        self.original_content = current_text

        # 更新配置
        if "custom_prompts" not in self.loaded_config:
            self.loaded_config["custom_prompts"] = {}
        self.loaded_config["custom_prompts"] = self._deep_copy_prompts(
            self.current_prompts
        )

        save_config(self.loaded_config, self.config_file)

        # 更新编辑状态
        self.has_edited = self._check_has_edited()
        self.restore_defaults_changed.emit(self.has_edited)

        self.saveButton.setEnabled(False)
        self.cancelButton.setEnabled(False)

        self.show_info("保存成功", f"Prompt '{self.current_prompt_name}' 已保存")

    def _cancel_edit(self):
        """
        取消编辑
        """
        if hasattr(self, "original_content"):
            self.promptEdit.setPlainText(self.original_content)
            self.saveButton.setEnabled(False)
            self.cancelButton.setEnabled(False)

    def restore_defaults(self):
        """
        恢复所有prompt为默认值
        """
        w = MessageBox(
            "确认恢复",
            "确定要将所有Prompt恢复为默认值吗？此操作不可撤销！",
            self.window(),
        )
        if w.exec():
            self.current_prompts = self._deep_copy_prompts(self.default_prompts)

            # 更新配置
            if "custom_prompts" in self.loaded_config:
                del self.loaded_config["custom_prompts"]

            save_config(self.loaded_config, self.config_file)

            # 更新状态
            self.has_edited = False
            self.restore_defaults_changed.emit(False)

            # 刷新显示
            if hasattr(self, "current_category"):
                self._switch_category(self.current_category)
            if hasattr(self, "promptEdit"):
                self.promptEdit.clear()
                self.promptNameLabel.setText("选择一个prompt进行编辑")
                self.saveButton.setEnabled(False)
                self.cancelButton.setEnabled(False)

            self.show_info("恢复成功", "所有Prompt已恢复为默认值")

    def is_edited(self):
        """
        检查是否有编辑过的prompt

        Returns:
            bool: 是否有编辑
        """
        return self.has_edited
