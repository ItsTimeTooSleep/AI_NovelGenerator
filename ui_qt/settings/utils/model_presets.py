# -*- coding: utf-8 -*-
"""
AI Novel Generator - 模型预设管理器
==============================

本模块提供模型配置的预设管理功能，包括：
- 为不同接口格式提供默认的 Base URL
- 为不同接口格式提供推荐的模型名称
- 支持自动填充功能
"""

from typing import Dict, Optional, Tuple


class ModelPresetManager:
    """
    模型预设管理器

    管理各种模型接口格式的预设配置，包括默认 Base URL 和推荐模型名称。
    """

    # LLM 模型预设配置
    LLM_PRESETS = {
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4",
            "description": "OpenAI 官方 API",
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat",
            "description": "DeepSeek 官方 API",
        },
        "Azure OpenAI": {
            "base_url": "https://your-resource-name.openai.azure.com",
            "model_name": "gpt-4",
            "description": "Azure OpenAI 服务",
        },
        "Gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model_name": "gemini-pro",
            "description": "Google Gemini API",
        },
        "Ollama": {
            "base_url": "http://localhost:11434/v1",
            "model_name": "llama2",
            "description": "本地 Ollama 服务",
        },
        "ML Studio": {
            "base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat",
            "description": "ML Studio 兼容 API",
        },
        "SiliconFlow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model_name": "Qwen/Qwen2.5-7B-Instruct",
            "description": "硅基流动 API",
        },
        "Composer": {
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4",
            "description": "Composer 兼容 API",
        },
    }

    # Embedding 模型预设配置
    EMBEDDING_PRESETS = {
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "model_name": "text-embedding-ada-002",
            "description": "OpenAI 官方 Embedding API",
        },
        "Nvidia": {
            "base_url": "https://integrate.api.nvidia.com/v1/embeddings",
            "model_name": "nvidia/llama-nemotron-embed-vl-1b-v2",
            "description": "NVIDIA NIM Embedding API",
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "model_name": "text-embedding-ada-002",
            "description": "DeepSeek Embedding API",
        },
        "Azure OpenAI": {
            "base_url": "https://your-resource-name.openai.azure.com",
            "model_name": "text-embedding-ada-002",
            "description": "Azure OpenAI Embedding 服务",
        },
        "Gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model_name": "embedding-001",
            "description": "Google Gemini Embedding API",
        },
        "Ollama": {
            "base_url": "http://localhost:11434/v1",
            "model_name": "nomic-embed-text",
            "description": "本地 Ollama Embedding 服务",
        },
        "ML Studio": {
            "base_url": "https://api.deepseek.com/v1",
            "model_name": "text-embedding-ada-002",
            "description": "ML Studio 兼容 Embedding API",
        },
        "SiliconFlow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model_name": "BAAI/bge-large-zh-v1.5",
            "description": "硅基流动 Embedding API",
        },
    }

    @classmethod
    def get_llm_preset(cls, interface_format: str) -> Optional[Dict[str, str]]:
        """
        获取 LLM 模型的预设配置

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[Dict[str, str]]: 预设配置字典，包含 base_url、model_name 和 description，
                                    如果没有找到对应的预设则返回 None
        """
        return cls.LLM_PRESETS.get(interface_format)

    @classmethod
    def get_embedding_preset(cls, interface_format: str) -> Optional[Dict[str, str]]:
        """
        获取 Embedding 模型的预设配置

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[Dict[str, str]]: 预设配置字典，包含 base_url、model_name 和 description，
                                    如果没有找到对应的预设则返回 None
        """
        return cls.EMBEDDING_PRESETS.get(interface_format)

    @classmethod
    def get_llm_base_url(cls, interface_format: str) -> Optional[str]:
        """
        获取 LLM 模型的预设 Base URL

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[str]: 预设的 Base URL，如果没有找到则返回 None
        """
        preset = cls.get_llm_preset(interface_format)
        return preset.get("base_url") if preset else None

    @classmethod
    def get_embedding_base_url(cls, interface_format: str) -> Optional[str]:
        """
        获取 Embedding 模型的预设 Base URL

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[str]: 预设的 Base URL，如果没有找到则返回 None
        """
        preset = cls.get_embedding_preset(interface_format)
        return preset.get("base_url") if preset else None

    @classmethod
    def get_llm_model_name(cls, interface_format: str) -> Optional[str]:
        """
        获取 LLM 模型的预设模型名称

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[str]: 预设的模型名称，如果没有找到则返回 None
        """
        preset = cls.get_llm_preset(interface_format)
        return preset.get("model_name") if preset else None

    @classmethod
    def get_embedding_model_name(cls, interface_format: str) -> Optional[str]:
        """
        获取 Embedding 模型的预设模型名称

        Args:
            interface_format: 接口格式名称

        Returns:
            Optional[str]: 预设的模型名称，如果没有找到则返回 None
        """
        preset = cls.get_embedding_preset(interface_format)
        return preset.get("model_name") if preset else None

    @classmethod
    def get_llm_formats(cls) -> list:
        """
        获取所有支持的 LLM 接口格式列表

        Returns:
            list: 接口格式名称列表
        """
        return list(cls.LLM_PRESETS.keys())

    @classmethod
    def get_embedding_formats(cls) -> list:
        """
        获取所有支持的 Embedding 接口格式列表

        Returns:
            list: 接口格式名称列表
        """
        return list(cls.EMBEDDING_PRESETS.keys())

    @classmethod
    def suggest_llm_config(
        cls, interface_format: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        为 LLM 模型建议完整配置

        Args:
            interface_format: 接口格式名称

        Returns:
            Tuple[Optional[str], Optional[str]]: (base_url, model_name) 元组
        """
        preset = cls.get_llm_preset(interface_format)
        if preset:
            return (preset.get("base_url"), preset.get("model_name"))
        return (None, None)

    @classmethod
    def suggest_embedding_config(
        cls, interface_format: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        为 Embedding 模型建议完整配置

        Args:
            interface_format: 接口格式名称

        Returns:
            Tuple[Optional[str], Optional[str]]: (base_url, model_name) 元组
        """
        preset = cls.get_embedding_preset(interface_format)
        if preset:
            return (preset.get("base_url"), preset.get("model_name"))
        return (None, None)
