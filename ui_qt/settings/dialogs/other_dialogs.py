# -*- coding: utf-8 -*-
"""
AI Novel Generator - 其他对话框模块
==============================

本模块包含其他对话框组件：
- ChangeDirectoryDialog: 更改目录对话框
- UpdateDialog: 更新对话框
- UpdateCheckThread: 更新检查线程
- ModelTypeDialog: 模型类型选择对话框
- ComposerModelDialog: Composer模型选择对话框
"""

import os
import re
import sys

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from markdown_it import MarkdownIt
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    IndicatorPosition,
    LineEdit,
    MessageBoxBase,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    SwitchButton,
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

import requests

from ...utils.dialog_sizer import DialogSizer, ScrollableContainer
from ...utils.styles import Styles


class UpdateCheckThread(QThread):
    """
    检查更新线程类

    用于在后台线程中执行 GitHub API 调用，避免阻塞 UI。
    """

    update_available = pyqtSignal(dict)
    update_not_available = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self):
        """
        初始化检查更新线程
        """
        super().__init__()

    def run(self):
        """
        执行更新检查

        调用 GitHub API 获取最新版本信息，通过信号返回结果。
        """
        try:
            response = requests.get(GITHUB_API_RELEASES_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            # 检查是否有更新
            latest_version = release_data.get("tag_name", "").lstrip("v")
            if self._compare_versions(latest_version, __version__) > 0:
                self.update_available.emit(release_data)
            else:
                self.update_not_available.emit()

        except requests.RequestException as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _compare_versions(self, v1, v2):
        """
        比较两个版本号

        Args:
            v1: 第一个版本号字符串
            v2: 第二个版本号字符串

        Returns:
            int: 如果 v1 > v2 返回 1，v1 < v2 返回 -1，相等返回 0
        """

        def normalize(v):
            return [int(x) for x in re.findall(r"\d+", v)]

        v1_parts = normalize(v1)
        v2_parts = normalize(v2)

        # 补零对齐
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))

        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0


class UpdateDialog(MessageBoxBase):
    """
    更新对话框

    用于显示发现新版本时的更新信息。
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, release_data, parent=None):
        """
        初始化更新对话框

        Args:
            release_data: GitHub API 返回的 release 数据字典
            parent: 父控件
        """
        super().__init__(parent)
        self.release_data = release_data

        self.titleLabel = SubtitleLabel("发现新版本", self)
        self.viewLayout.addWidget(self.titleLabel)

        version_tag = release_data.get("tag_name", "")
        version_label = BodyLabel(f"最新版本: {version_tag}", self)
        self.viewLayout.addWidget(version_label)

        note_label = BodyLabel("更新内容:", self)
        self.viewLayout.addWidget(note_label)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)

        self.note_browser = QTextBrowser(self._container)
        self.note_browser.setOpenExternalLinks(True)
        self.note_browser.setMinimumHeight(250)

        body = release_data.get("body", "")
        html_content = self._markdown_to_html(body)
        self.note_browser.setHtml(html_content)

        self._container.content_layout().addWidget(self.note_browser)
        self._container.content_layout().addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("前往更新")
        self.cancelButton.setText("稍后")

        sizer = DialogSizer(
            width_ratio=0.50,
            height_ratio=0.55,
            min_width=500,
            min_height=400,
        )
        sizer.apply_to_widget(self.widget, parent)

    def _markdown_to_html(self, markdown_text):
        """
        将 Markdown 文本转换为 HTML

        Args:
            markdown_text: Markdown 格式的文本

        Returns:
            str: HTML 格式的文本
        """
        md = MarkdownIt()
        html = md.render(markdown_text)
        return html


class ChangeDirectoryDialog(MessageBoxBase):
    """
    更改目录对话框

    用于更改小说存储目录，支持迁移现有数据和删除原目录。
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, current_dir, parent=None):
        """
        初始化更改目录对话框

        Args:
            current_dir: 当前目录路径
            parent: 父控件
        """
        super().__init__(parent)
        self.current_dir = current_dir
        self.new_dir = current_dir
        self.migrate_data = True
        self.delete_old_dir = False

        self.titleLabel = SubtitleLabel("更改小说目录", self)
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(15)

        currentLabel = BodyLabel("当前目录:", self._container)
        currentPathLabel = QTextEdit(self._container)
        currentPathLabel.setText(current_dir)
        currentPathLabel.setReadOnly(True)
        currentPathLabel.setMaximumHeight(60)
        currentPathLabel.setStyleSheet(
            "color: gray; background-color: transparent; border: none; padding: 0;"
        )
        content_layout.addWidget(currentLabel)
        content_layout.addWidget(currentPathLabel)

        newDirLayout = QHBoxLayout()
        newDirLabel = BodyLabel("新目录:", self._container)
        self.newDirEdit = LineEdit(self._container)
        self.newDirEdit.setText(current_dir)
        self.newDirEdit.setReadOnly(True)
        self.browseBtn = PushButton(FIF.FOLDER, "浏览", self._container)
        newDirLayout.addWidget(newDirLabel)
        newDirLayout.addWidget(self.newDirEdit)
        newDirLayout.addWidget(self.browseBtn)
        content_layout.addLayout(newDirLayout)

        self.advancedOptionsContainer = QWidget(self._container)
        self.advancedOptionsLayout = QVBoxLayout(self.advancedOptionsContainer)
        self.advancedOptionsLayout.setContentsMargins(0, 10, 0, 0)

        switchesLayout = QHBoxLayout()

        migrateLayout = QHBoxLayout()
        migrateLabel = BodyLabel("迁移现有小说", self.advancedOptionsContainer)
        self.migrateSwitch = SwitchButton(
            "", self.advancedOptionsContainer, IndicatorPosition.RIGHT
        )
        self.migrateSwitch.setChecked(True)
        migrateLayout.addWidget(migrateLabel)
        migrateLayout.addWidget(self.migrateSwitch)
        switchesLayout.addLayout(migrateLayout)

        switchesLayout.addSpacing(30)

        deleteLayout = QHBoxLayout()
        deleteLabel = BodyLabel("删除原目录", self.advancedOptionsContainer)
        self.deleteOldDirSwitch = SwitchButton(
            "", self.advancedOptionsContainer, IndicatorPosition.RIGHT
        )
        self.deleteOldDirSwitch.setChecked(False)
        deleteLayout.addWidget(deleteLabel)
        deleteLayout.addWidget(self.deleteOldDirSwitch)
        switchesLayout.addLayout(deleteLayout)

        switchesLayout.addStretch()
        self.advancedOptionsLayout.addLayout(switchesLayout)

        self.warningLabel = CaptionLabel("", self.advancedOptionsContainer)
        self.warningLabel.setStyleSheet(Styles.WarningText)
        self.warningLabel.setWordWrap(True)
        self.warningLabel.hide()
        self.advancedOptionsLayout.addWidget(self.warningLabel)

        self.advancedOptionsContainer.hide()
        content_layout.addWidget(self.advancedOptionsContainer)

        content_layout.addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.45,
            height_ratio=0.45,
            min_width=450,
            min_height=300,
        )
        sizer.apply_to_widget(self.widget, parent)

        self.browseBtn.clicked.connect(self.browse_directory)
        self.newDirEdit.textChanged.connect(self.on_dir_changed)
        self.deleteOldDirSwitch.checkedChanged.connect(self.on_delete_toggled)

    def browse_directory(self):
        """
        浏览选择目录

        打开文件对话框让用户选择新的目录。
        """
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "选择新的 novels 目录",
            self.newDirEdit.text(),
            QFileDialog.ShowDirsOnly,
        )
        if new_dir:
            self.new_dir = new_dir
            self.newDirEdit.setText(new_dir)

    def on_dir_changed(self):
        """
        目录变更时显示高级选项

        当用户选择了新目录时，显示高级选项（迁移数据和删除原目录）。
        """
        if self.newDirEdit.text() != self.current_dir:
            self.advancedOptionsContainer.show()
        else:
            self.advancedOptionsContainer.hide()

    def on_delete_toggled(self, checked):
        """
        删除选项切换时显示警告

        当用户选择删除原目录时，显示警告信息。

        Args:
            checked: 是否选中删除选项
        """
        if checked:
            self.warningLabel.setText("⚠️ 删除原目录将永久删除原目录中的所有文件！")
            self.warningLabel.show()
        else:
            self.warningLabel.hide()

    def get_result(self):
        """
        获取用户选择结果

        Returns:
            dict: 包含新目录、是否迁移数据、是否删除原目录的字典
        """
        return {
            "new_dir": self.newDirEdit.text(),
            "migrate_data": self.migrateSwitch.isChecked(),
            "delete_old_dir": self.deleteOldDirSwitch.isChecked(),
        }


class ModelTypeDialog(MessageBoxBase):
    """
    模型类型选择对话框

    用于让用户选择要新增的模型类型（LLM 或 Embedding）。
    支持尺寸自适应。
    """

    def __init__(self, parent=None):
        """
        初始化模型类型选择对话框

        Args:
            parent: 父控件
        """
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

        sizer = DialogSizer(
            width_ratio=0.30,
            height_ratio=0.30,
            min_width=280,
            min_height=200,
        )
        sizer.apply_to_widget(self.widget, parent)

    def select_type(self, type_):
        """
        选择模型类型

        Args:
            type_: 选择的模型类型 ("llm" 或 "embedding")
        """
        self.selected_type = type_
        self.accept()


class ComposerModelDialog(MessageBoxBase):
    """
    Composer模型选择对话框

    用于让用户选择 Composer AI 使用的 LLM 模型配置。
    支持尺寸自适应。
    """

    def __init__(self, configs, current_model, parent=None):
        """
        初始化 Composer 模型选择对话框

        Args:
            configs: 可用的 LLM 模型配置列表
            current_model: 当前选择的模型
            parent: 父控件
        """
        super().__init__(parent)
        self.selected_model = current_model

        self.titleLabel = SubtitleLabel("选择 Composer 使用的模型", self)
        self.viewLayout.addWidget(self.titleLabel)

        self.formLayout = QVBoxLayout()

        label = BodyLabel("选择一个 LLM 模型配置用于 Composer AI", self)
        self.formLayout.addWidget(label)

        self.combo = ComboBox(self)
        self.combo.addItems(configs)
        if current_model in configs:
            self.combo.setCurrentText(current_model)
        self.formLayout.addWidget(self.combo)

        self.viewLayout.addLayout(self.formLayout)

        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.35,
            height_ratio=0.30,
            min_width=350,
            min_height=200,
        )
        sizer.apply_to_widget(self.widget, parent)

    def get_selected_model(self):
        """
        获取用户选择的模型

        Returns:
            str: 用户选择的模型名称
        """
        return self.combo.currentText()


class TestResultDialog(MessageBoxBase):
    """
    测试结果对话框

    用于显示模型配置测试的结果。
    - 测试失败时不会自动关闭，方便用户查看错误信息
    - 支持复制错误信息到剪贴板
    - 支持尺寸自适应和内容滚动
    """

    def __init__(self, title: str, content: str, is_success: bool, parent=None):
        """
        初始化测试结果对话框

        Args:
            title: 对话框标题
            content: 测试结果内容
            is_success: 测试是否成功
            parent: 父控件
        """
        super().__init__(parent)
        self._is_success = is_success
        self._content = content

        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)

        self.contentBrowser = QTextBrowser(self._container)
        self.contentBrowser.setOpenExternalLinks(True)
        self.contentBrowser.setMinimumHeight(150)
        self.contentBrowser.setPlainText(content)

        if is_success:
            self.contentBrowser.setStyleSheet(
                "color: #107c10; background-color: transparent; border: none;"
            )
        else:
            self.contentBrowser.setStyleSheet(
                "color: #d13438; background-color: transparent; border: none;"
            )

        self._container.content_layout().addWidget(self.contentBrowser)
        self._container.content_layout().addStretch()

        self.viewLayout.addWidget(self._container)

        self.copyBtn = PushButton(FIF.COPY, "复制", self)
        self.buttonGroup.addWidget(self.copyBtn)

        if is_success:
            self.yesButton.setText("确定")
            self.cancelButton.hide()
        else:
            self.yesButton.setText("重试")
            self.cancelButton.setText("关闭")

        self.copyBtn.clicked.connect(self._copy_content)

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.35,
            min_width=400,
            min_height=250,
        )
        sizer.apply_to_widget(self.widget, parent)

    def _copy_content(self):
        """
        复制内容到剪贴板
        """
        from PyQt5.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)

        self.copyBtn.setText("已复制!")
        from PyQt5.QtCore import QTimer

        QTimer.singleShot(2000, lambda: self.copyBtn.setText("复制"))

    def get_action(self):
        """
        获取用户选择的操作

        Returns:
            str: "retry" 表示重试，"close" 表示关闭
        """
        return (
            "retry" if self._is_success is False and self.yesButton.clicked else "close"
        )
