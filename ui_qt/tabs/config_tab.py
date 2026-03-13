# -*- coding: utf-8 -*-
"""
AI Novel Generator - 全局配置模块
====================================

本模块实现了应用程序的全局配置界面，负责：
- LLM（大语言模型）的配置管理
- Embedding（嵌入模型）的配置管理
- 各生成阶段的模型选择
- 网络代理设置

主要组件：
- ConfigTab: 配置主界面，整合所有子配置页
- BaseConfigTab: 配置页基类
- LLMConfigTab: LLM 配置页
- EmbeddingConfigTab: Embedding 配置页
- ModelSelectionTab: 模型选择页
- ProxyConfigTab: 代理配置页
"""

import datetime
import uuid

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    IndicatorPosition,
    LineEdit,
    Pivot,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    Slider,
    StrongBodyLabel,
    SwitchButton,
)
from qfluentwidgets import FluentIcon as FIF

from core.config_manager import (
    load_config,
    save_config,
    test_embedding_config,
    test_llm_config,
)
from ui_qt.settings.dialogs.other_dialogs import TestResultDialog
from ui_qt.utils.notification_manager import NotificationManager


class ConfigTab(QWidget):
    """
    全局配置主界面

    使用 Pivot 导航切换不同的配置子页面：
    - LLM 配置
    - Embedding 配置
    - 模型选择
    - 代理设置
    """

    def __init__(self, parent=None):
        """
        初始化配置主界面

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("configTab")

        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.pivot = Pivot(self)  # 顶部导航
        self.stackedWidget = QStackedWidget(self)  # 页面堆栈

        # 添加导航项
        self.pivot.addItem(routeKey="llm", text="LLM配置")
        self.pivot.addItem(routeKey="embedding", text="Embedding配置")
        self.pivot.addItem(routeKey="selection", text="模型选择")
        self.pivot.addItem(routeKey="proxy", text="代理设置")

        # 创建各配置子页面
        self.llmConfigTab = LLMConfigTab(self)
        self.embeddingConfigTab = EmbeddingConfigTab(self)
        self.modelSelectionTab = ModelSelectionTab(self)
        self.proxyConfigTab = ProxyConfigTab(self)

        # 将子页面添加到堆栈
        self.stackedWidget.addWidget(self.llmConfigTab)
        self.stackedWidget.addWidget(self.embeddingConfigTab)
        self.stackedWidget.addWidget(self.modelSelectionTab)
        self.stackedWidget.addWidget(self.proxyConfigTab)

        # 添加到主布局
        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)

        # 连接导航切换信号
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentIndex(
                ["llm", "embedding", "selection", "proxy"].index(k)
            )
        )

        # 默认显示 LLM 配置页
        self.stackedWidget.setCurrentIndex(0)


class BaseConfigTab(ScrollArea):
    """
    配置页基类

    提供配置页面的通用功能：
    - 加载/保存配置文件
    - 显示信息/错误提示
    - 统一的样式设置
    """

    def __init__(self, parent=None):
        """
        初始化配置基类

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.view = QWidget(self)
        self.view.setObjectName("configView")

        self.setStyleSheet(
            "BaseConfigTab { background-color: transparent; border: none; }"
        )
        self.viewport().setStyleSheet("background-color: transparent;")
        self.view.setStyleSheet("QWidget#configView { background-color: transparent; }")

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(30, 20, 30, 20)

        self.config_file = "config.json"
        self.loaded_config = load_config(self.config_file) or {}

        self._notify = NotificationManager(self)

    def show_info(self, title, content):
        """
        显示成功提示信息

        Args:
            title: 提示标题
            content: 提示内容
        """
        self._notify.success(title, content)

    def show_error(self, title, content):
        """
        显示错误提示信息

        Args:
            title: 错误标题
            content: 错误内容
        """
        self._notify.error(title, content)

    def show_warning(self, title, content):
        """
        显示警告提示信息

        Args:
            title: 警告标题
            content: 警告内容
        """
        self._notify.warning(title, content)

    def save_config_to_file(self):
        """
        将配置保存到文件

        Returns:
            bool: 保存是否成功
        """
        try:
            save_config(self.loaded_config, self.config_file)
            return True
        except Exception as e:
            self.show_error("保存失败", str(e))
            return False


class LLMConfigTab(BaseConfigTab):
    """
    LLM（大语言模型）配置页

    提供以下功能：
    - 多配置管理（新增、重命名、删除）
    - API Key、Base URL 配置
    - 接口格式选择（OpenAI、Azure、Ollama 等）
    - Temperature、Max Tokens、Timeout 等参数调节
    - 配置测试功能
    """

    def __init__(self, parent=None):
        """
        初始化 LLM 配置页

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 配置选择卡片
        self.selectionCard = CardWidget(self.view)
        self.selectionLayout = QVBoxLayout(self.selectionCard)
        self.selectionHeader = StrongBodyLabel("配置管理", self.selectionCard)
        self.selectionCombo = ComboBox(self.selectionCard)

        # 操作按钮
        self.btnLayout = QHBoxLayout()
        self.addBtn = PushButton(FIF.ADD, "新增", self.selectionCard)
        self.renameBtn = PushButton(FIF.EDIT, "重命名", self.selectionCard)
        self.deleteBtn = PushButton(FIF.DELETE, "删除", self.selectionCard)
        self.saveBtn = PrimaryPushButton(FIF.SAVE, "保存", self.selectionCard)

        self.btnLayout.addWidget(self.addBtn)
        self.btnLayout.addWidget(self.renameBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addWidget(self.saveBtn)

        self.selectionLayout.addWidget(self.selectionHeader)
        self.selectionLayout.addWidget(self.selectionCombo)
        self.selectionLayout.addLayout(self.btnLayout)

        self.vBoxLayout.addWidget(self.selectionCard)

        # 配置表单卡片
        self.formCard = CardWidget(self.view)
        self.formLayout = QVBoxLayout(self.formCard)

        # API Key
        self.apiKeyLabel = BodyLabel("API Key", self.formCard)
        self.apiKeyEdit = LineEdit(self.formCard)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)  # 密码模式显示
        self.formLayout.addWidget(self.apiKeyLabel)
        self.formLayout.addWidget(self.apiKeyEdit)

        # Base URL
        self.baseUrlLabel = BodyLabel("Base URL", self.formCard)
        self.baseUrlEdit = LineEdit(self.formCard)
        self.formLayout.addWidget(self.baseUrlLabel)
        self.formLayout.addWidget(self.baseUrlEdit)

        # 接口格式
        self.formatLabel = BodyLabel("接口格式", self.formCard)
        self.formatCombo = ComboBox(self.formCard)
        self.formatCombo.addItems(
            ["OpenAI", "Azure OpenAI", "Ollama", "DeepSeek", "Gemini", "ML Studio"]
        )
        self.formLayout.addWidget(self.formatLabel)
        self.formLayout.addWidget(self.formatCombo)

        # 模型名称
        self.modelLabel = BodyLabel("模型名称", self.formCard)
        self.modelEdit = LineEdit(self.formCard)
        self.formLayout.addWidget(self.modelLabel)
        self.formLayout.addWidget(self.modelEdit)

        # Temperature（温度参数，控制随机性）
        self.tempLabel = BodyLabel("Temperature: 0.7", self.formCard)
        self.tempSlider = Slider(Qt.Horizontal, self.formCard)
        self.tempSlider.setRange(0, 200)  # 0.00 - 2.00
        self.tempSlider.setValue(70)  # 默认 0.7
        self.formLayout.addWidget(self.tempLabel)
        self.formLayout.addWidget(self.tempSlider)

        # Max Tokens（最大生成 token 数）
        self.tokensLabel = BodyLabel("Max Tokens: 8192", self.formCard)
        self.tokensSlider = Slider(Qt.Horizontal, self.formCard)
        self.tokensSlider.setRange(0, 102400)
        self.tokensSlider.setValue(8192)
        self.formLayout.addWidget(self.tokensLabel)
        self.formLayout.addWidget(self.tokensSlider)

        # Timeout（超时时间，秒）
        self.timeoutLabel = BodyLabel("Timeout: 600s", self.formCard)
        self.timeoutSlider = Slider(Qt.Horizontal, self.formCard)
        self.timeoutSlider.setRange(0, 3600)
        self.timeoutSlider.setValue(600)
        self.formLayout.addWidget(self.timeoutLabel)
        self.formLayout.addWidget(self.timeoutSlider)

        # 测试配置按钮
        self.testBtn = PushButton("测试配置", self.formCard)
        self.formLayout.addWidget(self.testBtn)

        self.vBoxLayout.addWidget(self.formCard)

        # 连接信号
        self.selectionCombo.currentTextChanged.connect(self.on_config_selected)
        self.addBtn.clicked.connect(self.add_config)
        self.renameBtn.clicked.connect(self.rename_config)
        self.deleteBtn.clicked.connect(self.delete_config)
        self.saveBtn.clicked.connect(self.save_current_config)
        self.testBtn.clicked.connect(self.test_config)

        # 滑块值变化时更新标签显示
        self.tempSlider.valueChanged.connect(
            lambda v: self.tempLabel.setText(f"Temperature: {v/100:.2f}")
        )
        self.tokensSlider.valueChanged.connect(
            lambda v: self.tokensLabel.setText(f"Max Tokens: {v}")
        )
        self.timeoutSlider.valueChanged.connect(
            lambda v: self.timeoutLabel.setText(f"Timeout: {v}s")
        )

        # 刷新配置列表
        self.refresh_configs()

    def refresh_configs(self):
        """
        刷新配置列表

        从配置文件读取所有 LLM 配置并更新下拉框。
        """
        configs = self.loaded_config.get("llm_configs", {})
        current = self.selectionCombo.currentText()
        self.selectionCombo.clear()
        self.selectionCombo.addItems(list(configs.keys()))
        if current in configs:
            self.selectionCombo.setCurrentText(current)
        elif configs:
            self.selectionCombo.setCurrentIndex(0)

    def add_default_config(self):
        """
        添加默认配置

        创建一个名为"默认配置"的 LLM 配置，使用 OpenAI 格式。
        """
        if "llm_configs" not in self.loaded_config:
            self.loaded_config["llm_configs"] = {}
        self.loaded_config["llm_configs"]["默认配置"] = {
            "id": str(uuid.uuid4()),
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 8192,
            "timeout": 600,
            "interface_format": "OpenAI",
            "created_at": datetime.datetime.now().isoformat(),
        }

    def on_config_selected(self, text):
        """
        配置选择变化事件

        当用户在下拉框中选择不同配置时，更新表单中的值。

        Args:
            text: 选中的配置名称
        """
        if not text:
            return
        config = self.loaded_config.get("llm_configs", {}).get(text, {})
        self.apiKeyEdit.setText(config.get("api_key", ""))
        self.baseUrlEdit.setText(config.get("base_url", ""))
        self.formatCombo.setCurrentText(config.get("interface_format", "OpenAI"))
        self.modelEdit.setText(config.get("model_name", ""))

        # 更新 Temperature 滑块
        temp = float(config.get("temperature", 0.7))
        self.tempSlider.setValue(int(temp * 100))

        # 更新 Max Tokens 滑块
        tokens = int(config.get("max_tokens", 8192))
        self.tokensSlider.setValue(tokens)

        # 更新 Timeout 滑块
        timeout = int(config.get("timeout", 600))
        self.timeoutSlider.setValue(timeout)

    def add_config(self):
        """
        新增配置

        弹出对话框让用户输入新配置名称，然后创建一个空白配置。
        """
        from PyQt5.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "新增配置", "配置名称:")
        if ok and text:
            if text in self.loaded_config.get("llm_configs", {}):
                self.show_error("错误", "配置名称已存在")
                return

            # 创建新配置
            self.loaded_config["llm_configs"][text] = {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "",
                "model_name": "",
                "temperature": 0.7,
                "max_tokens": 8192,
                "timeout": 600,
                "interface_format": "OpenAI",
                "created_at": datetime.datetime.now().isoformat(),
            }
            self.refresh_configs()
            self.selectionCombo.setCurrentText(text)
            self.show_info("成功", f"已添加配置 {text}")

    def rename_config(self):
        """
        重命名当前配置
        """
        old_name = self.selectionCombo.currentText()
        from PyQt5.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(
            self, "重命名配置", f"原名称: {old_name}\n新名称:"
        )
        if ok and text and text != old_name:
            if text in self.loaded_config.get("llm_configs", {}):
                self.show_error("错误", "配置名称已存在")
                return

            # 重命名字典键
            self.loaded_config["llm_configs"][text] = self.loaded_config[
                "llm_configs"
            ].pop(old_name)
            self.refresh_configs()
            self.selectionCombo.setCurrentText(text)
            self.show_info("成功", "重命名成功")

    def delete_config(self):
        """
        删除当前配置
        """
        name = self.selectionCombo.currentText()
        if not name:
            return

        del self.loaded_config["llm_configs"][name]
        self.refresh_configs()
        self.save_config_to_file()
        self.show_info("成功", f"已删除配置 {name}")

    def save_current_config(self):
        """
        保存当前配置

        将表单中的值保存到当前选中的配置中。
        """
        name = self.selectionCombo.currentText()
        if not name:
            return

        config = self.loaded_config["llm_configs"][name]
        config.update(
            {
                "api_key": self.apiKeyEdit.text(),
                "base_url": self.baseUrlEdit.text(),
                "interface_format": self.formatCombo.currentText(),
                "model_name": self.modelEdit.text(),
                "temperature": self.tempSlider.value() / 100.0,
                "max_tokens": self.tokensSlider.value(),
                "timeout": self.timeoutSlider.value(),
                "updated_at": datetime.datetime.now().isoformat(),
            }
        )

        if self.save_config_to_file():
            self.show_info("成功", "配置已保存")

    def test_config(self):
        """
        测试当前配置

        调用 test_llm_config 函数测试配置是否有效。
        使用 TestResultDialog 显示测试结果，失败时不自动关闭并支持复制。
        """
        test_messages = []

        def log_func(msg):
            test_messages.append(msg)

        def handle_exception(msg):
            test_messages.append(f"错误: {msg}")
            full_content = "\n".join(test_messages)
            dialog = TestResultDialog(
                title="LLM配置测试失败",
                content=full_content,
                is_success=False,
                parent=self.window(),
            )
            dialog.exec()

        def on_success():
            full_content = "\n".join(test_messages)
            dialog = TestResultDialog(
                title="LLM配置测试成功",
                content=full_content,
                is_success=True,
                parent=self.window(),
            )
            dialog.exec()

        test_llm_config(
            interface_format=self.formatCombo.currentText(),
            api_key=self.apiKeyEdit.text(),
            base_url=self.baseUrlEdit.text(),
            model_name=self.modelEdit.text(),
            temperature=self.tempSlider.value() / 100.0,
            max_tokens=self.tokensSlider.value(),
            timeout=self.timeoutSlider.value(),
            log_func=log_func,
            handle_exception_func=handle_exception,
            success_callback=on_success,
        )


class EmbeddingConfigTab(BaseConfigTab):
    """
    Embedding（嵌入模型）配置页

    配置用于向量化知识库的 Embedding 模型。
    """

    def __init__(self, parent=None):
        """
        初始化 Embedding 配置页

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 配置选择卡片
        self.selectionCard = CardWidget(self.view)
        self.selectionLayout = QVBoxLayout(self.selectionCard)
        self.selectionHeader = StrongBodyLabel("配置管理", self.selectionCard)
        self.selectionCombo = ComboBox(self.selectionCard)

        # 操作按钮
        self.btnLayout = QHBoxLayout()
        self.addBtn = PushButton(FIF.ADD, "新增", self.selectionCard)
        self.renameBtn = PushButton(FIF.EDIT, "重命名", self.selectionCard)
        self.deleteBtn = PushButton(FIF.DELETE, "删除", self.selectionCard)
        self.saveBtn = PrimaryPushButton(FIF.SAVE, "保存", self.selectionCard)

        self.btnLayout.addWidget(self.addBtn)
        self.btnLayout.addWidget(self.renameBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addWidget(self.saveBtn)

        self.selectionLayout.addWidget(self.selectionHeader)
        self.selectionLayout.addWidget(self.selectionCombo)
        self.selectionLayout.addLayout(self.btnLayout)

        self.vBoxLayout.addWidget(self.selectionCard)

        # 配置表单卡片
        self.formCard = CardWidget(self.view)
        self.formLayout = QVBoxLayout(self.formCard)

        # 接口格式
        self.formatLabel = BodyLabel("Embedding 接口格式", self.formCard)
        self.formatCombo = ComboBox(self.formCard)
        self.formatCombo.addItems(
            [
                "DeepSeek",
                "OpenAI",
                "Azure OpenAI",
                "Gemini",
                "Ollama",
                "ML Studio",
                "SiliconFlow",
            ]
        )
        self.formLayout.addWidget(self.formatLabel)
        self.formLayout.addWidget(self.formatCombo)

        # API Key
        self.apiKeyLabel = BodyLabel("API Key", self.formCard)
        self.apiKeyEdit = LineEdit(self.formCard)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)
        self.formLayout.addWidget(self.apiKeyLabel)
        self.formLayout.addWidget(self.apiKeyEdit)

        # Base URL
        self.baseUrlLabel = BodyLabel("Base URL", self.formCard)
        self.baseUrlEdit = LineEdit(self.formCard)
        self.formLayout.addWidget(self.baseUrlLabel)
        self.formLayout.addWidget(self.baseUrlEdit)

        # Model Name
        self.modelLabel = BodyLabel("Model Name", self.formCard)
        self.modelEdit = LineEdit(self.formCard)
        self.formLayout.addWidget(self.modelLabel)
        self.formLayout.addWidget(self.modelEdit)

        # Retrieval Top-K（检索时返回的相关文档数量）
        self.kLabel = BodyLabel("Retrieval Top-K", self.formCard)
        self.kEdit = LineEdit(self.formCard)
        self.formLayout.addWidget(self.kLabel)
        self.formLayout.addWidget(self.kEdit)

        # 测试按钮
        self.testBtn = PushButton("测试配置", self.formCard)
        self.formLayout.addWidget(self.testBtn)

        self.vBoxLayout.addWidget(self.formCard)

        # 连接信号
        self.selectionCombo.currentTextChanged.connect(self.on_config_selected)
        self.addBtn.clicked.connect(self.add_config)
        self.renameBtn.clicked.connect(self.rename_config)
        self.deleteBtn.clicked.connect(self.delete_config)
        self.saveBtn.clicked.connect(self.save_current_config)
        self.formatCombo.currentTextChanged.connect(self.on_format_changed)
        self.testBtn.clicked.connect(self.test_config)

        # 刷新配置列表
        self.refresh_configs()

    def refresh_configs(self):
        """
        刷新配置列表

        从配置文件读取所有 Embedding 配置并更新下拉框。
        """
        configs = self.loaded_config.get("embedding_configs", {})
        current = self.selectionCombo.currentText()
        self.selectionCombo.clear()
        self.selectionCombo.addItems(list(configs.keys()))
        if current in configs:
            self.selectionCombo.setCurrentText(current)
        elif configs:
            self.selectionCombo.setCurrentIndex(0)

    def on_config_selected(self, text):
        """
        配置选择变化事件

        当用户在下拉框中选择不同配置时，更新表单中的值。

        Args:
            text: 选中的配置名称
        """
        if not text:
            return
        config = self.loaded_config.get("embedding_configs", {}).get(text, {})
        self.formatCombo.setCurrentText(config.get("interface_format", "OpenAI"))
        self.apiKeyEdit.setText(config.get("api_key", ""))
        self.baseUrlEdit.setText(config.get("base_url", ""))
        self.modelEdit.setText(config.get("model_name", ""))
        self.kEdit.setText(str(config.get("retrieval_k", 4)))

    def add_config(self):
        """
        新增配置

        弹出对话框让用户输入新配置名称，然后创建一个空白配置。
        """
        from PyQt5.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "新增配置", "配置名称:")
        if ok and text:
            if text in self.loaded_config.get("embedding_configs", {}):
                self.show_error("错误", "配置名称已存在")
                return

            if "embedding_configs" not in self.loaded_config:
                self.loaded_config["embedding_configs"] = {}

            self.loaded_config["embedding_configs"][text] = {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "",
                "model_name": "",
                "retrieval_k": 4,
                "interface_format": "OpenAI",
                "created_at": datetime.datetime.now().isoformat(),
            }
            self.refresh_configs()
            self.selectionCombo.setCurrentText(text)
            self.show_info("成功", f"已添加配置 {text}")

    def rename_config(self):
        """
        重命名当前配置
        """
        old_name = self.selectionCombo.currentText()
        from PyQt5.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(
            self, "重命名配置", f"原名称: {old_name}\n新名称:"
        )
        if ok and text and text != old_name:
            if text in self.loaded_config.get("embedding_configs", {}):
                self.show_error("错误", "配置名称已存在")
                return

            # 重命名字典键
            self.loaded_config["embedding_configs"][text] = self.loaded_config[
                "embedding_configs"
            ].pop(old_name)
            self.refresh_configs()
            self.selectionCombo.setCurrentText(text)
            self.show_info("成功", "重命名成功")

    def delete_config(self):
        """
        删除当前配置
        """
        name = self.selectionCombo.currentText()
        if not name:
            return

        del self.loaded_config["embedding_configs"][name]

        # 如果删除后没有配置了，创建一个默认的
        if not self.loaded_config.get("embedding_configs"):
            self.loaded_config["embedding_configs"]["默认配置"] = {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "text-embedding-ada-002",
                "retrieval_k": 4,
                "interface_format": "OpenAI",
                "created_at": datetime.datetime.now().isoformat(),
            }

        self.refresh_configs()
        self.save_config_to_file()
        self.show_info("成功", f"已删除配置 {name}")

    def save_current_config(self):
        """
        保存当前配置

        将表单中的值保存到当前选中的配置中。
        """
        name = self.selectionCombo.currentText()
        if not name:
            return

        config = self.loaded_config["embedding_configs"][name]
        config.update(
            {
                "interface_format": self.formatCombo.currentText(),
                "api_key": self.apiKeyEdit.text(),
                "base_url": self.baseUrlEdit.text(),
                "model_name": self.modelEdit.text(),
                "retrieval_k": int(self.kEdit.text() or 4),
                "updated_at": datetime.datetime.now().isoformat(),
            }
        )
        self.loaded_config["last_embedding_interface_format"] = name

        if self.save_config_to_file():
            self.show_info("成功", "配置已保存")

    def on_format_changed(self, text):
        """
        接口格式变化事件

        当用户选择不同的接口格式时，自动填充相应的默认值。

        Args:
            text: 选中的接口格式
        """
        configs = self.loaded_config.get("embedding_configs", {})
        current_name = self.selectionCombo.currentText()
        if current_name and current_name in configs:
            conf = configs[current_name]
            if conf.get("interface_format") == text:
                return

        # 为特定格式设置默认值
        if text == "Ollama":
            self.baseUrlEdit.setText("http://localhost:11434/api")
        elif text == "OpenAI":
            self.baseUrlEdit.setText("https://api.openai.com/v1")
            self.modelEdit.setText("text-embedding-ada-002")

    def test_config(self):
        """
        测试 Embedding 配置
        使用 TestResultDialog 显示测试结果，失败时不自动关闭并支持复制。
        """
        test_messages = []

        def log_func(msg):
            test_messages.append(msg)

        def handle_exception(msg):
            test_messages.append(f"错误: {msg}")
            full_content = "\n".join(test_messages)
            dialog = TestResultDialog(
                title="Embedding配置测试失败",
                content=full_content,
                is_success=False,
                parent=self.window(),
            )
            dialog.exec()

        def on_success():
            full_content = "\n".join(test_messages)
            dialog = TestResultDialog(
                title="Embedding配置测试成功",
                content=full_content,
                is_success=True,
                parent=self.window(),
            )
            dialog.exec()

        test_embedding_config(
            api_key=self.apiKeyEdit.text(),
            base_url=self.baseUrlEdit.text(),
            interface_format=self.formatCombo.currentText(),
            model_name=self.modelEdit.text(),
            log_func=log_func,
            handle_exception_func=handle_exception,
            success_callback=on_success,
        )


class ModelSelectionTab(BaseConfigTab):
    """
    模型选择配置页

    为小说生成的不同阶段选择不同的 LLM 配置：
    - 生成架构所用大模型
    - 生成大目录所用大模型
    - 生成草稿所用大模型
    - 定稿章节所用大模型
    - 一致性审校所用大模型
    - Embedding模型
    """

    def __init__(self, parent=None):
        """
        初始化模型选择配置页

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        self.card = CardWidget(self.view)
        self.layout = QVBoxLayout(self.card)

        self.combos = {}
        self.embedding_combo = None
        # 各阶段对应的标签
        labels = {
            "architecture_llm": "生成架构所用大模型",
            "chapter_outline_llm": "生成大目录所用大模型",
            "prompt_draft_llm": "生成草稿所用大模型",
            "final_chapter_llm": "定稿章节所用大模型",
            "consistency_review_llm": "一致性审校所用大模型",
        }

        choose_configs = self.loaded_config.get("choose_configs", {})

        # 为每个阶段创建下拉框
        for key, label_text in labels.items():
            label = BodyLabel(label_text, self.card)
            combo = ComboBox(self.card)
            self.layout.addWidget(label)
            self.layout.addWidget(combo)
            self.combos[key] = combo

            # 恢复之前的选择
            if key in choose_configs:
                combo.setCurrentText(choose_configs[key])

        # 添加Embedding模型选择
        embeddingLabel = BodyLabel("Embedding模型", self.card)
        self.embedding_combo = ComboBox(self.card)
        self.layout.addWidget(embeddingLabel)
        self.layout.addWidget(self.embedding_combo)

        # 恢复Embedding模型选择
        if "embedding_config" in choose_configs:
            self.embedding_combo.setCurrentText(choose_configs["embedding_config"])

        # 刷新和保存按钮
        self.refreshBtn = PushButton(FIF.SYNC, "刷新选项", self.card)
        self.saveBtn = PrimaryPushButton(FIF.SAVE, "保存配置", self.card)

        self.layout.addWidget(self.refreshBtn)
        self.layout.addWidget(self.saveBtn)

        self.vBoxLayout.addWidget(self.card)

        # 连接信号
        self.refreshBtn.clicked.connect(self.refresh_options)
        self.saveBtn.clicked.connect(self.save_selection)

        # 刷新选项列表
        self.refresh_options()

    def refresh_options(self):
        """
        刷新模型选项列表

        从配置文件读取所有可用的 LLM 和 Embedding 配置，更新各下拉框。
        """
        configs = list(self.loaded_config.get("llm_configs", {}).keys())
        for combo in self.combos.values():
            current = combo.currentText()
            combo.clear()
            combo.addItems(configs)
            if current in configs:
                combo.setCurrentText(current)
            elif configs:
                combo.setCurrentIndex(0)

        # 刷新Embedding配置选项
        if self.embedding_combo:
            embedding_configs = ["无"] + list(
                self.loaded_config.get("embedding_configs", {}).keys()
            )
            current_embedding = self.embedding_combo.currentText()
            self.embedding_combo.clear()
            self.embedding_combo.addItems(embedding_configs)
            if current_embedding in embedding_configs:
                self.embedding_combo.setCurrentText(current_embedding)
            elif embedding_configs:
                self.embedding_combo.setCurrentIndex(0)

    def save_selection(self):
        """
        保存模型选择配置
        """
        if "choose_configs" not in self.loaded_config:
            self.loaded_config["choose_configs"] = {}

        for key, combo in self.combos.items():
            self.loaded_config["choose_configs"][key] = combo.currentText()

        # 保存Embedding配置选择
        if self.embedding_combo:
            self.loaded_config["choose_configs"][
                "embedding_config"
            ] = self.embedding_combo.currentText()

        if self.save_config_to_file():
            self.show_info("成功", "模型选择配置已保存")


class ProxyConfigTab(BaseConfigTab):
    """
    代理配置页

    配置网络代理，用于访问 API。
    """

    def __init__(self, parent=None):
        """
        初始化代理配置页

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        self.card = CardWidget(self.view)
        self.layout = QVBoxLayout(self.card)

        proxy_setting = self.loaded_config.get("proxy_setting", {})

        # 启用代理开关
        self.enableSwitch = SwitchButton("启用代理", self.card, IndicatorPosition.RIGHT)
        self.enableSwitch.setChecked(proxy_setting.get("enabled", False))
        self.layout.addWidget(self.enableSwitch)

        # 代理地址
        self.addrLabel = BodyLabel("地址", self.card)
        self.addrEdit = LineEdit(self.card)
        self.addrEdit.setText(proxy_setting.get("proxy_url", "127.0.0.1"))
        self.layout.addWidget(self.addrLabel)
        self.layout.addWidget(self.addrEdit)

        # 代理端口
        self.portLabel = BodyLabel("端口", self.card)
        self.portEdit = LineEdit(self.card)
        self.portEdit.setText(proxy_setting.get("proxy_port", "10809"))
        self.layout.addWidget(self.portLabel)
        self.layout.addWidget(self.portEdit)

        # 保存按钮
        self.saveBtn = PrimaryPushButton(FIF.SAVE, "保存代理设置", self.card)
        self.layout.addWidget(self.saveBtn)

        self.vBoxLayout.addWidget(self.card)

        # 连接信号
        self.saveBtn.clicked.connect(self.save_proxy)

    def save_proxy(self):
        """
        保存代理设置

        如果启用了代理，还会设置环境变量 HTTP_PROXY 和 HTTPS_PROXY。
        """
        import os

        if "proxy_setting" not in self.loaded_config:
            self.loaded_config["proxy_setting"] = {}

        enabled = self.enableSwitch.isChecked()
        url = self.addrEdit.text()
        port = self.portEdit.text()

        self.loaded_config["proxy_setting"]["enabled"] = enabled
        self.loaded_config["proxy_setting"]["proxy_url"] = url
        self.loaded_config["proxy_setting"]["proxy_port"] = port

        if self.save_config_to_file():
            self.show_info("成功", "代理配置已保存")

        # 设置或取消环境变量
        if enabled:
            os.environ["HTTP_PROXY"] = f"http://{url}:{port}"
            os.environ["HTTPS_PROXY"] = f"http://{url}:{port}"
        else:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
