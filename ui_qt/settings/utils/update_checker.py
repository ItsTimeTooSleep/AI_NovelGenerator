# -*- coding: utf-8 -*-
"""
更新检查模块
============

本模块提供更新检查线程类，用于在后台检查 GitHub 上的最新版本。
"""

import os
import re
import sys

from PyQt5.QtCore import QThread, pyqtSignal
import requests

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from core.version import (
        GITHUB_API_RELEASES_URL,
        __version__,
    )
except ImportError:
    __version__ = "1.0.0"
    GITHUB_API_RELEASES_URL = (
        "https://api.github.com/repos/itstimetoosleep/AI_NovelGenerator/releases/latest"
    )


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

        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))

        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
