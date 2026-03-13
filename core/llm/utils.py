# -*- coding: utf-8 -*-
"""
LLM适配器工具函数模块

================================================================================
模块功能概述
================================================================================
本模块提供LLM适配器的工具函数，包括：
- Token管理器全局实例管理
- Token数量估算
- Token使用记录
- URL格式处理

================================================================================
核心函数
================================================================================
- set_global_tokens_manager: 设置全局Token管理器
- get_global_tokens_manager: 获取全局Token管理器
- estimate_tokens: Token数量估算
- record_token_usage: Token使用记录
- check_base_url: URL格式处理

================================================================================
设计决策
================================================================================
- 使用全局Token管理器支持跨模块的Token统计
- 支持tiktoken精确计算和近似估算两种模式
- URL处理支持自定义规则

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import re
from typing import Optional

from core.llm.base import UsageInfo, TIKTOKEN_AVAILABLE
from core.tokens_manager import TokensManager, TokenUsageRecord, get_token_context
from core import get_logger

_global_tokens_manager: Optional[TokensManager] = None


def set_global_tokens_manager(project_path: str) -> None:
    """
    设置全局Token管理器

    Args:
        project_path: 项目路径
    """
    global _global_tokens_manager
    _global_tokens_manager = TokensManager(project_path)
    get_logger().debug(
        "llm_adapters", f"全局Token管理器已设置，项目路径: {project_path}"
    )


def get_global_tokens_manager() -> Optional[TokensManager]:
    """
    获取全局Token管理器

    Returns:
        TokensManager实例，如果未设置则返回None
    """
    return _global_tokens_manager


def estimate_tokens(text: str, model_name: str = "gpt-4") -> tuple:
    """
    估算文本的Token数量

    Args:
        text: 要估算的文本
        model_name: 模型名称（用于选择合适的编码器）

    Returns:
        tuple: (估算的Token数量, 是否为估算值)
            - 当使用tiktoken精确计算时，is_estimated为False
            - 当使用近似估算时，is_estimated为True
    """
    logger = get_logger()
    if not text:
        return (0, False)

    if TIKTOKEN_AVAILABLE:
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(model_name)
            token_count = len(encoding.encode(text))
            logger.debug(
                "llm_adapters",
                f"Token估算(tiktoken): {token_count} tokens, 模型: {model_name}",
            )
            return (token_count, True)
        except KeyError:
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            token_count = len(encoding.encode(text))
            logger.debug(
                "llm_adapters",
                f"Token估算(默认编码): {token_count} tokens, 模型: {model_name}",
            )
            return (token_count, True)
    else:
        token_count = len(text) // 3
        logger.debug(
            "llm_adapters",
            f"Token估算(近似): {token_count} tokens, 文本长度: {len(text)}",
        )
        return (token_count, True)


def record_token_usage(
    model_name: str,
    prompt: str,
    response: str,
    model_version: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    cached_tokens: int = 0,
) -> None:
    """
    记录Token使用情况

    Args:
        model_name: 模型名称
        prompt: 输入提示词
        response: 输出响应
        model_version: 模型版本（可选）
        input_tokens: 输入Token数量（可选，如不提供则根据配置估算或标记为未知）
        output_tokens: 输出Token数量（可选，如不提供则根据配置估算或标记为未知）
        cached_tokens: 缓存Token数量
    """
    from core.config_manager import load_config

    logger = get_logger()
    tokens_manager = get_global_tokens_manager()
    token_context = get_token_context()

    if not tokens_manager or not token_context:
        logger.debug("llm_adapters", "Token管理器或上下文未设置，跳过Token记录")
        return

    input_estimated = False
    output_estimated = False

    config_file = os.path.join(os.getcwd(), "config.json")
    try:
        config = load_config(config_file)
        local_estimation_enabled = config.get("local_token_estimation", True)
    except Exception:
        local_estimation_enabled = True

    if input_tokens is None:
        if local_estimation_enabled:
            input_tokens, input_estimated = estimate_tokens(prompt, model_name)
        else:
            input_tokens = -1

    if output_tokens is None:
        if local_estimation_enabled:
            output_tokens, output_estimated = estimate_tokens(response, model_name)
        else:
            output_tokens = -1

    record = TokenUsageRecord(
        step_name=token_context.get("step_name", ""),
        model_name=model_name,
        model_version=model_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        chapter_number=token_context.get("chapter_number"),
        metadata=token_context.get("metadata", {}),
        input_estimated=input_estimated,
        output_estimated=output_estimated,
    )

    tokens_manager.add_record(record)
    cache_info = f", 缓存命中={cached_tokens}" if cached_tokens > 0 else ""
    input_display = "未知" if input_tokens == -1 else str(input_tokens)
    output_display = "未知" if output_tokens == -1 else str(output_tokens)
    if input_estimated:
        input_display += "(估算)"
    if output_estimated:
        output_display += "(估算)"
    logger.info(
        "llm_adapters",
        f"Token使用记录: 模型={model_name}, 输入={input_display}, 输出={output_display}{cache_info}, 步骤={token_context.get('step_name', '')}",
    )


def check_base_url(url: str) -> str:
    """
    处理base_url的规则：
    1. 如果url以#结尾，则移除#并直接使用用户提供的url
    2. 否则检查是否需要添加/v1后缀

    Args:
        url: 原始URL

    Returns:
        处理后的URL
    """
    url = url.strip()
    if not url:
        return url

    if url.endswith("#"):
        return url.rstrip("#")

    if not re.search(r"/v\d+$", url):
        if "/v1" not in url:
            url = url.rstrip("/") + "/v1"
    return url
