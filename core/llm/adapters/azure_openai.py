# -*- coding: utf-8 -*-
"""
Azure OpenAI适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供Azure OpenAI API的适配器实现。

================================================================================
核心类
================================================================================
- AzureOpenAIAdapter: Azure OpenAI API适配器

================================================================================
特性
================================================================================
- 支持流式和非流式调用
- 使用LangChain AzureChatOpenAI作为底层客户端
- 自动解析Azure OpenAI特定的URL格式

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import re
from typing import Optional, Callable, Generator

from langchain_openai import AzureChatOpenAI

from core.llm.base import BaseLLMAdapter, StreamChunk, UsageInfo, UsageExtractor
from core.llm.utils import record_token_usage
from core import get_logger


class AzureOpenAIAdapter(BaseLLMAdapter):
    """
    适配 Azure OpenAI 接口（使用 langchain.AzureChatOpenAI）

    Azure OpenAI使用特定的URL格式，需要从中提取endpoint、deployment和api-version。
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
        初始化Azure OpenAI适配器

        Args:
            api_key: API密钥
            base_url: Azure OpenAI URL（格式：https://{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}）
            model_name: 模型名称（实际使用deployment名称）
            max_tokens: 最大输出token数
            temperature: 温度参数
            timeout: 请求超时时间（秒）

        Raises:
            ValueError: 当base_url格式无效时抛出
        """
        self._logger = get_logger()
        match = re.match(
            r"https://(.+?)/openai/deployments/(.+?)/chat/completions\?api-version=(.+)",
            base_url,
        )
        if match:
            self.azure_endpoint = f"https://{match.group(1)}"
            self.azure_deployment = match.group(2)
            self.api_version = match.group(3)
        else:
            self._logger.error(
                "llm_adapters", f"无效的Azure OpenAI base_url格式: {base_url}"
            )
            raise ValueError("Invalid Azure OpenAI base_url format")

        self.api_key = api_key
        self.model_name = self.azure_deployment
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._logger.debug(
            "llm_adapters",
            f"AzureOpenAIAdapter初始化: endpoint={self.azure_endpoint}, deployment={self.azure_deployment}",
        )

        self._client = AzureChatOpenAI(
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        """
        非流式调用Azure OpenAI API

        Args:
            prompt: 输入提示词

        Returns:
            完整的响应文本
        """
        self._logger.debug(
            "llm_adapters",
            f"AzureOpenAIAdapter调用: deployment={self.azure_deployment}, 提示词长度={len(prompt)}",
        )
        response = self._client.invoke(prompt)
        if not response:
            self._logger.warn("llm_adapters", "AzureOpenAIAdapter未获取到响应")
            return ""
        result = response.content

        usage_info = UsageExtractor.extract(response, UsageExtractor.PROVIDER_LANGCHAIN)

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
        流式调用Azure OpenAI API

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数

        Yields:
            StreamChunk: 流式响应数据块
        """
        self._logger.debug(
            "llm_adapters",
            f"AzureOpenAIAdapter流式调用: deployment={self.azure_deployment}, 提示词长度={len(prompt)}",
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
                usage_info = UsageExtractor.extract(
                    last_chunk, UsageExtractor.PROVIDER_LANGCHAIN
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
            self._logger.error("llm_adapters", f"AzureOpenAIAdapter流式调用失败: {e}")
            error_chunk = StreamChunk(content="", is_done=True)
            yield error_chunk
