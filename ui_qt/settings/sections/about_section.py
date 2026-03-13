# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    HyperlinkCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SettingCardGroup,
    SwitchSettingCard,
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


from core import get_logger, LogLevel
from ..base import BaseSettingsSection
from ..dialogs import (
    UpdateDialog,
)
from ..utils import UpdateCheckThread
from ui_qt.utils.styles import ThemeManager


class ClickableLabel(BodyLabel):
    """支持点击和悬停变色的标签组件"""

    def __init__(self, text: str, url: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self._normal_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)
        self._hover_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY_DARK)
        self.setStyleSheet(f"color: {self._normal_color}; font-size: 12px;")
        self.setToolTip("点击打开链接")

    def enterEvent(self, event):
        """鼠标进入时改变颜色"""
        self.setStyleSheet(f"color: {self._hover_color}; font-size: 12px;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时恢复颜色"""
        self.setStyleSheet(f"color: {self._normal_color}; font-size: 12px;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击时打开链接"""
        if event.button() == Qt.LeftButton:
            import webbrowser

            webbrowser.open(self.url)
        super().mousePressEvent(event)


class AboutSection(BaseSettingsSection):
    """
    关于信息分区

    包含版本信息、GitHub 链接、捐赠链接、开源协议等内容。
    """

    def __init__(self, parent=None):
        """
        初始化关于信息分区

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 关于信息组
        self.aboutGroup = SettingCardGroup("关于", self.view)

        # 版本信息卡片
        self.versionCard = PrimaryPushSettingCard(
            "检查更新",
            FIF.INFO,
            "版本信息",
            f"当前版本：v{__version__}",
            parent=self.aboutGroup,
        )
        self.versionCard.clicked.connect(self.check_for_updates)
        self.aboutGroup.addSettingCard(self.versionCard)

        # GitHub 仓库链接
        self.aboutCard = HyperlinkCard(
            GITHUB_REPO_URL,
            "GitHub 仓库",
            FIF.LINK,
            "AI Novel Generator Enhanced",
            "",  # 清空默认内容
            self.aboutGroup,
        )

        # 创建水平布局来放置所有文本
        from PyQt5.QtWidgets import QHBoxLayout

        # 添加可点击的"原始项目"标签
        self.originalProjectLabel = ClickableLabel(
            "AI_NovelGenerator",
            "https://github.com/YILING0013/AI_NovelGenerator",
            self.aboutCard,
        )

        # 创建水平布局容器
        contentWidget = QWidget()
        contentLayout = QHBoxLayout(contentWidget)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(4)

        # 添加"基于"文字
        basedLabel = BodyLabel("基于 ", contentWidget)
        basedLabel.setStyleSheet("color: gray; font-size: 12px;")
        contentLayout.addWidget(basedLabel)

        # 添加可点击标签
        contentLayout.addWidget(self.originalProjectLabel)

        # 添加后续说明文字
        self.projectDescLabel = BodyLabel(" 的 UI 优化分支", contentWidget)
        self.projectDescLabel.setStyleSheet("color: gray; font-size: 12px;")
        contentLayout.addWidget(self.projectDescLabel)

        contentLayout.addStretch()

        # 替换原有的内容标签布局
        self.aboutCard.contentLabel.hide()
        self.aboutCard.vBoxLayout.addWidget(contentWidget)

        self.aboutGroup.addSettingCard(self.aboutCard)

        # 问题反馈链接
        self.feedbackCard = PushSettingCard(
            "提交反馈",
            FIF.FEEDBACK,
            "问题反馈",
            "有 Bug 需要反馈？有更新建议？点击提交 Issue",
            self.aboutGroup,
        )
        self.feedbackCard.clicked.connect(self.open_feedback_link)
        self.aboutGroup.addSettingCard(self.feedbackCard)

        # 捐赠链接
        self.donationCard = PushSettingCard(
            "支持项目",
            FIF.HEART,
            "支持项目",
            "觉得这个改进版本好用？请当前维护者喝杯咖啡",
            self.aboutGroup,
        )
        self.donationCard.clicked.connect(self.open_donation_link)
        self.aboutGroup.addSettingCard(self.donationCard)

        # 开源协议
        self.licenseCard = PushSettingCard(
            "查看协议",
            FIF.CODE,
            "开源协议",
            "GNU General Public License",
            self.aboutGroup,
        )
        self.licenseCard.clicked.connect(self.open_license_link)
        self.aboutGroup.addSettingCard(self.licenseCard)

        self.vBoxLayout.addWidget(self.aboutGroup)

        # 开发者选项组
        self.developerGroup = SettingCardGroup("开发者选项", self.view)

        self.developerModeCard = SwitchSettingCard(
            FIF.SETTING,
            "开发者模式",
            "启用后可以在 Step 1 和 Step 2 中使用跳过功能",
            parent=self.developerGroup,
        )
        self.developerModeCard.checkedChanged.connect(self.on_developer_mode_changed)
        self.developerGroup.addSettingCard(self.developerModeCard)

        self.vBoxLayout.addWidget(self.developerGroup)

        self.localTokenEstimationCard = SwitchSettingCard(
            FIF.TAG,
            "本地Token估算",
            "当API未返回Token使用信息时，使用本地算法估算Token数量。关闭后，未返回Token信息的请求将显示为'未知'",
            parent=self.developerGroup,
        )
        self.localTokenEstimationCard.checkedChanged.connect(
            self.on_local_token_estimation_changed
        )
        self.developerGroup.addSettingCard(self.localTokenEstimationCard)

        self.vBoxLayout.addWidget(self.developerGroup)

        self.update_thread = None

        self._init_developer_mode()
        self._init_local_token_estimation()

        self.original_button_text = "检查更新"

    def _set_loading_state(self, is_loading):
        """
        设置加载状态

        Args:
            is_loading: 是否处于加载状态
        """
        if is_loading:
            self.versionCard.setEnabled(False)
            if hasattr(self.versionCard, "button"):
                self.versionCard.button.setText("检查中...")
        else:
            self.versionCard.setEnabled(True)
            if hasattr(self.versionCard, "button"):
                self.versionCard.button.setText(self.original_button_text)

    def check_for_updates(self):
        """
        检查应用程序更新

        启动后台线程检查 GitHub 上的最新版本。
        """
        if self.update_thread and self.update_thread.isRunning():
            self.show_info("提示", "正在检查更新中，请稍候...")
            return

        self.update_thread = UpdateCheckThread()
        self.update_thread.update_available.connect(self.on_update_available)
        self.update_thread.update_not_available.connect(self.on_update_not_available)
        self.update_thread.error_occurred.connect(self.on_update_error)

        # 显示加载状态
        self._set_loading_state(True)
        self.update_thread.start()

    def on_update_available(self, release_data):
        """
        处理发现新版本的事件

        Args:
            release_data: GitHub release 数据字典
        """
        self._set_loading_state(False)
        dialog = UpdateDialog(release_data, self.window())
        if dialog.exec():
            # 用户点击了"前往更新"
            html_url = release_data.get("html_url", GITHUB_REPO_URL + "/releases")
            webbrowser.open(html_url)

    def on_update_not_available(self):
        """
        处理没有更新的事件
        """
        self._set_loading_state(False)
        self.show_info("已是最新", f"当前版本 v{__version__} 是最新版本！")

    def on_update_error(self, error_msg):
        """
        处理更新检查错误

        Args:
            error_msg: 错误信息字符串
        """
        self._set_loading_state(False)
        self.show_error("检查更新失败", f"网络错误: {error_msg}")

    def open_donation_link(self):
        """
        打开捐赠链接
        """
        webbrowser.open(DONATION_URL)

    def open_license_link(self):
        """
        打开开源协议链接
        """
        webbrowser.open(LICENSE_URL)

    def open_feedback_link(self):
        """
        打开问题反馈链接（GitHub Issue 页面）
        """
        issue_url = f"{GITHUB_REPO_URL}/issues/new"
        webbrowser.open(issue_url)

    def _init_developer_mode(self):
        """
        初始化开发者模式状态
        """
        developer_mode = self.loaded_config.get("developer_mode", False)
        self.developerModeCard.setChecked(developer_mode)

    def _init_local_token_estimation(self):
        """
        初始化本地Token估算状态
        """
        local_estimation = self.loaded_config.get("local_token_estimation", True)
        self.localTokenEstimationCard.setChecked(local_estimation)

    def on_local_token_estimation_changed(self, checked):
        """
        处理本地Token估算开关变更

        Args:
            checked: 开关是否被选中
        """
        self.loaded_config["local_token_estimation"] = checked
        if self.save_config_to_file():
            if checked:
                self.show_info(
                    "本地Token估算",
                    "本地Token估算已启用，API未返回Token信息时将使用本地算法估算",
                )
            else:
                self.show_info(
                    "本地Token估算",
                    "本地Token估算已禁用，API未返回Token信息时将显示为'未知'",
                )

    def on_developer_mode_changed(self, checked):
        """
        处理开发者模式开关变更

        Args:
            checked: 开关是否被选中
        """
        self.loaded_config["developer_mode"] = checked
        logger = get_logger()
        if checked:
            logger.set_level(LogLevel.DEBUG)
        else:
            logger.set_level(LogLevel.INFO)
        if self.save_config_to_file():
            if checked:
                self.show_info(
                    "开发者模式",
                    "开发者模式已启用，现在可以使用跳过功能，DEBUG日志已开启",
                )
            else:
                self.show_info("开发者模式", "开发者模式已禁用，DEBUG日志已关闭")
