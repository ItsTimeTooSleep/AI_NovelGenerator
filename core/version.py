# -*- coding: utf-8 -*-
"""
版本管理模块

================================================================================
模块功能概述
================================================================================
本模块存储AI小说生成器应用程序的版本信息、产品信息和相关链接配置。
集中管理版本号便于维护和更新检查。

================================================================================
核心变量
================================================================================
- __version__: 应用程序版本号
- PRODUCT_NAME_EN: 产品英文名称
- PRODUCT_NAME_CN: 产品中文名称
- PRODUCT_NAME_FILESAFE: 文件系统友好名称（无空格和特殊字符）
- LEGAL_COPYRIGHT: 法律版权声明
- GITHUB_REPO_URL: GitHub仓库地址
- GITHUB_API_RELEASES_URL: GitHub API发布检查地址
- DONATION_URL: 捐赠链接
- LICENSE_URL: 开源许可证链接
- AUTHOR: 项目作者信息

================================================================================
设计决策
================================================================================
- 版本信息集中管理，便于自动化更新和版本检查
- 使用语义化版本号（Semantic Versioning）
- 相关链接统一配置，便于维护
- 提供双语产品名称，支持国际化场景

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

__version__ = "1.0.0"

PRODUCT_NAME_EN = "AI Novel Generator"

PRODUCT_NAME_CN = "AI小说生成器"

PRODUCT_NAME_FILESAFE = "AI_Novel_Generator"

LEGAL_COPYRIGHT = (
    "Copyright (C) YILING0013 and contributors; Modifications (C) 2026 ItsTimeTooSleep"
)

GITHUB_REPO_URL = "https://github.com/itstimetoosleep/AI_NovelGenerator"

GITHUB_API_RELEASES_URL = (
    "https://api.github.com/repos/itstimetoosleep/AI_NovelGenerator/releases/latest"
)

DONATION_URL = "https://afadian.com/"

LICENSE_URL = f"{GITHUB_REPO_URL}/blob/main/LICENSE"

AUTHOR = "ItsTimeTooSleep"
