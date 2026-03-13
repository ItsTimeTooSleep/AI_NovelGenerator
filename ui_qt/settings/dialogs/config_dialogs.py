# -*- coding: utf-8 -*-
"""
AI Novel Generator - 配置对话框模块
==============================

本模块包含用于配置模型和相关设置的对话框：
- ModelConfigDialog: LLM 模型配置编辑对话框
- EmbeddingConfigDialog: Embedding 模型配置编辑对话框
- ModelSelectionDialog: 模型选择对话框
"""

import datetime

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    LineEdit,
    MessageBoxBase,
    PushButton,
    Slider,
    StrongBodyLabel,
    SubtitleLabel,
)

from core.config_manager import test_embedding_config, test_llm_config
from ui_qt.utils.helpers import get_global_notify

from ...utils.dialog_sizer import DialogSizer, ScrollableContainer
from ...utils.styles import ThemeManager
from ..utils import ModelPresetManager


class TestResultSignaler(QObject):
    """
    测试结果信号发射器

    用于在子线程中发射信号，确保 UI 更新在主线程中执行。
    解决 QObject::setParent 跨线程错误问题。

    参数:
        无

    信号:
        info_signal: 发送信息消息信号，参数为 (title, message)
        error_signal: 发送错误消息信号，参数为 (title, message)

    使用示例:
        >>> signaler = TestResultSignaler()
        >>> signaler.info_signal.connect(lambda t, m: show_info(t, m))
        >>> signaler.info_signal.emit("标题", "消息内容")
    """

    info_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str, str)


class EmbeddingConfigDialog(MessageBoxBase):
    """
    Embedding 模型配置编辑对话框

    用于新增或编辑 Embedding 模型配置，包含所有必要的配置字段。
    支持根据选择的接口格式自动填充 Base URL 和模型名称。
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, config_name=None, config_data=None, parent=None):
        """
        初始化 Embedding 模型配置编辑对话框

        Args:
            config_name: 配置名称，None表示新增模式
            config_data: 配置数据字典，None表示新增模式
            parent: 父控件
        """
        super().__init__(parent)
        self.config_name = config_name
        self.config_data = config_data or {}
        self.is_edit_mode = config_name is not None

        self._baseUrlUserEdited = False
        self._modelNameUserEdited = False

        self._testSignaler = TestResultSignaler()
        self._testSignaler.info_signal.connect(self._showTestInfo)
        self._testSignaler.error_signal.connect(self._showTestError)

        self.titleLabel = SubtitleLabel(
            "编辑 Embedding 配置" if self.is_edit_mode else "新增 Embedding 配置", self
        )
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(15)

        self.nameLabel = BodyLabel("配置名称", self._container)
        self.nameEdit = LineEdit(self._container)
        if self.is_edit_mode:
            self.nameEdit.setText(config_name)
        content_layout.addWidget(self.nameLabel)
        content_layout.addWidget(self.nameEdit)

        self.apiKeyLabel = BodyLabel("API Key", self._container)
        self.apiKeyEdit = LineEdit(self._container)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)
        self.apiKeyEdit.setText(self.config_data.get("api_key", ""))
        content_layout.addWidget(self.apiKeyLabel)
        content_layout.addWidget(self.apiKeyEdit)

        self.baseUrlLabel = BodyLabel("Base URL", self._container)
        self.baseUrlEdit = LineEdit(self._container)
        self.baseUrlEdit.setText(self.config_data.get("base_url", ""))
        self.baseUrlEdit.textChanged.connect(self._onBaseUrlChanged)
        content_layout.addWidget(self.baseUrlLabel)
        content_layout.addWidget(self.baseUrlEdit)

        self.formatLabel = BodyLabel("接口格式", self._container)
        self.formatCombo = ComboBox(self._container)
        self.formatCombo.addItem("--- 请选择接口格式 ---")
        self.formatCombo.addItems(ModelPresetManager.get_embedding_formats())
        if self.is_edit_mode and self.config_data.get("interface_format"):
            self.formatCombo.setCurrentText(self.config_data.get("interface_format"))
        else:
            self.formatCombo.setCurrentIndex(0)
        self.formatCombo.currentTextChanged.connect(self.on_format_changed)
        content_layout.addWidget(self.formatLabel)
        content_layout.addWidget(self.formatCombo)

        content_layout.addSpacing(5)
        self.formatHintLabel = CaptionLabel(
            "💡 选择接口格式后将自动填充推荐的 Base URL 和模型名称", self._container
        )
        self.formatHintLabel.setStyleSheet(
            f"color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
        )
        content_layout.addWidget(self.formatHintLabel)
        content_layout.addSpacing(5)

        self.modelLabel = BodyLabel("模型名称", self._container)
        self.modelEdit = LineEdit(self._container)
        self.modelEdit.setText(self.config_data.get("model_name", ""))
        self.modelEdit.textChanged.connect(self._onModelNameChanged)
        content_layout.addWidget(self.modelLabel)
        content_layout.addWidget(self.modelEdit)

        self.kLabel = BodyLabel("Retrieval Top-K", self._container)
        self.kEdit = LineEdit(self._container)
        self.kEdit.setText(str(self.config_data.get("retrieval_k", 4)))
        content_layout.addWidget(self.kLabel)
        content_layout.addWidget(self.kEdit)

        self.testBtn = PushButton("测试配置", self._container)
        self.testBtn.clicked.connect(self.test_config)
        content_layout.addWidget(self.testBtn)

        content_layout.addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.60,
            min_width=450,
            min_height=450,
            max_height=700,
        )
        sizer.apply_to_widget(self.widget, parent)

    def _onBaseUrlChanged(self):
        """标记 Base URL 已被用户手动编辑"""
        self._baseUrlUserEdited = True

    def _onModelNameChanged(self):
        """标记模型名称已被用户手动编辑"""
        self._modelNameUserEdited = True

    def on_format_changed(self, interface_format: str):
        """
        当接口格式改变时，自动填充 Base URL 和模型名称（仅在字段未被用户手动编辑时）

        Args:
            interface_format: 新选择的接口格式
        """
        if interface_format == "--- 请选择接口格式 ---":
            return

        preset = ModelPresetManager.get_embedding_preset(interface_format)
        if preset:
            if not self._baseUrlUserEdited:
                self.baseUrlEdit.blockSignals(True)
                self.baseUrlEdit.setText(preset.get("base_url", ""))
                self.baseUrlEdit.blockSignals(False)
            if not self._modelNameUserEdited:
                self.modelEdit.blockSignals(True)
                self.modelEdit.setText(preset.get("model_name", ""))
                self.modelEdit.blockSignals(False)

    def get_config_data(self):
        """
        获取配置数据

        Returns:
            tuple: (config_name, config_data)
        """
        import uuid

        # 获取当前选择的接口格式，如果是占位符则返回空
        current_format = self.formatCombo.currentText()
        if current_format == "--- 请选择接口格式 ---":
            current_format = ""

        config_data = {
            "id": self.config_data.get("id", str(uuid.uuid4())),
            "api_key": self.apiKeyEdit.text(),
            "base_url": self.baseUrlEdit.text(),
            "interface_format": current_format,
            "model_name": self.modelEdit.text(),
            "retrieval_k": int(self.kEdit.text() or 4),
            "created_at": self.config_data.get(
                "created_at", datetime.datetime.now().isoformat()
            ),
            "updated_at": datetime.datetime.now().isoformat(),
        }
        return (self.nameEdit.text(), config_data)

    def test_config(self):
        """
        测试当前配置

        该方法在子线程中执行测试，通过信号机制确保 UI 更新在主线程中执行。
        解决 QObject::setParent 跨线程错误问题。

        参数:
            无

        返回值:
            无
        """
        current_format = self.formatCombo.currentText()
        if current_format == "--- 请选择接口格式 ---":
            current_format = ""

        test_embedding_config(
            api_key=self.apiKeyEdit.text(),
            base_url=self.baseUrlEdit.text(),
            interface_format=current_format,
            model_name=self.modelEdit.text(),
            log_func=lambda msg: self._testSignaler.info_signal.emit("测试结果", msg),
            handle_exception_func=lambda msg: self._testSignaler.error_signal.emit(
                "测试错误", msg
            ),
        )

    def _showTestInfo(self, title: str, message: str):
        """
        在主线程中显示测试信息

        参数:
            title: 信息标题
            message: 信息内容

        返回值:
            无
        """
        notify = get_global_notify()
        if notify:
            notify.info(title, message)

    def _showTestError(self, title: str, message: str):
        """
        在主线程中显示测试错误

        参数:
            title: 错误标题
            message: 错误内容

        返回值:
            无
        """
        notify = get_global_notify()
        if notify:
            notify.error(title, message)


class ModelConfigDialog(MessageBoxBase):
    """
    模型配置编辑对话框

    用于新增或编辑LLM模型配置，包含所有必要的配置字段。
    支持根据选择的接口格式自动填充 Base URL 和模型名称。
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, config_name=None, config_data=None, parent=None):
        """
        初始化模型配置编辑对话框

        Args:
            config_name: 配置名称，None表示新增模式
            config_data: 配置数据字典，None表示新增模式
            parent: 父控件
        """
        super().__init__(parent)
        self.config_name = config_name
        self.config_data = config_data or {}
        self.is_edit_mode = config_name is not None

        self._baseUrlUserEdited = False
        self._modelNameUserEdited = False

        self._testSignaler = TestResultSignaler()
        self._testSignaler.info_signal.connect(self._showTestInfo)
        self._testSignaler.error_signal.connect(self._showTestError)

        self.titleLabel = SubtitleLabel(
            "编辑模型配置" if self.is_edit_mode else "新增模型配置", self
        )
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(15)

        self.nameLabel = BodyLabel("配置名称", self._container)
        self.nameEdit = LineEdit(self._container)
        if self.is_edit_mode:
            self.nameEdit.setText(config_name)
        content_layout.addWidget(self.nameLabel)
        content_layout.addWidget(self.nameEdit)

        self.apiKeyLabel = BodyLabel("API Key", self._container)
        self.apiKeyEdit = LineEdit(self._container)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)
        self.apiKeyEdit.setText(self.config_data.get("api_key", ""))
        content_layout.addWidget(self.apiKeyLabel)
        content_layout.addWidget(self.apiKeyEdit)

        self.baseUrlLabel = BodyLabel("Base URL", self._container)
        self.baseUrlEdit = LineEdit(self._container)
        self.baseUrlEdit.setText(self.config_data.get("base_url", ""))
        self.baseUrlEdit.textChanged.connect(self._onBaseUrlChanged)
        content_layout.addWidget(self.baseUrlLabel)
        content_layout.addWidget(self.baseUrlEdit)

        self.formatLabel = BodyLabel("接口格式", self._container)
        self.formatCombo = ComboBox(self._container)
        self.formatCombo.addItem("--- 请选择接口格式 ---")
        self.formatCombo.addItems(ModelPresetManager.get_llm_formats())
        if self.is_edit_mode and self.config_data.get("interface_format"):
            self.formatCombo.setCurrentText(self.config_data.get("interface_format"))
        else:
            self.formatCombo.setCurrentIndex(0)
        self.formatCombo.currentTextChanged.connect(self.on_format_changed)
        content_layout.addWidget(self.formatLabel)
        content_layout.addWidget(self.formatCombo)

        content_layout.addSpacing(5)
        self.formatHintLabel = CaptionLabel(
            "💡 选择接口格式后将自动填充推荐的 Base URL 和模型名称", self._container
        )
        self.formatHintLabel.setStyleSheet(
            f"color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
        )
        content_layout.addWidget(self.formatHintLabel)
        content_layout.addSpacing(5)

        self.modelLabel = BodyLabel("模型名称", self._container)
        self.modelEdit = LineEdit(self._container)
        self.modelEdit.setText(self.config_data.get("model_name", ""))
        self.modelEdit.textChanged.connect(self._onModelNameChanged)
        content_layout.addWidget(self.modelLabel)
        content_layout.addWidget(self.modelEdit)

        temp_value = float(self.config_data.get("temperature", 0.7))
        self.tempLabel = BodyLabel(f"Temperature: {temp_value:.2f}", self._container)
        self.tempSlider = Slider(Qt.Horizontal, self._container)
        self.tempSlider.setRange(0, 200)
        self.tempSlider.setValue(int(temp_value * 100))
        self.tempSlider.valueChanged.connect(
            lambda v: self.tempLabel.setText(f"Temperature: {v/100:.2f}")
        )
        content_layout.addWidget(self.tempLabel)
        content_layout.addWidget(self.tempSlider)

        tokens_value = int(self.config_data.get("max_tokens", 8192))
        self.tokensLabel = BodyLabel(f"Max Tokens: {tokens_value}", self._container)
        self.tokensSlider = Slider(Qt.Horizontal, self._container)
        self.tokensSlider.setRange(0, 102400)
        self.tokensSlider.setValue(tokens_value)
        self.tokensSlider.valueChanged.connect(
            lambda v: self.tokensLabel.setText(f"Max Tokens: {v}")
        )
        content_layout.addWidget(self.tokensLabel)
        content_layout.addWidget(self.tokensSlider)

        timeout_value = int(self.config_data.get("timeout", 600))
        self.timeoutLabel = BodyLabel(f"Timeout: {timeout_value}s", self._container)
        self.timeoutSlider = Slider(Qt.Horizontal, self._container)
        self.timeoutSlider.setRange(0, 3600)
        self.timeoutSlider.setValue(timeout_value)
        self.timeoutSlider.valueChanged.connect(
            lambda v: self.timeoutLabel.setText(f"Timeout: {v}s")
        )
        content_layout.addWidget(self.timeoutLabel)
        content_layout.addWidget(self.timeoutSlider)

        self.testBtn = PushButton("测试配置", self._container)
        self.testBtn.clicked.connect(self.test_config)
        content_layout.addWidget(self.testBtn)

        content_layout.addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.65,
            min_width=450,
            min_height=500,
            max_height=700,
        )
        sizer.apply_to_widget(self.widget, parent)

    def _onBaseUrlChanged(self):
        """标记 Base URL 已被用户手动编辑"""
        self._baseUrlUserEdited = True

    def _onModelNameChanged(self):
        """标记模型名称已被用户手动编辑"""
        self._modelNameUserEdited = True

    def on_format_changed(self, interface_format: str):
        """
        当接口格式改变时，自动填充 Base URL 和模型名称（仅在字段未被用户手动编辑时）

        Args:
            interface_format: 新选择的接口格式
        """
        if interface_format == "--- 请选择接口格式 ---":
            return

        preset = ModelPresetManager.get_llm_preset(interface_format)
        if preset:
            if not self._baseUrlUserEdited:
                self.baseUrlEdit.blockSignals(True)
                self.baseUrlEdit.setText(preset.get("base_url", ""))
                self.baseUrlEdit.blockSignals(False)
            if not self._modelNameUserEdited:
                self.modelEdit.blockSignals(True)
                self.modelEdit.setText(preset.get("model_name", ""))
                self.modelEdit.blockSignals(False)

    def get_config_data(self):
        """
        获取配置数据

        Returns:
            tuple: (config_name, config_data)
        """
        import uuid

        # 获取当前选择的接口格式，如果是占位符则返回空
        current_format = self.formatCombo.currentText()
        if current_format == "--- 请选择接口格式 ---":
            current_format = ""

        config_data = {
            "id": self.config_data.get("id", str(uuid.uuid4())),
            "api_key": self.apiKeyEdit.text(),
            "base_url": self.baseUrlEdit.text(),
            "interface_format": current_format,
            "model_name": self.modelEdit.text(),
            "temperature": self.tempSlider.value() / 100.0,
            "max_tokens": self.tokensSlider.value(),
            "timeout": self.timeoutSlider.value(),
            "created_at": self.config_data.get(
                "created_at", datetime.datetime.now().isoformat()
            ),
            "updated_at": datetime.datetime.now().isoformat(),
        }
        return (self.nameEdit.text(), config_data)

    def test_config(self):
        """
        测试当前配置

        该方法在子线程中执行测试，通过信号机制确保 UI 更新在主线程中执行。
        解决 QObject::setParent 跨线程错误问题。

        参数:
            无

        返回值:
            无
        """
        current_format = self.formatCombo.currentText()
        if current_format == "--- 请选择接口格式 ---":
            current_format = ""

        test_llm_config(
            interface_format=current_format,
            api_key=self.apiKeyEdit.text(),
            base_url=self.baseUrlEdit.text(),
            model_name=self.modelEdit.text(),
            temperature=self.tempSlider.value() / 100.0,
            max_tokens=self.tokensSlider.value(),
            timeout=self.timeoutSlider.value(),
            log_func=lambda msg: self._testSignaler.info_signal.emit("测试结果", msg),
            handle_exception_func=lambda msg: self._testSignaler.error_signal.emit(
                "测试错误", msg
            ),
        )

    def _showTestInfo(self, title: str, message: str):
        """
        在主线程中显示测试信息

        参数:
            title: 信息标题
            message: 信息内容

        返回值:
            无
        """
        notify = get_global_notify()
        if notify:
            notify.info(title, message)

    def _showTestError(self, title: str, message: str):
        """
        在主线程中显示测试错误

        参数:
            title: 错误标题
            message: 错误内容

        返回值:
            无
        """
        notify = get_global_notify()
        if notify:
            notify.error(title, message)


class ModelSelectionDialog(MessageBoxBase):
    """
    模型选择对话框

    用于配置各生成阶段使用的大模型和 Embedding 模型。
    支持尺寸自适应和内容滚动。
    """

    def __init__(
        self,
        llm_configs,
        llm_configs_data,
        embedding_configs,
        choose_configs,
        parent=None,
    ):
        """
        初始化模型选择对话框

        Args:
            llm_configs: 可用的 LLM 模型配置列表
            llm_configs_data: 可用的 LLM 模型配置数据字典
            embedding_configs: 可用的 Embedding 模型配置列表
            choose_configs: 当前的模型选择配置
            parent: 父控件
        """
        super().__init__(parent)
        self.setWindowTitle("模型选择")

        self.titleLabel = SubtitleLabel("选择各阶段使用的模型", self)
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(15)

        self.model_selection_combos = {}
        self.composer_version_combos = {}
        self.llm_configs_data = llm_configs_data

        llm_label = StrongBodyLabel("LLM 模型", self._container)
        content_layout.addWidget(llm_label)

        model_selection_labels = {
            "architecture_llm": "生成架构所用大模型",
            "chapter_outline_llm": "生成大目录所用大模型",
            "prompt_draft_llm": "生成草稿所用大模型",
            "final_chapter_llm": "定稿章节所用大模型",
            "consistency_review_llm": "一致性审校所用大模型",
        }

        for key, label_text in model_selection_labels.items():
            label = BodyLabel(label_text, self._container)
            combo = ComboBox(self._container)
            combo.addItems(llm_configs)
            if key in choose_configs:
                combo.setCurrentText(choose_configs[key])
            elif llm_configs:
                combo.setCurrentIndex(0)
            content_layout.addWidget(label)
            content_layout.addWidget(combo)
            self.model_selection_combos[key] = combo

            composer_version_label = BodyLabel("Composer 版本", self._container)
            composer_version_combo = ComboBox(self._container)
            composer_version_combo.addItems(["mini", "standard", "pro"])

            version_key = f"{key}_composer_version"
            if version_key in choose_configs:
                composer_version_combo.setCurrentText(choose_configs[version_key])
            else:
                composer_version_combo.setCurrentIndex(1)

            composer_version_label.hide()
            composer_version_combo.hide()

            content_layout.addWidget(composer_version_label)
            content_layout.addWidget(composer_version_combo)
            self.composer_version_combos[key] = (
                composer_version_label,
                composer_version_combo,
            )

            combo.currentTextChanged.connect(
                lambda text, k=key: self.toggle_composer_version_selection(k, text)
            )

            current_model = combo.currentText()
            self.toggle_composer_version_selection(key, current_model)

        embedding_label = StrongBodyLabel("Embedding 模型", self._container)
        content_layout.addWidget(embedding_label)

        embedding_key = "embedding_model"
        embedding_label = BodyLabel("Embedding 模型", self._container)
        embedding_combo = ComboBox(self._container)
        embedding_combo.addItems(["无"] + embedding_configs)
        if embedding_key in choose_configs:
            if (
                choose_configs[embedding_key] == "无"
                or choose_configs[embedding_key] in embedding_configs
            ):
                embedding_combo.setCurrentText(choose_configs[embedding_key])
        elif embedding_configs:
            embedding_combo.setCurrentIndex(0)
        content_layout.addWidget(embedding_label)
        content_layout.addWidget(embedding_combo)
        self.model_selection_combos[embedding_key] = embedding_combo

        content_layout.addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.65,
            min_width=450,
            min_height=400,
        )
        sizer.apply_to_widget(self.widget, parent)

    def toggle_composer_version_selection(self, key, model_name):
        """
        根据选择的模型切换Composer版本选择的显示状态

        Args:
            key: 模型配置的键
            model_name: 选择的模型名称
        """
        # 从配置中获取模型的interface_format
        is_composer = False
        try:
            # 检查模型配置是否为Composer类型
            if model_name in self.llm_configs_data:
                model_config = self.llm_configs_data[model_name]
                if model_config.get("interface_format") == "Composer":
                    is_composer = True
            # 同时检查模型名称是否包含"Composer"作为后备
            elif "Composer" in model_name:
                is_composer = True
        except Exception:
            pass

        if is_composer:
            label, combo = self.composer_version_combos[key]
            label.show()
            combo.show()
        else:
            label, combo = self.composer_version_combos[key]
            label.hide()
            combo.hide()

    def get_selection(self):
        """
        获取用户的模型选择

        Returns:
            dict: 模型选择配置
        """
        selection = {}
        for key, combo in self.model_selection_combos.items():
            selection[key] = combo.currentText()

        # 保存Composer版本选择
        for key, (label, combo) in self.composer_version_combos.items():
            if label.isVisible():
                version_key = f"{key}_composer_version"
                selection[version_key] = combo.currentText()

        return selection
