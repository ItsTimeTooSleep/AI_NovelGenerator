# -*- coding: utf-8 -*-
"""
DeepSeek适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供DeepSeek API的适配器实现，支持缓存命中token统计。

================================================================================
核心类
================================================================================
- DeepSeekAdapter: DeepSeek API适配器

================================================================================
特性
================================================================================
- 支持流式和非流式调用
- 支持缓存命中token统计（prompt_cache_hit_tokens）
- 使用LangChain ChatOpenAI作为底层客户端

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional, Callable, Generator

from langchain_openai import ChatOpenAI

from core.llm.base import BaseLLMAdapter, StreamChunk, UsageInfo, UsageExtractor
from core.llm.utils import record_token_usage, check_base_url
from core import get_logger


class DeepSeekAdapter(BaseLLMAdapter):
    """
    适配DeepSeek API（使用 langchain.ChatOpenAI）

    DeepSeek API支持缓存命中token统计，通过prompt_cache_hit_tokens字段返回。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        """
        初始化DeepSeek适配器

        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
            max_tokens: 最大输出token数
            temperature: 温度参数
            timeout: 请求超时时间（秒）
        """
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._logger = get_logger()

        self._logger.debug(
            "llm_adapters",
            f"DeepSeekAdapter初始化: 模型={model_name}, base_url={self.base_url}",
        )

        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        """
        非流式调用DeepSeek API

        Args:
            prompt: 输入提示词

        Returns:
            完整的响应文本
        """
        self._logger.debug(
            "llm_adapters",
            f"DeepSeekAdapter调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )
        response = self._client.invoke(prompt)

        self._logger.debug("llm_adapters", "=" * 60)
        self._logger.debug("llm_adapters", "[DEBUG] DeepSeek非流式响应原始对象:")
        self._logger.debug("llm_adapters", f"  响应类型: {type(response)}")
        if hasattr(response, "__dict__"):
            self._logger.debug("llm_adapters", f"  响应__dict__: {response.__dict__}")
        if hasattr(response, "response_metadata"):
            self._logger.debug(
                "llm_adapters", f"  response_metadata: {response.response_metadata}"
            )
        self._logger.debug("llm_adapters", "=" * 60)

        if not response:
            self._logger.warn("llm_adapters", "DeepSeekAdapter未获取到响应")
            return ""
        result = response.content

        usage_info = UsageExtractor.extract(response, UsageExtractor.PROVIDER_DEEPSEEK)

        record_token_usage(
            model_name=self.model_name,
            prompt=prompt,
            response=result,
            input_tokens=usage_info.input_tokens,
            output_tokens=usage_info.output_tokens,
            cached_tokens=usage_info.cached_tokens or 0,
        )

        return result

    def invoke_stream(
        self, prompt: str, on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> Generator[StreamChunk, None, None]:
        """
        流式调用DeepSeek API

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数

        Yields:
            StreamChunk: 流式响应数据块
        """
        self._logger.debug(
            "llm_adapters",
            f"DeepSeekAdapter流式调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )

        full_content = ""
        usage_info = UsageInfo()
        last_chunk = None

        try:
            for chunk in self._client.stream(prompt):
                last_chunk = chunk
                if chunk and chunk.content:
                    content = chunk.content
                    full_content += content
                    stream_chunk = StreamChunk(content=content, is_done=False)
                    if on_chunk:
                        on_chunk(stream_chunk)
                    yield stream_chunk

            if last_chunk is not None:
                self._logger.debug("llm_adapters", "=" * 60)
                self._logger.debug(
                    "llm_adapters", "[DEBUG] DeepSeek流式响应最后一个chunk原始对象:"
                )
                self._logger.debug(
                    "llm_adapters", f"  last_chunk类型: {type(last_chunk)}"
                )
                if hasattr(last_chunk, "__dict__"):
                    self._logger.debug(
                        "llm_adapters", f"  last_chunk__dict__: {last_chunk.__dict__}"
                    )
                if hasattr(last_chunk, "response_metadata"):
                    self._logger.debug(
                        "llm_adapters",
                        f"  response_metadata: {last_chunk.response_metadata}",
                    )
                self._logger.debug("llm_adapters", "=" * 60)

                usage_info = UsageExtractor.extract(
                    last_chunk, UsageExtractor.PROVIDER_DEEPSEEK
                )

            record_token_usage(
                model_name=self.model_name,
                prompt=prompt,
                response=full_content,
                input_tokens=usage_info.input_tokens,
                output_tokens=usage_info.output_tokens,
                cached_tokens=usage_info.cached_tokens or 0,
            )

            final_chunk = StreamChunk(
                content="",
                is_done=True,
                input_tokens=usage_info.input_tokens,
                output_tokens=usage_info.output_tokens,
                cached_tokens=usage_info.cached_tokens,
            )
            if on_chunk:
                on_chunk(final_chunk)
            yield final_chunk

        except Exception as e:
            self._logger.error("llm_adapters", f"DeepSeekAdapter流式调用失败: {e}")
            error_chunk = StreamChunk(content="", is_done=True)
            yield error_chunk
