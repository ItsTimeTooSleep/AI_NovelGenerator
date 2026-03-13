# -*- coding: utf-8 -*-
"""
WebDAV 客户端模块
==================

本模块提供 WebDAV 客户端类，用于与 WebDAV 服务器交互。
"""

from requests.auth import HTTPBasicAuth


class WebDAVClient:
    """
    WebDAV 客户端类

    用于与 WebDAV 服务器进行交互，提供基本的认证功能。
    """

    def __init__(self, base_url, username, password):
        """
        初始化 WebDAV 客户端

        Args:
            base_url: WebDAV 服务器的基础 URL
            username: WebDAV 用户名
            password: WebDAV 密码
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = HTTPBasicAuth(username, password)
