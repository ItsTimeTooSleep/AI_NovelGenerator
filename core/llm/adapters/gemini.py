# -*- coding: utf-8 -*-
"""
Gemini适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供Google Gemini API的适配器实现。

================================================================================
核心类
================================================================================
- GeminiAdapter: Google Gemini API适配器

================================================================================
特性
================================================================================
- 支持流式和非流式调用
- 使用google.generativeai SDK
- 支持Gemini系列模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from typing import Optional, Callable, Generator

import google.generativeai as genai

from core.llm.base import BaseLLMAdapter, StreamChunk, UsageInfo, UsageExtractor
from core.llm.utils import record_token_usage
from core import get_logger


class GeminiAdapter(BaseLLMAdapter):
    """
    适配 Google Gemini (Google Generative AI) 接口

    使用google.generativeai SDK进行API调用。
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
        初始化Gemini适配器

        Args:
            api_key: API密钥
            base_url: API基础URL（Gemini不使用此参数）
            model_name: 模型名称
            max_tokens: 最大输出token数
            temperature: 温度参数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._logger = get_logger()

        self._logger.debug("llm_adapters", f"GeminiAdapter初始化: 模型={model_name}")

        genai.configure(api_key=self.api_key)

        self._model = genai.GenerativeModel(model_name=self.model_name)

    def invoke(self, prompt: str) -> str:
        """
        非流式调用Gemini API

        Args:
            prompt: 输入提示词

        Returns:
            完整的响应文本
        """
        self._logger.debug(
            "llm_adapters",
            f"GeminiAdapter调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            response = self._model.generate_content(
                prompt, generation_config=generation_config
            )

            if response and response.text:
                result = response.text

                usage_info = UsageExtractor.extract(
                    response, UsageExtractor.PROVIDER_GEMINI
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
                self._logger.warn("llm_adapters", "GeminiAdapter未获取到文本响应")
                return ""
        except Exception as e:
            self._logger.error("llm_adapters", f"Gemini API调用失败: {e}")
            return ""

    def invoke_stream(
        self, prompt: str, on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> Generator[StreamChunk, None, None]:
        """
        流式调用Gemini API

        Args:
            prompt: 输入提示词
            on_chunk: 可选的回调函数

        Yields:
            StreamChunk: 流式响应数据块
        """
        self._logger.debug(
            "llm_adapters",
            f"GeminiAdapter流式调用: 模型={self.model_name}, 提示词长度={len(prompt)}",
        )

        full_content = ""
        usage_info = UsageInfo()

        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            response = self._model.generate_content(
                prompt, generation_config=generation_config, stream=True
            )

            for chunk in response:
                if chunk and chunk.text:
                    content = chunk.text
                    full_content += content
                    stream_chunk = StreamChunk(content=content, is_done=False)
                    if on_chunk:
                        on_chunk(stream_chunk)
                    yield stream_chunk

            usage_info = UsageExtractor.extract(
                response, UsageExtractor.PROVIDER_GEMINI
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
            self._logger.error("llm_adapters", f"GeminiAdapter流式调用失败: {e}")
            error_chunk = StreamChunk(content="", is_done=True)
            yield error_chunk
