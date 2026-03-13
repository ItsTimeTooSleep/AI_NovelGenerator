# -*- coding: utf-8 -*-
"""
一致性检查器模块

================================================================================
模块功能概述
================================================================================
本模块负责检查小说生成过程中的内容一致性，确保新生成的章节与已有设定、
角色状态、前文摘要等保持逻辑一致，避免出现矛盾或冲突。

================================================================================
核心功能
================================================================================
check_consistency: 调用LLM检查小说设定与最新章节的一致性

================================================================================
检查维度
================================================================================
1. 小说设定：核心世界观、规则体系
2. 角色状态：人物属性、关系网络
3. 前文摘要：已发生的剧情事件
4. 剧情要点：未解决的冲突或伏笔
5. 章节内容：新生成的章节文本

================================================================================
设计决策
================================================================================
- 使用LLM进行语义级别的一致性检查，而非简单的规则匹配
- 检查结果由AI生成，包含具体的冲突描述和建议
- 温度参数默认设为0.3，确保检查结果的稳定性

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from core.llm import create_llm_adapter

CONSISTENCY_PROMPT = """\
请检查下面的小说设定与最新章节是否存在明显冲突或不一致之处，如有请列出：
- 小说设定：
{novel_setting}

- 角色状态（可能包含重要信息）：
{character_state}

- 前文摘要：
{global_summary}

- 已记录的未解决冲突或剧情要点：
{plot_arcs}

- 最新章节内容：
{chapter_text}

如果存在冲突或不一致，请说明；如果在未解决冲突中有被忽略或需要推进的地方，也请提及；否则请返回"无明显冲突"。
"""


def check_consistency(
    novel_setting: str,
    character_state: str,
    global_summary: str,
    chapter_text: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float = 0.3,
    plot_arcs: str = "",
    interface_format: str = "OpenAI",
    max_tokens: int = 2048,
    timeout: int = 600,
) -> str:
    """
    调用LLM检查小说内容的一致性。

    该函数将小说设定、角色状态、前文摘要、剧情要点和最新章节内容
    组合成提示词，发送给LLM进行一致性检查。

    参数:
        novel_setting: 小说世界观设定文本
        character_state: 角色状态文档文本
        global_summary: 前文摘要文本
        chapter_text: 待检查的章节内容
        api_key: API密钥
        base_url: API基础URL
        model_name: 使用的模型名称
        temperature: 生成温度，默认0.3（较低值确保稳定性）
        plot_arcs: 未解决的冲突或剧情要点，可选
        interface_format: 接口格式，默认"OpenAI"
        max_tokens: 最大生成Token数，默认2048
        timeout: 请求超时时间（秒），默认600

    返回值:
        str: LLM返回的一致性检查结果文本。如果调用失败返回"审校Agent无回复"

    异常:
        无直接抛出异常，内部捕获所有异常

    使用示例:
        >>> result = check_consistency(
        ...     novel_setting="世界观设定...",
        ...     character_state="角色状态...",
        ...     global_summary="前文摘要...",
        ...     chapter_text="新章节内容...",
        ...     api_key="sk-xxx",
        ...     base_url="https://api.openai.com/v1",
        ...     model_name="gpt-4"
        ... )
        >>> print(result)

    设计说明:
        - 使用较低的温度值(0.3)确保检查结果的稳定性
        - 支持检查未解决冲突/剧情要点的衔接情况
        - 调试模式下会打印提示词和响应内容
    """
    prompt = CONSISTENCY_PROMPT.format(
        novel_setting=novel_setting,
        character_state=character_state,
        global_summary=global_summary,
        plot_arcs=plot_arcs,
        chapter_text=chapter_text,
    )

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    print("\n[ConsistencyChecker] Prompt >>>", prompt)

    response = llm_adapter.invoke(prompt)
    if not response:
        return "审校Agent无回复"

    print("[ConsistencyChecker] Response <<<", response)

    return response
