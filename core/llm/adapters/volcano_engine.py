# -*- coding: utf-8 -*-
"""
火山引擎适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供火山引擎（字节跳动云服务）模型API的适配器实现。

================================================================================
核心类
================================================================================
- VolcanoEngineAIAdapter: 火山引擎API适配器

================================================================================
特性
================================================================================
- 支持流式和非流式调用
- 使用OpenAI原生SDK
- 支持火山引擎部署的各类模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional, Callable, Generator

from openai import OpenAI

from core.llm.base import BaseLLMAdapter, StreamChunk, UsageInfo, UsageExtractor
from core.llm.utils import record_token_usage, check_base_url
from core import get_logger


class VolcanoEngineAIAdapter(BaseLLMAdapter):
    """
    适配火山引擎（字节跳动云服务）API

    使用OpenAI原生SDK进行API调用。
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
        初始化火山引擎适配器

        Args:
            api_key: API密钥
            base_url: 火山引擎API地址
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
            f"VolcanoEngineAIAdapter初始化: 模型={model_name}, base_url={self.base_url}",
        )

        self._client = OpenAI(
            base_url=self.base_url, api_key=self.api_key, timeout=self.timeout
        )

    def invoke(self, prompt: str) -> str:
        """
        非流式调用火山引擎API

        Args:
            prompt: 输入提示词

        Returns:
            完整的响应文本
        """
        self._logger.debug(
            "llm_adapters",
            f"VolcanoEngineAIAdapter调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是DeepSeek，是一个 AI 人工智能助手",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=self.timeout,
            )
            if not response:
                self._logger.warn("llm_adapters", "VolcanoEngineAIAdapter未获取到响应")
                return ""
            result = response.choices[0].message.content

            usage_info = UsageExtractor.extract(
                response, UsageExtractor.PROVIDER_OPENAI
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
        except Exception as e:
            self._logger.error("llm_adapters", f"火山引擎API调用超时或失败: {e}")
            return ""

    def invoke_stream(
        self, prompt: str, on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> Generator[StreamChunk, None, None]:
        """
        流式调用火山引擎API

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数

        Yields:
            StreamChunk: 流式响应数据块
        """
        self._logger.debug(
            "llm_adapters",
            f"VolcanoEngineAIAdapter流式调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )

        full_content = ""
        usage_info = UsageInfo()

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是DeepSeek，是一个 AI 人工智能助手",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                timeout=self.timeout,
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
                response, UsageExtractor.PROVIDER_OPENAI
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
            self._logger.error(
                "llm_adapters", f"VolcanoEngineAIAdapter流式调用失败: {e}"
            )
            error_chunk = StreamChunk(content="", is_done=True)
            yield error_chunk
