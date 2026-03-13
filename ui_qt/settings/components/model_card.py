# -*- coding: utf-8 -*-
"""
AI Novel Generator - 模型卡片组件模块
====================================

本模块包含用于展示和管理模型配置的卡片组件：
- ModelCard: LLM 模型卡片组件
- EmbeddingCard: Embedding 模型卡片组件
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CardWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import StrongBodyLabel, ToolButton

from ...utils.styles import ThemeManager


class EmbeddingCard(CardWidget):
    """
    Embedding 模型卡片组件

    用于展示单个 Embedding 模型配置，支持点击编辑、删除和测试。
    """

    editRequested = pyqtSignal(str, dict)
    deleteRequested = pyqtSignal(str)
    testRequested = pyqtSignal(dict)

    def __init__(self, config_name, config_data, parent=None):
        """
        初始化 Embedding 模型卡片

        Args:
            config_name: 配置名称
            config_data: 配置数据字典
            parent: 父控件
        """
        super().__init__(parent)
        self.config_name = config_name
        self.config_data = config_data
        self.setMinimumSize(320, 120)
        self.setMaximumHeight(140)
        self.setCursor(Qt.PointingHandCursor)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 15, 20, 15)
        self.mainLayout.setSpacing(16)

        # 左侧信息区域
        self.infoWidget = QWidget(self)
        self.infoLayout = QVBoxLayout(self.infoWidget)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(6)

        self.titleLabel = StrongBodyLabel(config_name, self)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setMaximumHeight(40)

        interface_format = config_data.get("interface_format", "Unknown")
        model_name = config_data.get("model_name", "Unknown")
        self.infoLabel = BodyLabel(f"{interface_format} · {model_name}", self)
        from ...utils.styles import Styles

        self.infoLabel.setStyleSheet(Styles.HintText + " font-size: 12px;")

        # API Key 状态（仅未配置时显示警告）
        has_api_key = bool(config_data.get("api_key", ""))
        if not has_api_key:
            self.statusLabel = BodyLabel("⚠️ API Key 未配置", self)
            self.statusLabel.setStyleSheet(Styles.WarningText + " font-size: 11px;")
            self.infoLayout.addWidget(self.statusLabel)

        # Retrieval K 值
        retrieval_k = config_data.get("retrieval_k", 4)
        self.kLabel = BodyLabel(f"Top-K: {retrieval_k}", self)
        self.kLabel.setStyleSheet(Styles.SecondaryText + " font-size: 11px;")

        self.infoLayout.addWidget(self.titleLabel)
        self.infoLayout.addWidget(self.infoLabel)
        if not has_api_key:
            self.infoLayout.addWidget(self.statusLabel)
        self.infoLayout.addWidget(self.kLabel)
        self.infoLayout.addStretch()

        # 右侧按钮区域
        self.btnWidget = QWidget(self)
        self.btnLayout = QVBoxLayout(self.btnWidget)
        self.btnLayout.setContentsMargins(0, 0, 0, 0)
        self.btnLayout.setSpacing(8)

        self.editBtn = ToolButton(FIF.EDIT, self)
        self.editBtn.setFixedSize(32, 32)
        self.editBtn.setCursor(Qt.PointingHandCursor)
        self.editBtn.clicked.connect(self._on_edit_clicked)

        self.testBtn = ToolButton(FIF.SYNC, self)
        self.testBtn.setFixedSize(32, 32)
        self.testBtn.setCursor(Qt.PointingHandCursor)
        self.testBtn.clicked.connect(self._on_test_clicked)

        self.deleteBtn = ToolButton(FIF.DELETE, self)
        self.deleteBtn.setFixedSize(32, 32)
        self.deleteBtn.setCursor(Qt.PointingHandCursor)
        self.deleteBtn.clicked.connect(self._on_delete_clicked)

        self.btnLayout.addWidget(self.editBtn)
        self.btnLayout.addWidget(self.testBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addStretch()

        self.mainLayout.addWidget(self.infoWidget)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.btnWidget)

        self.clicked.connect(self._on_card_clicked)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow_color = QColor(
            ThemeManager.get_color(ThemeManager.Colors.SHADOW_PRIMARY)
        )
        shadow_color.setAlpha(20)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def _on_card_clicked(self):
        """卡片点击事件"""
        self.editRequested.emit(self.config_name, self.config_data)

    def _on_edit_clicked(self):
        """编辑按钮点击事件"""
        self.editRequested.emit(self.config_name, self.config_data)

    def _on_test_clicked(self):
        """测试按钮点击事件"""
        self.testRequested.emit(self.config_data)

    def _on_delete_clicked(self):
        """删除按钮点击事件"""
        self.deleteRequested.emit(self.config_name)


class ModelCard(CardWidget):
    """
    模型卡片组件

    用于展示单个LLM配置，支持点击编辑、删除和测试。
    """

    editRequested = pyqtSignal(str, dict)
    deleteRequested = pyqtSignal(str)
    testRequested = pyqtSignal(dict)

    def __init__(self, config_name, config_data, parent=None):
        """
        初始化模型卡片

        Args:
            config_name: 配置名称
            config_data: 配置数据字典
            parent: 父控件
        """
        super().__init__(parent)
        self.config_name = config_name
        self.config_data = config_data
        self.setMinimumSize(320, 120)
        self.setMaximumHeight(140)
        self.setCursor(Qt.PointingHandCursor)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 15, 20, 15)
        self.mainLayout.setSpacing(16)

        # 左侧信息区域
        self.infoWidget = QWidget(self)
        self.infoLayout = QVBoxLayout(self.infoWidget)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(6)

        self.titleLabel = StrongBodyLabel(config_name, self)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setMaximumHeight(40)

        interface_format = config_data.get("interface_format", "Unknown")
        model_name = config_data.get("model_name", "Unknown")
        self.infoLabel = BodyLabel(f"{interface_format} · {model_name}", self)
        from ...utils.styles import Styles

        self.infoLabel.setStyleSheet(Styles.HintText + " font-size: 12px;")

        # API Key 状态（仅未配置时显示警告）
        has_api_key = bool(config_data.get("api_key", ""))
        if not has_api_key:
            self.statusLabel = BodyLabel("⚠️ API Key 未配置", self)
            self.statusLabel.setStyleSheet(Styles.WarningText + " font-size: 11px;")
            self.infoLayout.addWidget(self.statusLabel)
        else:
            # API Key 已配置时，显示 Temperature 和 Max Tokens 信息
            temperature = config_data.get("temperature", 0.7)
            max_tokens = config_data.get("max_tokens", 8192)
            self.paramsLabel = BodyLabel(
                f"Temp: {temperature} · Max: {max_tokens}", self
            )
            self.paramsLabel.setStyleSheet(Styles.SecondaryText + " font-size: 11px;")
            self.infoLayout.addWidget(self.paramsLabel)

        self.infoLayout.addWidget(self.titleLabel)
        self.infoLayout.addWidget(self.infoLabel)
        if not has_api_key:
            self.infoLayout.addWidget(self.statusLabel)
        else:
            self.infoLayout.addWidget(self.paramsLabel)
        self.infoLayout.addStretch()

        # 右侧按钮区域
        self.btnWidget = QWidget(self)
        self.btnLayout = QVBoxLayout(self.btnWidget)
        self.btnLayout.setContentsMargins(0, 0, 0, 0)
        self.btnLayout.setSpacing(8)

        self.editBtn = ToolButton(FIF.EDIT, self)
        self.editBtn.setFixedSize(32, 32)
        self.editBtn.setCursor(Qt.PointingHandCursor)
        self.editBtn.clicked.connect(self._on_edit_clicked)

        self.testBtn = ToolButton(FIF.SYNC, self)
        self.testBtn.setFixedSize(32, 32)
        self.testBtn.setCursor(Qt.PointingHandCursor)
        self.testBtn.clicked.connect(self._on_test_clicked)

        self.deleteBtn = ToolButton(FIF.DELETE, self)
        self.deleteBtn.setFixedSize(32, 32)
        self.deleteBtn.setCursor(Qt.PointingHandCursor)
        self.deleteBtn.clicked.connect(self._on_delete_clicked)

        self.btnLayout.addWidget(self.editBtn)
        self.btnLayout.addWidget(self.testBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addStretch()

        self.mainLayout.addWidget(self.infoWidget)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.btnWidget)

        self.clicked.connect(self._on_card_clicked)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow_color = QColor(
            ThemeManager.get_color(ThemeManager.Colors.SHADOW_PRIMARY)
        )
        shadow_color.setAlpha(20)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def _on_card_clicked(self):
        """卡片点击事件"""
        self.editRequested.emit(self.config_name, self.config_data)

    def _on_edit_clicked(self):
        """编辑按钮点击事件"""
        self.editRequested.emit(self.config_name, self.config_data)

    def _on_test_clicked(self):
        """测试按钮点击事件"""
        self.testRequested.emit(self.config_data)

    def _on_delete_clicked(self):
        """删除按钮点击事件"""
        self.deleteRequested.emit(self.config_name)
