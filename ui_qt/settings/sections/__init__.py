# -*- coding: utf-8 -*-
"""
设置分区模块
==========

本模块包含所有设置分区类。
"""

from .about_section import AboutSection
from .appearance_section import AppearanceSection
from .composer_section import ComposerSection
from .directory_section import DirectorySection
from .llm_section import LLMSection
from .prompt_section import PromptSection
from .proxy_section import ProxySection
from .webdav_section import WebDAVSection

__all__ = [
    "LLMSection",
    "ComposerSection",
    "DirectorySection",
    "ProxySection",
    "AppearanceSection",
    "WebDAVSection",
    "AboutSection",
    "PromptSection",
]
