# -*- coding: utf-8 -*-
"""
AI Novel Generator - 设置分区模块
=============================
"""

import os
import sys

from qfluentwidgets import (
    PushSettingCard,
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
    GITHUB_REPO_URL = "https://github.com/itstimetoosleep/AI_NovelGenerator"
    GITHUB_API_RELEASES_URL = (
        "https://api.github.com/repos/itstimetoosleep/AI_NovelGenerator/releases/latest"
    )
    DONATION_URL = "https://afadian.com/"
    LICENSE_URL = f"{GITHUB_REPO_URL}/blob/main/LICENSE"
    AUTHOR = "ItsTimeTooSleep"


from ..base import BaseSettingsSection
from ..dialogs import (
    ChangeDirectoryDialog,
)


class DirectorySection(BaseSettingsSection):
    """
    小说目录设置分区
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建路径设置卡片
        self.pathCard = PushSettingCard(
            "更改",
            FIF.FOLDER,
            "小说存储目录",
            self.loaded_config.get("novels_directory", ""),
            self.view,
        )

        self.vBoxLayout.addWidget(self.pathCard)

        # 连接信号
        self.pathCard.clicked.connect(self.show_change_dialog)

    def show_change_dialog(self):
        """显示更改目录对话框"""
        current_dir = self.loaded_config.get("novels_directory", "")
        dialog = ChangeDirectoryDialog(current_dir, self.window())

        if dialog.exec():
            result = dialog.get_result()
            new_dir = result["new_dir"]
            migrate_data = result["migrate_data"]
            delete_old_dir = result["delete_old_dir"]

            if new_dir == current_dir:
                return

            self.apply_directory_change(
                current_dir, new_dir, migrate_data, delete_old_dir
            )

    def apply_directory_change(self, old_dir, new_dir, migrate_data, delete_old_dir):
        """应用目录更改"""
        import shutil

        try:
            # 创建新目录
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)

            # 迁移数据
            if migrate_data and old_dir and os.path.exists(old_dir):
                if os.listdir(old_dir):
                    self.show_info("提示", "正在迁移小说项目...")
                    for item in os.listdir(old_dir):
                        src = os.path.join(old_dir, item)
                        dst = os.path.join(new_dir, item)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)

            # 删除原目录
            if delete_old_dir and old_dir and os.path.exists(old_dir):
                shutil.rmtree(old_dir)

            # 更新配置
            self.loaded_config["novels_directory"] = new_dir
            self.pathCard.setContent(new_dir)

            if self.save_config_to_file():
                # 如果没有选择迁移，显示警告
                if (
                    not migrate_data
                    and old_dir
                    and os.path.exists(old_dir)
                    and os.listdir(old_dir)
                ):
                    self.show_warning(
                        "注意",
                        "您未选择迁移现有小说，程序以后可能找不到之前生成的小说！",
                    )
                else:
                    self.show_info("成功", "目录设置已保存")

        except Exception as e:
            self.show_error("错误", f"操作失败: {str(e)}")
