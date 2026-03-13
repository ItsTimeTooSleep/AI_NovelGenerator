# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys

from PyQt5.QtWidgets import (
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    IndicatorPosition,
    LineEdit,
    PrimaryPushButton,
    SwitchButton,
)
from qfluentwidgets import FluentIcon as FIF

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from core.version import (
        AUTHOR,
        DONATION_URL,
        GITHUB_API_RELEASES_URL,
        GITHUB_REPO_URL,
        LICENSE_URL,
        __version__,
    )
except ImportError:
    __version__ = "1.0.0"
    GITHUB_REPO_URL = "https://github.com/Doctor-Shadow/AI_NovelGenerator"
    GITHUB_API_RELEASES_URL = (
        "https://api.github.com/repos/Doctor-Shadow/AI_NovelGenerator/releases/latest"
    )
    DONATION_URL = "https://afadian.com/"
    LICENSE_URL = f"{GITHUB_REPO_URL}/blob/main/LICENSE"
    AUTHOR = "ItsTimeTooSleep"


from ..base import BaseSettingsSection


class ProxySection(BaseSettingsSection):
    """
    代理配置分区
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.card = CardWidget(self.view)
        self.layout = QVBoxLayout(self.card)

        proxy_setting = self.loaded_config.get("proxy_setting", {})

        self.enableSwitch = SwitchButton("启用代理", self.card, IndicatorPosition.RIGHT)
        self.enableSwitch.setChecked(proxy_setting.get("enabled", False))
        self.layout.addWidget(self.enableSwitch)

        self.addrLabel = BodyLabel("地址", self.card)
        self.addrEdit = LineEdit(self.card)
        self.addrEdit.setText(proxy_setting.get("proxy_url", "127.0.0.1"))
        self.layout.addWidget(self.addrLabel)
        self.layout.addWidget(self.addrEdit)

        self.portLabel = BodyLabel("端口", self.card)
        self.portEdit = LineEdit(self.card)
        self.portEdit.setText(proxy_setting.get("proxy_port", "10809"))
        self.layout.addWidget(self.portLabel)
        self.layout.addWidget(self.portEdit)

        self.saveBtn = PrimaryPushButton(FIF.SAVE, "保存代理设置", self.card)
        self.layout.addWidget(self.saveBtn)

        self.vBoxLayout.addWidget(self.card)

        self.saveBtn.clicked.connect(self.save_proxy)

    def save_proxy(self):
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

        if enabled:
            os.environ["HTTP_PROXY"] = f"http://{url}:{port}"
            os.environ["HTTPS_PROXY"] = f"http://{url}:{port}"
        else:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
