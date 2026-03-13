# -*- coding: utf-8 -*-
"""
Azure AI适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供Azure AI Inference API的适配器实现，用于访问Azure AI服务部署的模型。

================================================================================
核心类
================================================================================
- AzureAIAdapter: Azure AI Inference API适配器

================================================================================
特性
================================================================================
- 支持流式和非流式调用
- 使用azure-ai-inference SDK
- 支持Azure AI服务部署的各类模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import re
from typing import Optional, Callable, Generator

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from core.llm.base import BaseLLMAdapter, StreamChunk, UsageInfo, UsageExtractor
from core.llm.utils import record_token_usage
from core import get_logger


class AzureAIAdapter(BaseLLMAdapter):
    """
    适配 Azure AI Inference 接口，用于访问Azure AI服务部署的模型

    使用azure-ai-inference库进行API调用。
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
        初始化Azure AI适配器

        Args:
            api_key: API密钥
            base_url: Azure AI URL（格式：https://{endpoint}.services.ai.azure.com/models/chat/completions?api-version={version}）
            model_name: 模型名称
            max_tokens: 最大输出token数
            temperature: 温度参数
            timeout: 请求超时时间（秒）

        Raises:
            ValueError: 当base_url格式无效时抛出
        """
        self._logger = get_logger()
        match = re.match(
            r"https://(.+?)\.services\.ai\.azure\.com(?:/models)?(?:/chat/completions)?(?:\?api-version=(.+))?",
            base_url,
        )
        if match:
            self.endpoint = f"https://{match.group(1)}.services.ai.azure.com/models"
            self.api_version = (
                match.group(2) if match.group(2) else "2024-05-01-preview"
            )
        else:
            self._logger.error(
                "llm_adapters", f"无效的Azure AI base_url格式: {base_url}"
            )
            raise ValueError(
                "Invalid Azure AI base_url format. Expected format: https://<endpoint>.services.ai.azure.com/models/chat/completions?api-version=xxx"
            )

        self.base_url = self.endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._logger.debug(
            "llm_adapters",
            f"AzureAIAdapter初始化: endpoint={self.endpoint}, 模型={model_name}",
        )

        self._client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        """
        非流式调用Azure AI Inference API

        Args:
            prompt: 输入提示词

        Returns:
            完整的响应文本
        """
        self._logger.debug(
            "llm_adapters",
            f"AzureAIAdapter调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )
        try:
            response = self._client.complete(
                messages=[
                    SystemMessage("You are a helpful assistant."),
                    UserMessage(prompt),
                ]
            )
            if response and response.choices:
                result = response.choices[0].message.content

                usage_info = UsageExtractor.extract(
                    response, UsageExtractor.PROVIDER_AZURE_AI
                )

                record_token_usage(
                    model_name=self.model_name,
                    prompt=prompt,
                    response=result,
                    input_tokens=usage_info.input_tokens,
                    output_tokens=usage_info.output_tokens,
                    cached_tokens=usage_info.cached_tokens or 0,
                )

                return result
            else:
                self._logger.warn("llm_adapters", "AzureAIAdapter未获取到响应")
                return ""
        except Exception as e:
            self._logger.error("llm_adapters", f"Azure AI Inference API调用失败: {e}")
            return ""

    def invoke_stream(
        self, prompt: str, on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> Generator[StreamChunk, None, None]:
        """
        流式调用Azure AI Inference API

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数

        Yields:
            StreamChunk: 流式响应数据块
        """
        self._logger.debug(
            "llm_adapters",
            f"AzureAIAdapter流式调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )

        full_content = ""
        usage_info = UsageInfo()

        try:
            response = self._client.complete(
                stream=True,
                messages=[
                    SystemMessage("You are a helpful assistant."),
                    UserMessage(prompt),
                ],
            )

            for chunk in response:
                if chunk and chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        full_content += content
                        stream_chunk = StreamChunk(content=content, is_done=False)
                        if on_chunk:
                            on_chunk(stream_chunk)
                        yield stream_chunk

            usage_info = UsageExtractor.extract(
                response, UsageExtractor.PROVIDER_AZURE_AI
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
            self._logger.error("llm_adapters", f"AzureAIAdapter流式调用失败: {e}")
            error_chunk = StreamChunk(content="", is_done=True)
            yield error_chunk
