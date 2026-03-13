# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import datetime
import os
import sys
import uuid

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    FlowLayout,
    IconWidget,
    MessageBox,
    MessageBoxBase,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from core.version import (
    AUTHOR,
    DONATION_URL,
    GITHUB_API_RELEASES_URL,
    GITHUB_REPO_URL,
    LICENSE_URL,
    __version__,
)

from core.config_manager import (
    test_embedding_config,
    test_llm_config,
)
from ui_qt.utils.helpers import get_global_notify
from ui_qt.utils.styles import Styles
from ui_qt.widgets.placeholder_widget import EmptyState, PlaceholderWidget

from ..base import BaseSettingsSection
from ..components import EmbeddingCard, ModelCard
from ..dialogs import (
    EmbeddingConfigDialog,
    ModelConfigDialog,
    ModelSelectionDialog,
)


class LLMSection(BaseSettingsSection):
    """
    LLM（大语言模型）配置分区 - 图书馆风格设计

    使用卡片式布局展示所有LLM配置，支持新增、编辑、删除和测试。
    """

    def __init__(self, parent=None):
        """
        初始化LLM配置分区

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 顶部标题区域
        self.headerWidget = QWidget(self.view)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.iconWidget = IconWidget(FIF.ROBOT, self.view)
        self.iconWidget.setFixedSize(32, 32)

        self.titleContainer = QWidget()
        self.titleLayout = QVBoxLayout(self.titleContainer)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.setSpacing(0)

        self.titleLabel = SubtitleLabel("AI 模型库", self.view)

        self.subtitleLabel = BodyLabel("管理您的大语言模型配置", self.view)
        self.subtitleLabel.setStyleSheet(Styles.SecondaryText)

        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addWidget(self.subtitleLabel)

        self.createBtn = PrimaryPushButton(FIF.ADD, "新增模型", self.view)
        self.createBtn.clicked.connect(self.show_add_dialog)

        self.selectionBtn = PushButton(FIF.MENU, "模型选择", self.view)
        self.selectionBtn.clicked.connect(self.show_selection_dialog)

        self.headerLayout.addWidget(self.iconWidget)
        self.headerLayout.addSpacing(10)
        self.headerLayout.addWidget(self.titleContainer)
        self.headerLayout.addStretch()
        self.headerLayout.addWidget(self.selectionBtn)
        self.headerLayout.addSpacing(10)
        self.headerLayout.addWidget(self.createBtn)

        self.vBoxLayout.addWidget(self.headerWidget)
        self.vBoxLayout.addSpacing(20)

        # LLM 模型区域
        self.llmHeader = StrongBodyLabel("LLM 模型", self.view)
        self.vBoxLayout.addWidget(self.llmHeader)
        self.vBoxLayout.addSpacing(10)

        # LLM 模型卡片容器
        self.llmGridWidget = QWidget()
        self.llmFlowLayout = FlowLayout(self.llmGridWidget, needAni=True)
        self.llmFlowLayout.setContentsMargins(0, 0, 0, 0)
        self.llmFlowLayout.setVerticalSpacing(20)
        self.llmFlowLayout.setHorizontalSpacing(20)

        self.vBoxLayout.addWidget(self.llmGridWidget)
        self.vBoxLayout.addSpacing(20)

        # Embedding 模型区域
        self.embeddingHeader = StrongBodyLabel("Embedding 模型", self.view)
        self.vBoxLayout.addWidget(self.embeddingHeader)
        self.vBoxLayout.addSpacing(10)

        # Embedding 模型卡片容器
        self.embeddingGridWidget = QWidget()
        self.embeddingFlowLayout = FlowLayout(self.embeddingGridWidget, needAni=True)
        self.embeddingFlowLayout.setContentsMargins(0, 0, 0, 0)
        self.embeddingFlowLayout.setVerticalSpacing(20)
        self.embeddingFlowLayout.setHorizontalSpacing(20)

        self.vBoxLayout.addWidget(self.embeddingGridWidget)
        self.vBoxLayout.addStretch()

        # 确保有默认配置
        self.ensure_default_configs()

        # 刷新显示
        self.refresh_model_cards()

    def ensure_default_configs(self):
        """确保配置中有默认的模型配置"""
        # 确保 llm_configs 存在
        if "llm_configs" not in self.loaded_config:
            self.loaded_config["llm_configs"] = {}
        if not self.loaded_config["llm_configs"]:
            self.loaded_config["llm_configs"]["DeepSeek"] = {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model_name": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 8192,
                "timeout": 600,
                "interface_format": "DeepSeek",
                "created_at": datetime.datetime.now().isoformat(),
            }

        # 确保 embedding_configs 存在
        if "embedding_configs" not in self.loaded_config:
            self.loaded_config["embedding_configs"] = {}
        if not self.loaded_config["embedding_configs"]:
            self.loaded_config["embedding_configs"]["默认 Embedding"] = {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "text-embedding-ada-002",
                "retrieval_k": 4,
                "interface_format": "OpenAI",
                "created_at": datetime.datetime.now().isoformat(),
            }

        self.save_config_to_file()

    def refresh_model_cards(self):
        """刷新模型卡片显示"""
        try:
            # 清空 LLM 区域
            while self.llmFlowLayout.count():
                item = self.llmFlowLayout.takeAt(0)
                if hasattr(item, "widget") and callable(getattr(item, "widget")):
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                elif isinstance(item, QWidget):
                    item.deleteLater()

            # 清空 Embedding 区域
            while self.embeddingFlowLayout.count():
                item = self.embeddingFlowLayout.takeAt(0)
                if hasattr(item, "widget") and callable(getattr(item, "widget")):
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                elif isinstance(item, QWidget):
                    item.deleteLater()

            # 刷新 LLM 模型卡片
            llm_configs = self.loaded_config.get("llm_configs", {})
            if not llm_configs:
                llm_empty_state = EmptyState.llm_models()
                llm_placeholder = PlaceholderWidget(
                    llm_empty_state["icon"],
                    llm_empty_state["title"],
                    llm_empty_state["description"],
                    self.view,
                )
                llm_placeholder.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding
                )
                self.llmFlowLayout.addWidget(llm_placeholder)
            else:
                for config_name, config_data in llm_configs.items():
                    card = ModelCard(config_name, config_data, self.view)
                    card.editRequested.connect(self.on_edit_requested)
                    card.deleteRequested.connect(self.on_delete_requested)
                    card.testRequested.connect(self.on_test_requested)
                    self.llmFlowLayout.addWidget(card)

            # 刷新 Embedding 模型卡片
            embedding_configs = self.loaded_config.get("embedding_configs", {})
            if not embedding_configs:
                embedding_empty_state = {
                    "icon": FIF.ROBOT,
                    "title": "暂无设置的 Embedding 模型",
                    "description": "点击右上角「新增模型」按钮，添加您的 Embedding 模型配置吧！",
                }
                embedding_placeholder = PlaceholderWidget(
                    embedding_empty_state["icon"],
                    embedding_empty_state["title"],
                    embedding_empty_state["description"],
                    self.view,
                )
                embedding_placeholder.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding
                )
                self.embeddingFlowLayout.addWidget(embedding_placeholder)
            else:
                for config_name, config_data in embedding_configs.items():
                    card = EmbeddingCard(config_name, config_data, self.view)
                    card.editRequested.connect(self.on_embedding_edit_requested)
                    card.deleteRequested.connect(self.on_embedding_delete_requested)
                    card.testRequested.connect(self.on_embedding_test_requested)
                    self.embeddingFlowLayout.addWidget(card)

        except Exception as e:
            print(f"Error loading model cards: {e}")
            notify = get_global_notify()
            if notify:
                notify.error("加载失败", str(e))

    def show_add_dialog(self):
        """显示新增模型对话框"""

        # 创建模型类型选择对话框
        class ModelTypeDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("选择模型类型")
                self.titleLabel = SubtitleLabel("请选择要新增的模型类型", self)
                self.viewLayout.addWidget(self.titleLabel)

                self.llmBtn = PrimaryPushButton("LLM 模型", self)
                self.embeddingBtn = PrimaryPushButton("Embedding 模型", self)

                self.viewLayout.addWidget(self.llmBtn)
                self.viewLayout.addWidget(self.embeddingBtn)

                self.selected_type = None

                self.llmBtn.clicked.connect(lambda: self.select_type("llm"))
                self.embeddingBtn.clicked.connect(lambda: self.select_type("embedding"))

                self.widget.setMinimumWidth(300)

            def select_type(self, type_):
                self.selected_type = type_
                self.accept()

        # 显示类型选择对话框
        type_dialog = ModelTypeDialog(parent=self.window())
        if not type_dialog.exec():
            return

        model_type = type_dialog.selected_type

        # 根据选择的类型显示相应的配置对话框
        if model_type == "llm":
            dialog = ModelConfigDialog(parent=self.window())
            config_key = "llm_configs"
        else:
            dialog = EmbeddingConfigDialog(parent=self.window())
            config_key = "embedding_configs"

        if dialog.exec():
            config_name, config_data = dialog.get_config_data()
            notify = get_global_notify()
            if not config_name:
                if notify:
                    notify.warning("提示", "配置名称不能为空")
                return
            if config_name in self.loaded_config.get(config_key, {}):
                if notify:
                    notify.error("错误", "配置名称已存在")
                return

            self.loaded_config[config_key][config_name] = config_data
            if self.save_config_to_file():
                self.refresh_model_cards()
                if notify:
                    notify.success("成功", f"已添加配置 {config_name}")

    def on_edit_requested(self, config_name, config_data):
        """处理编辑请求"""
        notify = get_global_notify()
        dialog = ModelConfigDialog(config_name, config_data, parent=self.window())
        if dialog.exec():
            new_name, new_data = dialog.get_config_data()
            if new_name != config_name:
                if new_name in self.loaded_config.get("llm_configs", {}):
                    if notify:
                        notify.error("错误", "配置名称已存在")
                    return
                self.loaded_config["llm_configs"][new_name] = self.loaded_config[
                    "llm_configs"
                ].pop(config_name)
                self.update_model_selection_references(config_name, new_name)
            else:
                self.loaded_config["llm_configs"][config_name] = new_data

            if self.save_config_to_file():
                self.refresh_model_cards()
                if notify:
                    notify.success("成功", "配置已更新")

    def on_embedding_edit_requested(self, config_name, config_data):
        """处理 Embedding 模型编辑请求"""
        notify = get_global_notify()
        dialog = EmbeddingConfigDialog(config_name, config_data, parent=self.window())
        if dialog.exec():
            new_name, new_data = dialog.get_config_data()
            if new_name != config_name:
                if new_name in self.loaded_config.get("embedding_configs", {}):
                    if notify:
                        notify.error("错误", "配置名称已存在")
                    return
                self.loaded_config["embedding_configs"][new_name] = self.loaded_config[
                    "embedding_configs"
                ].pop(config_name)
            else:
                self.loaded_config["embedding_configs"][config_name] = new_data

            if self.save_config_to_file():
                self.refresh_model_cards()
                if notify:
                    notify.success("成功", "配置已更新")

    def update_model_selection_references(self, old_name, new_name):
        """更新模型选择中的引用"""
        choose_configs = self.loaded_config.get("choose_configs", {})
        for key, value in choose_configs.items():
            if value == old_name:
                choose_configs[key] = new_name

    def on_delete_requested(self, config_name):
        """处理删除请求"""
        notify = get_global_notify()
        if len(self.loaded_config.get("llm_configs", {})) <= 1:
            if notify:
                notify.error("错误", "至少保留一个LLM配置")
            return

        first_dialog = MessageBox(
            "确认删除", f"确定要删除配置「{config_name}」吗？", self.window()
        )
        if not first_dialog.exec():
            return

        second_dialog = MessageBox(
            "二次确认",
            f"此操作将永久删除「{config_name}」配置，无法恢复！",
            self.window(),
        )
        if not second_dialog.exec():
            return

        del self.loaded_config["llm_configs"][config_name]

        # 清理模型选择中的引用
        choose_configs = self.loaded_config.get("choose_configs", {})
        configs = list(self.loaded_config.get("llm_configs", {}).keys())
        for key, value in choose_configs.items():
            if value == config_name and configs:
                choose_configs[key] = configs[0]
            elif value == config_name and not configs:
                del choose_configs[key]

        if self.save_config_to_file():
            self.refresh_model_cards()
            if notify:
                notify.success("成功", f"「{config_name}」已删除")

    def on_test_requested(self, config_data):
        """处理测试请求"""
        notify = get_global_notify()

        def log_func(msg):
            if notify:
                notify.info("测试结果", msg)

        def handle_exception(msg):
            if notify:
                notify.error("测试错误", msg)

        test_llm_config(
            interface_format=config_data.get("interface_format", "OpenAI"),
            api_key=config_data.get("api_key", ""),
            base_url=config_data.get("base_url", ""),
            model_name=config_data.get("model_name", ""),
            temperature=float(config_data.get("temperature", 0.7)),
            max_tokens=int(config_data.get("max_tokens", 8192)),
            timeout=int(config_data.get("timeout", 600)),
            log_func=log_func,
            handle_exception_func=handle_exception,
        )

    def show_selection_dialog(self):
        """显示模型选择对话框"""
        notify = get_global_notify()
        llm_configs = list(self.loaded_config.get("llm_configs", {}).keys())
        llm_configs_data = self.loaded_config.get("llm_configs", {})
        embedding_configs = list(self.loaded_config.get("embedding_configs", {}).keys())

        if not llm_configs:
            if notify:
                notify.warning("提示", "请先添加 LLM 模型配置")
            return

        choose_configs = self.loaded_config.get("choose_configs", {})
        dialog = ModelSelectionDialog(
            llm_configs,
            llm_configs_data,
            embedding_configs,
            choose_configs,
            parent=self.window(),
        )

        if dialog.exec():
            selection = dialog.get_selection()
            if "choose_configs" not in self.loaded_config:
                self.loaded_config["choose_configs"] = {}

            self.loaded_config["choose_configs"].update(selection)

            if self.save_config_to_file():
                if notify:
                    notify.success("成功", "模型选择配置已保存")

    def on_embedding_delete_requested(self, config_name):
        """处理 Embedding 模型删除请求"""
        notify = get_global_notify()
        first_dialog = MessageBox(
            "确认删除", f"确定要删除配置「{config_name}」吗？", self.window()
        )
        if not first_dialog.exec():
            return

        second_dialog = MessageBox(
            "二次确认",
            f"此操作将永久删除「{config_name}」配置，无法恢复！",
            self.window(),
        )
        if not second_dialog.exec():
            return

        del self.loaded_config["embedding_configs"][config_name]

        if self.save_config_to_file():
            self.refresh_model_cards()
            if notify:
                notify.success("成功", f"「{config_name}」已删除")

    def on_embedding_test_requested(self, config_data):
        """处理 Embedding 模型测试请求"""
        notify = get_global_notify()

        def log_func(msg):
            if notify:
                notify.info("测试结果", msg)

        def handle_exception(msg):
            if notify:
                notify.error("测试错误", msg)

        test_embedding_config(
            api_key=config_data.get("api_key", ""),
            base_url=config_data.get("base_url", ""),
            interface_format=config_data.get("interface_format", "OpenAI"),
            model_name=config_data.get("model_name", ""),
            log_func=log_func,
            handle_exception_func=handle_exception,
        )
