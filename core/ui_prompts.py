# -*- coding: utf-8 -*-
"""
UI提示文本模块

================================================================================
模块功能概述
================================================================================
本模块集中定义了应用程序界面中各类提示信息文本。
这些提示文本用于帮助用户理解界面元素的含义和功能。

================================================================================
提示分类
================================================================================
1. Composer设置类：AI等级说明、模型选择说明等
2. 其他UI提示：待扩展

================================================================================
设计决策
================================================================================
- 使用字典结构存储提示文本，便于通过键名快速查找
- 支持HTML格式的富文本提示，便于格式化显示
- 提示文本集中管理，便于维护和国际化

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

UI_PROMPTS = {
    "composer_ai_level_description": {
        "title": "等级说明",
        "content": """
        <div style="font-family: 'Microsoft YaHei', sans-serif;">
            <p style="margin: 8px 0;"><strong style="color: {info_color};">mini（精简模式）</strong></p>
            <ul style="margin: 4px 0 12px 16px; color: {text_tertiary};">
                <li>发送内容：选中的文本 + 基础任务提示</li>
                <li>适用场景：语法修正、文字润色等简单编辑</li>
                <li>特点：响应最快，消耗最少</li>
            </ul>

            <p style="margin: 8px 0;"><strong style="color: {primary_color};">standard（标准模式）</strong></p>
            <ul style="margin: 4px 0 12px 16px; color: {text_tertiary};">
                <li>发送内容：选中文本 + 基础提示词 + <strong>当前章节完整内容</strong></li>
                <li>适用场景：段落扩展、需要上下文理解的编辑</li>
                <li>特点：平衡性能与智能程度</li>
            </ul>

            <p style="margin: 8px 0;"><strong style="color: {pro_color};">pro（专业模式）</strong></p>
            <ul style="margin: 4px 0 8px 16px; color: {text_tertiary};">
                <li>发送内容：选中文本 + 基础提示词 + <strong>完整上下文</strong></li>
                <li>上下文包括：小说架构、大纲目录、角色状态、全局摘要、当前章节</li>
                <li>适用场景：深度创作建议、复杂情节修改、需要全局一致性的编辑</li>
                <li>特点：最智能，但响应较慢，Token 消耗较多</li>
            </ul>
        </div>
        """,
    },
}


def get_prompt(key: str, **kwargs) -> str:
    """
    获取指定键的提示文本，支持变量替换

    Args:
        key: 提示文本的键名
        **kwargs: 用于替换提示文本中变量的关键字参数

    Returns:
        str: 格式化后的提示文本

    Raises:
        KeyError: 当指定的键不存在时抛出
    """
    if key not in UI_PROMPTS:
        raise KeyError(f"Prompt key '{key}' not found in UI_PROMPTS")

    prompt_data = UI_PROMPTS[key]
    content = prompt_data.get("content", "")

    if kwargs:
        content = content.format(**kwargs)

    return content


def get_prompt_title(key: str) -> str:
    """
    获取指定键的提示标题

    Args:
        key: 提示文本的键名

    Returns:
        str: 提示标题

    Raises:
        KeyError: 当指定的键不存在时抛出
    """
    if key not in UI_PROMPTS:
        raise KeyError(f"Prompt key '{key}' not found in UI_PROMPTS")

    return UI_PROMPTS[key].get("title", "")
