# -*- coding: utf-8 -*-
"""
LLM调用辅助模块

================================================================================
模块功能概述
================================================================================
本模块提供统一的LLM调用接口，支持流式和非流式两种模式，
根据配置自动选择调用方式。

================================================================================
核心函数
================================================================================
- invoke_llm: 统一的LLM调用接口，根据设置选择流式或非流式
- invoke_llm_stream: 强制使用流式调用

================================================================================
设计决策
================================================================================
- 统一的调用接口，简化上层代码
- 自动根据配置选择调用模式
- 支持回调函数处理流式响应

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional, Callable, Generator, Union
from core.llm import BaseLLMAdapter, StreamChunk


def invoke_llm(
    llm_adapter: BaseLLMAdapter,
    prompt: str,
    streaming_enabled: bool = False,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    """
    统一的LLM调用接口

    Args:
        llm_adapter: LLM适配器实例
        prompt: 输入提示词
        streaming_enabled: 是否启用流式传输
        on_chunk: 流式回调函数（仅在流式模式下使用）

    Returns:
        完整的响应文本
    """
    if streaming_enabled and on_chunk:
        return _invoke_stream_and_collect(llm_adapter, prompt, on_chunk)
    else:
        return llm_adapter.invoke(prompt)


def _invoke_stream_and_collect(
    llm_adapter: BaseLLMAdapter,
    prompt: str,
    on_chunk: Callable[[str], None],
) -> str:
    """
    流式调用并收集完整响应

    Args:
        llm_adapter: LLM适配器实例
        prompt: 输入提示词
        on_chunk: 流式回调函数

    Returns:
        完整的响应文本
    """
    full_content = ""
    for chunk in llm_adapter.invoke_stream(prompt):
        if chunk.content:
            full_content += chunk.content
            on_chunk(chunk.content)
    return full_content


def invoke_llm_stream(
    llm_adapter: BaseLLMAdapter,
    prompt: str,
    on_chunk: Optional[Callable[[StreamChunk], None]] = None,
) -> Generator[StreamChunk, None, None]:
    """
    强制使用流式调用

    Args:
        llm_adapter: LLM适配器实例
        prompt: 输入提示词
        on_chunk: 可选的回调函数

    Yields:
        StreamChunk: 流式响应数据块
    """
    yield from llm_adapter.invoke_stream(prompt, on_chunk)
