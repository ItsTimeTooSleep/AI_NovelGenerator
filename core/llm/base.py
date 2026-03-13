# -*- coding: utf-8 -*-
"""
LLM适配器基础组件模块

================================================================================
模块功能概述
================================================================================
本模块提供LLM适配器的基础组件，包括：
- StreamChunk: 流式响应数据块
- UsageInfo: Token使用信息数据结构
- UsageExtractor: Token使用信息提取器
- BaseLLMAdapter: LLM适配器基类

================================================================================
设计决策
================================================================================
- 使用适配器模式统一不同服务商的API差异
- Token使用信息提取器支持多种API提供商
- 流式响应数据块支持完整的token统计信息

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional, Callable, Generator

from core import get_logger


class StreamChunk:
    """
    流式响应数据块

    Attributes:
        content: 文本内容
        is_done: 是否完成
        input_tokens: 输入token数（仅最后一个chunk有效）
        output_tokens: 输出token数（仅最后一个chunk有效）
        cached_tokens: 缓存命中token数（仅最后一个chunk有效）
    """

    def __init__(
        self,
        content: str = "",
        is_done: bool = False,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
    ):
        self.content = content
        self.is_done = is_done
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cached_tokens = cached_tokens


try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    get_logger().warn(
        "llm_adapters", "tiktoken not available, using approximate token counting"
    )


class UsageInfo:
    """
    Token使用信息数据结构

    用于统一封装不同API提供商返回的token使用信息

    Attributes:
        input_tokens: 输入token数量
        output_tokens: 输出token数量
        cached_tokens: 缓存命中token数量
    """

    def __init__(
        self,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cached_tokens = cached_tokens

    def __repr__(self) -> str:
        return f"UsageInfo(input={self.input_tokens}, output={self.output_tokens}, cached={self.cached_tokens})"


class UsageExtractor:
    """
    Token使用信息提取器

    统一处理不同API提供商的usage信息提取，支持缓存命中token的识别。

    支持的API提供商及其usage字段格式：
    - DeepSeek: usage.prompt_tokens, usage.completion_tokens, usage.prompt_cache_hit_tokens
    - OpenAI (LangChain): usage_metadata.input_tokens, usage_metadata.output_tokens
    - OpenAI (原生): usage.prompt_tokens, usage.completion_tokens
    - Azure AI: usage.prompt_tokens, usage.completion_tokens
    - Gemini: usage_metadata.prompt_token_count, usage_metadata.candidates_token_count

    缓存命中字段命名：
    - DeepSeek: prompt_cache_hit_tokens
    - OpenAI (部分): cached_tokens (企业版特性)
    - 其他: 暂不支持缓存命中统计
    """

    PROVIDER_DEEPSEEK = "deepseek"
    PROVIDER_OPENAI = "openai"
    PROVIDER_AZURE_AI = "azure_ai"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_LANGCHAIN = "langchain"
    PROVIDER_GENERIC = "generic"

    @classmethod
    def extract(cls, response, provider: str = None) -> UsageInfo:
        """
        从API响应中提取token使用信息

        Args:
            response: API响应对象
            provider: API提供商标识，如果为None则自动检测

        Returns:
            UsageInfo: 统一的token使用信息对象
        """
        logger = get_logger()

        logger.debug("llm_adapters", "=" * 60)
        logger.debug("llm_adapters", "[DEBUG] AI原始响应对象信息:")
        logger.debug("llm_adapters", f"  响应类型: {type(response)}")
        logger.debug("llm_adapters", f"  响应属性列表: {dir(response)}")

        if hasattr(response, "__dict__"):
            logger.debug("llm_adapters", f"  响应__dict__: {response.__dict__}")

        if hasattr(response, "usage_metadata"):
            usage_meta = response.usage_metadata
            logger.debug("llm_adapters", f"  usage_metadata类型: {type(usage_meta)}")
            logger.debug("llm_adapters", f"  usage_metadata属性: {dir(usage_meta)}")
            logger.debug("llm_adapters", f"  usage_metadata值: {usage_meta}")

        if hasattr(response, "usage"):
            usage = response.usage
            logger.debug("llm_adapters", f"  usage类型: {type(usage)}")
            logger.debug("llm_adapters", f"  usage属性: {dir(usage)}")
            logger.debug("llm_adapters", f"  usage值: {usage}")

        if hasattr(response, "response_metadata"):
            resp_meta = response.response_metadata
            logger.debug("llm_adapters", f"  response_metadata: {resp_meta}")

        logger.debug("llm_adapters", "=" * 60)

        if provider is None:
            provider = cls._detect_provider(response)

        logger.debug("llm_adapters", f"[DEBUG] 检测到的提供商: {provider}")

        extractor_map = {
            cls.PROVIDER_DEEPSEEK: cls._extract_deepseek,
            cls.PROVIDER_OPENAI: cls._extract_openai,
            cls.PROVIDER_AZURE_AI: cls._extract_azure_ai,
            cls.PROVIDER_GEMINI: cls._extract_gemini,
            cls.PROVIDER_LANGCHAIN: cls._extract_langchain,
            cls.PROVIDER_GENERIC: cls._extract_generic,
        }

        extractor = extractor_map.get(provider, cls._extract_generic)
        result = extractor(response)

        logger.debug("llm_adapters", f"[DEBUG] 提取结果: {result}")
        logger.debug("llm_adapters", "=" * 60)

        return result

    @classmethod
    def _detect_provider(cls, response) -> str:
        """
        自动检测API提供商类型

        Args:
            response: API响应对象

        Returns:
            str: 提供商标识
        """
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            if hasattr(usage, "prompt_token_count"):
                return cls.PROVIDER_GEMINI

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict):
                model_name = metadata.get("model_name", "")
                if "deepseek" in model_name.lower():
                    return cls.PROVIDER_DEEPSEEK
                token_usage = metadata.get("token_usage", {})
                if (
                    isinstance(token_usage, dict)
                    and "prompt_cache_hit_tokens" in token_usage
                ):
                    return cls.PROVIDER_DEEPSEEK

        if hasattr(response, "usage"):
            usage = response.usage
            if hasattr(usage, "prompt_cache_hit_tokens"):
                return cls.PROVIDER_DEEPSEEK
            if hasattr(usage, "prompt_tokens"):
                if hasattr(usage, "completion_tokens"):
                    return cls.PROVIDER_OPENAI

        if hasattr(response, "usage_metadata"):
            return cls.PROVIDER_LANGCHAIN

        return cls.PROVIDER_GENERIC

    @classmethod
    def _extract_deepseek(cls, response) -> UsageInfo:
        """
        提取DeepSeek API的usage信息

        DeepSeek API返回格式（通过LangChain）：
        {
            "usage_metadata": {
                "input_tokens": 8509,
                "output_tokens": 4096,
                "total_tokens": 12605,
                "input_token_details": {"cache_read": 4096}
            },
            "response_metadata": {
                "token_usage": {
                    "prompt_tokens": 8509,
                    "completion_tokens": 4096,
                    "total_tokens": 12605,
                    "prompt_tokens_details": {"cached_tokens": 4096}
                },
                "model_name": "deepseek-chat"
            }
        }

        Args:
            response: DeepSeek API响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None
        cached_tokens = None

        if hasattr(response, "usage"):
            usage = response.usage
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)
            cached_tokens = getattr(usage, "prompt_cache_hit_tokens", None)

        if hasattr(response, "usage_metadata") and input_tokens is None:
            usage = response.usage_metadata
            if isinstance(usage, dict):
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                details = usage.get("input_token_details", {})
                if isinstance(details, dict):
                    cached_tokens = details.get("cache_read")
            else:
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None)
                if hasattr(usage, "input_token_details"):
                    details = getattr(usage, "input_token_details", {})
                    if isinstance(details, dict):
                        cached_tokens = details.get("cache_read")

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict) and "token_usage" in metadata:
                token_usage = metadata["token_usage"]
                if input_tokens is None:
                    input_tokens = token_usage.get("prompt_tokens")
                if output_tokens is None:
                    output_tokens = token_usage.get("completion_tokens")
                if cached_tokens is None:
                    cached_tokens = token_usage.get("prompt_cache_hit_tokens")
                if cached_tokens is None:
                    details = token_usage.get("prompt_tokens_details", {})
                    if isinstance(details, dict):
                        cached_tokens = details.get("cached_tokens")

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

    @classmethod
    def _extract_openai(cls, response) -> UsageInfo:
        """
        提取OpenAI API的usage信息

        OpenAI API返回格式：
        {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        注：OpenAI企业版可能包含 cached_tokens 字段

        Args:
            response: OpenAI API响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None
        cached_tokens = None

        if hasattr(response, "usage"):
            usage = response.usage
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)
            cached_tokens = getattr(usage, "cached_tokens", None)

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

    @classmethod
    def _extract_azure_ai(cls, response) -> UsageInfo:
        """
        提取Azure AI Inference API的usage信息

        Azure AI API返回格式：
        {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }

        Args:
            response: Azure AI API响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None

        if hasattr(response, "usage"):
            usage = response.usage
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=None,
        )

    @classmethod
    def _extract_gemini(cls, response) -> UsageInfo:
        """
        提取Google Gemini API的usage信息

        Gemini API返回格式：
        {
            "usage_metadata": {
                "prompt_token_count": 100,
                "candidates_token_count": 50,
                "total_token_count": 150
            }
        }

        Args:
            response: Gemini API响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=None,
        )

    @classmethod
    def _extract_langchain(cls, response) -> UsageInfo:
        """
        提取LangChain ChatOpenAI的usage信息

        LangChain封装的响应格式：
        {
            "usage_metadata": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            },
            "response_metadata": {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "prompt_cache_hit_tokens": 80
                }
            }
        }

        注：对于DeepSeek通过LangChain调用的情况，
        缓存命中信息可能需要在原始响应中查找

        Args:
            response: LangChain响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None
        cached_tokens = None

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata

            if isinstance(usage, dict):
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                cached_tokens = usage.get("prompt_cache_hit_tokens")
            else:
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None)

                if hasattr(usage, "prompt_cache_hit_tokens"):
                    cached_tokens = usage.prompt_cache_hit_tokens
                elif hasattr(usage, "input_token_details"):
                    details = getattr(usage, "input_token_details", {})
                    if isinstance(details, dict):
                        cached_tokens = details.get("cache_read")

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict) and "token_usage" in metadata:
                token_usage = metadata["token_usage"]
                if input_tokens is None:
                    input_tokens = token_usage.get("prompt_tokens")
                if output_tokens is None:
                    output_tokens = token_usage.get("completion_tokens")
                if cached_tokens is None:
                    cached_tokens = token_usage.get("prompt_cache_hit_tokens")
                if cached_tokens is None:
                    cached_tokens = token_usage.get("prompt_tokens_details", {}).get(
                        "cached_tokens"
                    )

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

    @classmethod
    def _extract_generic(cls, response) -> UsageInfo:
        """
        通用的usage信息提取方法

        尝试从响应对象中提取token使用信息，
        支持多种可能的字段命名方式。

        Args:
            response: API响应对象

        Returns:
            UsageInfo: token使用信息
        """
        input_tokens = None
        output_tokens = None
        cached_tokens = None

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata

            if isinstance(usage, dict):
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                cached_tokens = usage.get("prompt_cache_hit_tokens")

                if input_tokens is None:
                    input_tokens = usage.get("prompt_token_count")
                if output_tokens is None:
                    output_tokens = usage.get("candidates_token_count")
            else:
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None)
                cached_tokens = getattr(usage, "prompt_cache_hit_tokens", None)

                if input_tokens is None:
                    input_tokens = getattr(usage, "prompt_token_count", None)
                if output_tokens is None:
                    output_tokens = getattr(usage, "candidates_token_count", None)

        if hasattr(response, "usage") and input_tokens is None:
            usage = response.usage

            if isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens")
                output_tokens = usage.get("completion_tokens")

                if cached_tokens is None:
                    cached_tokens = usage.get("prompt_cache_hit_tokens")
                if cached_tokens is None:
                    cached_tokens = usage.get("cached_tokens")
            else:
                input_tokens = getattr(usage, "prompt_tokens", None)
                output_tokens = getattr(usage, "completion_tokens", None)

                if cached_tokens is None:
                    cached_tokens = getattr(usage, "prompt_cache_hit_tokens", None)
                if cached_tokens is None:
                    cached_tokens = getattr(usage, "cached_tokens", None)

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )


class BaseLLMAdapter:
    """
    统一的 LLM 接口基类，为不同后端（OpenAI、Ollama、ML Studio、Gemini等）提供一致的方法签名。
    """

    def invoke(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement .invoke(prompt) method.")

    def invoke_stream(
        self, prompt: str, on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> Generator[StreamChunk, None, None]:
        """
        流式调用LLM

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数，每次收到chunk时调用

        Yields:
            StreamChunk: 流式响应数据块
        """
        raise NotImplementedError(
            "Subclasses must implement .invoke_stream(prompt, on_chunk) method."
        )
