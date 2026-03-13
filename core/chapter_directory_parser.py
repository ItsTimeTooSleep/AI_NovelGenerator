# -*- coding: utf-8 -*-
"""
章节目录解析器模块

================================================================================
模块功能概述
================================================================================
本模块负责解析AI生成的章节蓝图文本，将其转换为结构化的章节信息列表。
章节蓝图是小说生成过程中的重要中间产物，定义了每章的定位、作用、悬念等元信息。

================================================================================
核心功能
================================================================================
1. parse_chapter_blueprint: 解析整份章节蓝图文本，返回结构化章节列表
2. get_chapter_info_from_blueprint: 获取指定章节的结构化信息

================================================================================
解析格式
================================================================================
章节蓝图文本格式示例：
    第1章 - [开端]
    本章定位：[角色]
    核心作用：[推进]
    悬念密度：[紧凑]
    伏笔操作：埋设(A线索)
    认知颠覆：★☆☆☆☆
    本章简述：[详细描述...]

================================================================================
设计决策
================================================================================
- 使用正则表达式解析文本，支持多行内容和可选的方括号包裹
- 解析结果按章节号排序，确保顺序正确
- 找不到指定章节时返回默认结构，避免程序崩溃

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import re


def parse_chapter_blueprint(blueprint_text: str):
    """
    解析整份章节蓝图文本，返回结构化的章节信息列表。

    该函数使用正则表达式从蓝图文本中提取每章的元信息，
    包括章节号、标题、定位、作用、悬念密度、伏笔操作、认知颠覆等级和简述。
    支持两种格式：
    1. 标准格式：第1章 - [开端]
    2. Markdown格式：## 第1章 - 标题，**本章定位**：内容

    参数:
        blueprint_text: 章节蓝图的完整文本内容

    返回值:
        list: 章节信息字典列表，每个字典包含：
            - chapter_number: 章节号（整数）
            - chapter_title: 章节标题（字符串）
            - chapter_role: 本章定位（字符串）
            - chapter_purpose: 核心作用（字符串）
            - suspense_level: 悬念密度（字符串）
            - foreshadowing: 伏笔操作（字符串）
            - plot_twist_level: 认知颠覆等级（字符串）
            - chapter_summary: 本章简述（字符串）

    使用示例:
        >>> blueprint = "第1章 - [开端]\\n本章定位：[角色]\\n..."
        >>> chapters = parse_chapter_blueprint(blueprint)
        >>> print(chapters[0]["chapter_title"])
        开端

    设计说明:
        - 支持章节号前后有空格（如"第 1 章"）
        - 支持标题是否用方括号包裹
        - 支持Markdown格式的粗体字段
        - 简述内容可以是多行文本
        - 结果按章节号升序排列
    """
    chapter_block_pattern = r"(##?\s*第\s*\d+\s*章.*?)(?=^##?\s*第\s*\d+\s*章|\Z)"
    chunks = re.findall(
        chapter_block_pattern, blueprint_text, flags=re.DOTALL | re.MULTILINE
    )

    if not chunks:
        chapter_block_pattern = r"(第\s*\d+\s*章.*?)(?=^第\s*\d+\s*章|\Z)"
        chunks = re.findall(
            chapter_block_pattern, blueprint_text, flags=re.DOTALL | re.MULTILINE
        )

    results = []

    chapter_number_pattern = re.compile(
        r"##?\s*第\s*(\d+)\s*章\s*-\s*\[?(.*?)\]?$", re.MULTILINE
    )

    if not chapter_number_pattern.search(blueprint_text):
        chapter_number_pattern = re.compile(
            r"第\s*(\d+)\s*章\s*-\s*\[?(.*?)\]?$", re.MULTILINE
        )

    role_pattern = re.compile(
        r"^\*?\*?本章定位\*?\*?[:：]\*?\*?\s*\[?(.*?)\]?$", re.MULTILINE
    )
    purpose_pattern = re.compile(
        r"^\*?\*?核心作用\*?\*?[:：]\*?\*?\s*\[?(.*?)\]?$", re.MULTILINE
    )
    suspense_pattern = re.compile(
        r"^\*?\*?悬念密度\*?\*?[:：]\*?\*?\s*\[?(.*?)\]?$", re.MULTILINE
    )
    foreshadow_pattern = re.compile(
        r"^\*?\*?伏笔操作\*?\*?[:：]\*?\*?\s*\[?(.*?)\]?$", re.MULTILINE
    )
    twist_pattern = re.compile(
        r"^\*?\*?认知颠覆\*?\*?[:：]\*?\*?\s*\[?(.*?)\]?$", re.MULTILINE
    )
    summary_pattern = re.compile(
        r"^\*?\*?本章简述\*?\*?[:：]\*?\*?\s*\[?(.*)", re.DOTALL | re.MULTILINE
    )

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        header_match = chapter_number_pattern.search(chunk)
        if not header_match:
            continue

        chapter_number = int(header_match.group(1))
        chapter_title = header_match.group(2).strip()

        chapter_role = ""
        m_role = role_pattern.search(chunk)
        if m_role:
            chapter_role = m_role.group(1).strip()

        chapter_purpose = ""
        m_purpose = purpose_pattern.search(chunk)
        if m_purpose:
            chapter_purpose = m_purpose.group(1).strip()

        suspense_level = ""
        m_suspense = suspense_pattern.search(chunk)
        if m_suspense:
            suspense_level = m_suspense.group(1).strip()

        foreshadowing = ""
        m_foreshadow = foreshadow_pattern.search(chunk)
        if m_foreshadow:
            foreshadowing = m_foreshadow.group(1).strip()

        plot_twist_level = ""
        m_twist = twist_pattern.search(chunk)
        if m_twist:
            plot_twist_level = m_twist.group(1).strip()

        chapter_summary = ""
        m_summary = summary_pattern.search(chunk)
        if m_summary:
            raw_summary = m_summary.group(1).strip()
            if raw_summary.endswith("]"):
                raw_summary = raw_summary[:-1].strip()
            chapter_summary = raw_summary

        results.append(
            {
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "chapter_role": chapter_role,
                "chapter_purpose": chapter_purpose,
                "suspense_level": suspense_level,
                "foreshadowing": foreshadowing,
                "plot_twist_level": plot_twist_level,
                "chapter_summary": chapter_summary,
            }
        )

    results.sort(key=lambda x: x["chapter_number"])
    return results


def get_chapter_info_from_blueprint(blueprint_text: str, target_chapter_number: int):
    """
    从章节蓝图中获取指定章节的结构化信息。

    该函数先解析整份蓝图，然后查找指定章节号的信息。
    如果找不到指定章节，返回一个包含默认值的结构。

    参数:
        blueprint_text: 章节蓝图的完整文本内容
        target_chapter_number: 目标章节号

    返回值:
        dict: 章节信息字典，包含与parse_chapter_blueprint相同的字段结构

    使用示例:
        >>> info = get_chapter_info_from_blueprint(blueprint, 5)
        >>> print(info["chapter_title"])

    设计说明:
        - 找不到章节时返回默认结构而非None，避免调用方空指针异常
        - 默认标题为"第{章节号}章"格式
    """
    all_chapters = parse_chapter_blueprint(blueprint_text)
    for ch in all_chapters:
        if ch["chapter_number"] == target_chapter_number:
            return ch
    return {
        "chapter_number": target_chapter_number,
        "chapter_title": f"第{target_chapter_number}章",
        "chapter_role": "",
        "chapter_purpose": "",
        "suspense_level": "",
        "foreshadowing": "",
        "plot_twist_level": "",
        "chapter_summary": "",
    }
