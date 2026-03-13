# -*- coding: utf-8 -*-
"""
大语言模型(LLM)适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供统一的大语言模型接口适配层，支持多种AI服务商的模型调用。
通过适配器模式屏蔽不同API接口的差异，为上层提供一致的调用方式。

================================================================================
支持的模型服务商
================================================================================
- OpenAI: 官方GPT系列模型
- DeepSeek: 深度求索大模型
- Azure OpenAI: 微软Azure托管的OpenAI模型
- Azure AI: Azure AI服务部署的模型
- Ollama: 本地部署的开源模型
- ML Studio: 本地开发环境模型
- Gemini: Google Gemini系列模型
- 阿里云百炼: 阿里云大模型服务
- 火山引擎: 字节跳动云服务模型
- 硅基流动: SiliconFlow模型服务
- Grok: xAI Grok模型

================================================================================
核心类与函数
================================================================================
- BaseLLMAdapter: LLM适配器基类，定义统一接口
- StreamChunk: 流式响应数据块
- UsageInfo: Token使用信息数据结构
- UsageExtractor: Token使用信息提取器
- create_llm_adapter: 工厂函数，根据接口格式创建对应适配器
- estimate_tokens: Token数量估算函数
- record_token_usage: Token使用记录函数
- check_base_url: URL格式处理函数
- set_global_tokens_manager: 设置全局Token管理器
- get_global_tokens_manager: 获取全局Token管理器

================================================================================
设计决策
================================================================================
- 使用适配器模式统一不同服务商的API差异
- 采用工厂模式创建适配器实例，便于扩展新模型
- 集成Token统计功能，支持成本分析
- 支持自定义base_url，兼容各类代理和私有部署

================================================================================
依赖要求
================================================================================
- langchain_openai: OpenAI兼容接口的LangChain封装
- openai: OpenAI官方SDK
- google.generativeai: Google Gemini SDK
- azure-ai-inference: Azure AI推理SDK
- tiktoken: Token计数工具（可选）

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from core.llm.base import (
    StreamChunk,
    UsageInfo,
    UsageExtractor,
    BaseLLMAdapter,
    TIKTOKEN_AVAILABLE,
)
from core.llm.utils import (
    set_global_tokens_manager,
    get_global_tokens_manager,
    estimate_tokens,
    record_token_usage,
    check_base_url,
)
from core.llm.factory import create_llm_adapter
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

__all__ = [
    "StreamChunk",
    "UsageInfo",
    "UsageExtractor",
    "BaseLLMAdapter",
    "TIKTOKEN_AVAILABLE",
    "set_global_tokens_manager",
    "get_global_tokens_manager",
    "estimate_tokens",
    "record_token_usage",
    "check_base_url",
    "create_llm_adapter",
    "DeepSeekAdapter",
    "OpenAIAdapter",
    "GeminiAdapter",
    "AzureOpenAIAdapter",
    "AzureAIAdapter",
    "OllamaAdapter",
    "MLStudioAdapter",
    "VolcanoEngineAIAdapter",
    "SiliconFlowAdapter",
    "GrokAdapter",
]
