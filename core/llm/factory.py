# -*- coding: utf-8 -*-
"""
LLM适配器工厂模块

================================================================================
模块功能概述
================================================================================
本模块提供LLM适配器的工厂函数，根据接口格式创建对应的适配器实例。

================================================================================
核心函数
================================================================================
- create_llm_adapter: 工厂函数，根据接口格式创建适配器

================================================================================
支持的接口格式
================================================================================
- deepseek: DeepSeek API
- openai: OpenAI API
- azure openai: Azure OpenAI API
- azure ai: Azure AI Inference API
- ollama: Ollama本地模型
- ml studio: ML Studio本地开发环境
- gemini: Google Gemini API
- 阿里云百炼: 阿里云大模型服务
- 火山引擎: 字节跳动云服务
- 硅基流动: SiliconFlow模型服务
- grok: xAI Grok模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional

from core.llm.base import BaseLLMAdapter
from core.llm.adapters import (
    DeepSeekAdapter,
    OpenAIAdapter,
    GeminiAdapter,
    AzureOpenAIAdapter,
    AzureAIAdapter,
    OllamaAdapter,
    MLStudioAdapter,
    VolcanoEngineAIAdapter,
    SiliconFlowAdapter,
    GrokAdapter,
)
from core import get_logger


def create_llm_adapter(
    interface_format: str,
    base_url: str,
    model_name: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> BaseLLMAdapter:
    """
    工厂函数：根据 interface_format 返回不同的适配器实例。

    Args:
        interface_format: 接口格式名称
        base_url: API基础URL
        model_name: 模型名称
        api_key: API密钥
        temperature: 温度参数
        max_tokens: 最大输出token数
        timeout: 请求超时时间（秒）

    Returns:
        BaseLLMAdapter: 对应的适配器实例

    Raises:
        ValueError: 当接口格式未知时抛出
    """
    logger = get_logger()
    fmt = interface_format.strip().lower()
    logger.info(
        "llm_adapters", f"创建LLM适配器: 格式={interface_format}, 模型={model_name}"
    )

    if fmt == "deepseek":
        return DeepSeekAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "openai":
        return OpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "azure openai":
        return AzureOpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "azure ai":
        return AzureAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "ollama":
        return OllamaAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "ml studio":
        return MLStudioAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "gemini":
        return GeminiAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "阿里云百炼":
        return OpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "火山引擎":
        return VolcanoEngineAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "硅基流动":
        return SiliconFlowAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    elif fmt == "grok":
        return GrokAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
    else:
        logger.error("llm_adapters", f"未知的接口格式: {interface_format}")
        raise ValueError(f"Unknown interface_format: {interface_format}")
