# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys

from qfluentwidgets import (
    PrimaryPushSettingCard,
    PushSettingCard,
    SettingCardGroup,
)
from qfluentwidgets import FluentIcon as FIF
import requests
from requests.auth import HTTPBasicAuth

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
    load_config,
    save_config,
)
from ui_qt.utils.helpers import get_global_notify

from ..base import BaseSettingsSection


class WebDAVSection(BaseSettingsSection):
    """
    WebDAV 备份分区
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.webdavGroup = SettingCardGroup("WebDAV 备份", self.view)

        webdav_conf = self.loaded_config.get("webdav_config", {})

        self.webdavUrlCard = PushSettingCard(
            "配置",
            FIF.LINK,
            "WebDAV URL",
            webdav_conf.get("webdav_url", "") or "未配置",
            self.webdavGroup,
        )

        self.webdavUserCard = PushSettingCard(
            "配置",
            FIF.PEOPLE,
            "用户名",
            webdav_conf.get("webdav_username", "") or "未配置",
            self.webdavGroup,
        )

        self.webdavPwdCard = PushSettingCard(
            "配置", FIF.EDIT, "密码", "******", self.webdavGroup
        )

        self.testConnCard = PrimaryPushSettingCard(
            "测试连接",
            FIF.LINK,
            "测试连接",
            "测试 WebDAV 服务器连接状态",
            self.webdavGroup,
        )

        self.backupCard = PrimaryPushSettingCard(
            "立即备份",
            FIF.CLOUD_DOWNLOAD,
            "备份配置",
            "将当前配置备份到 WebDAV",
            self.webdavGroup,
        )

        self.restoreCard = PrimaryPushSettingCard(
            "立即恢复",
            FIF.SYNC,
            "恢复配置",
            "从 WebDAV 恢复配置 (会覆盖当前设置)",
            self.webdavGroup,
        )

        self.webdavGroup.addSettingCard(self.webdavUrlCard)
        self.webdavGroup.addSettingCard(self.webdavUserCard)
        self.webdavGroup.addSettingCard(self.webdavPwdCard)
        self.webdavGroup.addSettingCard(self.testConnCard)
        self.webdavGroup.addSettingCard(self.backupCard)
        self.webdavGroup.addSettingCard(self.restoreCard)

        self.vBoxLayout.addWidget(self.webdavGroup)

        self.webdavUrlCard.clicked.connect(
            lambda: self.edit_webdav_setting("webdav_url", "WebDAV URL")
        )
        self.webdavUserCard.clicked.connect(
            lambda: self.edit_webdav_setting("webdav_username", "用户名")
        )
        self.webdavPwdCard.clicked.connect(
            lambda: self.edit_webdav_setting(
                "webdav_password", "密码", is_password=True
            )
        )

        self.testConnCard.clicked.connect(self.test_webdav)
        self.backupCard.clicked.connect(self.backup_webdav)
        self.restoreCard.clicked.connect(self.restore_webdav)

    def edit_webdav_setting(self, key, title, is_password=False):
        from PyQt5.QtWidgets import QInputDialog, QLineEdit

        current_val = self.loaded_config.get("webdav_config", {}).get(key, "")
        mode = QLineEdit.Password if is_password else QLineEdit.Normal

        text, ok = QInputDialog.getText(
            self, f"编辑 {title}", f"请输入 {title}:", mode, current_val
        )
        if ok:
            if "webdav_config" not in self.loaded_config:
                self.loaded_config["webdav_config"] = {}
            self.loaded_config["webdav_config"][key] = text
            save_config(self.loaded_config, self.config_file)

            if key == "webdav_url":
                self.webdavUrlCard.setContent(text)
            elif key == "webdav_username":
                self.webdavUserCard.setContent(text)

            notify = get_global_notify()
            if notify:
                notify.success("成功", f"{title} 已更新")

    def get_webdav_client(self):
        conf = self.loaded_config.get("webdav_config", {})
        url = conf.get("webdav_url", "")
        user = conf.get("webdav_username", "")
        pwd = conf.get("webdav_password", "")

        if not url:
            show_error_notification("错误", "请先配置 WebDAV URL", parent=self.window())
            return None

        return WebDAVClient(url, user, pwd)

    def test_webdav(self):
        client = self.get_webdav_client()
        if client:
            try:
                response = requests.request(
                    "PROPFIND",
                    client.base_url,
                    headers={"Depth": "0"},
                    auth=client.auth,
                )
                if response.status_code < 400:
                    notify = get_global_notify()
                    if notify:
                        notify.success("成功", "连接成功")
                else:
                    show_error_notification(
                        "失败",
                        f"连接失败: {response.status_code}",
                        parent=self.window(),
                    )
            except Exception as e:
                show_error_notification("错误", str(e), parent=self.window())

    def backup_webdav(self):
        client = self.get_webdav_client()
        if not client:
            return

        try:
            target_dir = "AI_Novel_Generator"
            try:
                requests.request(
                    "MKCOL", client.base_url + target_dir, auth=client.auth
                )
            except Exception:
                pass

            with open(self.config_file, "rb") as f:
                requests.put(
                    client.base_url + f"{target_dir}/config.json",
                    data=f,
                    auth=client.auth,
                )

            notify = get_global_notify()
            if notify:
                notify.success("成功", "备份成功")
        except Exception as e:
            show_error_notification("错误", str(e), parent=self.window())

    def restore_webdav(self):
        client = self.get_webdav_client()
        if not client:
            return

        try:
            target_dir = "AI_Novel_Generator"
            resp = requests.get(
                client.base_url + f"{target_dir}/config.json", auth=client.auth
            )
            resp.raise_for_status()

            with open(self.config_file, "wb") as f:
                f.write(resp.content)

            self.loaded_config = load_config(self.config_file)
            notify = get_global_notify()
            if notify:
                notify.success("成功", "恢复成功，请重启应用生效")
        except Exception as e:
            show_error_notification("错误", str(e), parent=self.window())


class WebDAVClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = HTTPBasicAuth(username, password)
