# -*- coding: utf-8 -*-
"""
LLM适配器集合

================================================================================
模块功能概述
================================================================================
本模块导出所有LLM适配器类，便于统一导入。

================================================================================
支持的适配器
================================================================================
- DeepSeekAdapter: DeepSeek API适配器
- OpenAIAdapter: OpenAI API适配器
- GeminiAdapter: Google Gemini API适配器
- AzureOpenAIAdapter: Azure OpenAI API适配器
- AzureAIAdapter: Azure AI Inference API适配器
- OllamaAdapter: Ollama本地模型适配器
- MLStudioAdapter: ML Studio本地开发环境适配器
- VolcanoEngineAIAdapter: 火山引擎API适配器
- SiliconFlowAdapter: 硅基流动API适配器
- GrokAdapter: xAI Grok API适配器

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from core.llm.adapters.deepseek import DeepSeekAdapter
from core.llm.adapters.openai import OpenAIAdapter
from core.llm.adapters.gemini import GeminiAdapter
from core.llm.adapters.azure_openai import AzureOpenAIAdapter
from core.llm.adapters.azure_ai import AzureAIAdapter
from core.llm.adapters.ollama import OllamaAdapter
from core.llm.adapters.ml_studio import MLStudioAdapter
from core.llm.adapters.volcano_engine import VolcanoEngineAIAdapter
from core.llm.adapters.silicon_flow import SiliconFlowAdapter
from core.llm.adapters.grok import GrokAdapter

__all__ = [
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
