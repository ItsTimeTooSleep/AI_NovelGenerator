# -*- coding: utf-8 -*-
"""
通用工具函数模块

================================================================================
模块功能概述
================================================================================
本模块提供小说生成过程中常用的工具函数，包括：
- LLM调用重试机制
- 响应文本清理
- 调试日志记录

================================================================================
核心函数
================================================================================
- call_with_retry: 通用重试封装函数
- remove_think_tags: 移除AI思考过程标签
- debug_log: 记录提示词和响应到日志
- invoke_with_cleaning: 调用LLM并清理响应
- invoke_stream_with_cleaning: 流式调用LLM并清理响应

================================================================================
设计决策
================================================================================
- 使用重试机制提高API调用稳定性
- 清理响应中的特殊格式标记，确保内容纯净
- 日志记录便于问题排查和效果分析
- 支持流式和非流式两种调用方式

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import logging
import re
import time
import traceback
from typing import Callable, Optional, Generator

from core.llm import StreamChunk

# 导入Token管理相关模块
try:
    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TOKEN_MANAGER_AVAILABLE = False

logging.basicConfig(
    filename="app.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def call_with_retry(func, max_retries=3, sleep_time=2, fallback_return=None, **kwargs):
    """
    通用的重试机制封装。
    :param func: 要执行的函数
    :param max_retries: 最大重试次数
    :param sleep_time: 重试前的等待秒数
    :param fallback_return: 如果多次重试仍失败时的返回值（如果为None则抛出异常）
    :param kwargs: 传给func的命名参数
    :return: func的结果，若失败则返回 fallback_return 或抛出异常
    :raises: Exception: 当重试次数用尽且fallback_return为None时抛出最后一次异常
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return func(**kwargs)
        except Exception as e:
            last_exception = e
            logging.warning(
                f"[call_with_retry] Attempt {attempt} failed with error: {e}"
            )
            traceback.print_exc()
            if attempt < max_retries:
                time.sleep(sleep_time)

    logging.error("Max retries reached.")
    if fallback_return is not None:
        return fallback_return
    else:
        raise last_exception


def remove_think_tags(text: str) -> str:
    """移除 <think>...</think> 包裹的内容"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


def debug_log(prompt: str, response_content: str):
    logging.info(
        f"\n[#########################################  Prompt  #########################################]\n{prompt}\n"
    )
    logging.info(
        f"\n[######################################### Response #########################################]\n{response_content}\n"
    )


def invoke_with_cleaning(llm_adapter, prompt: str, max_retries: int = 3) -> str:
    """
    调用 LLM 并清理返回结果

    Args:
        llm_adapter: LLM适配器实例
        prompt: 输入提示词
        max_retries: 最大重试次数

    Returns:
        清理后的响应文本
    """
    print("\n" + "=" * 50)
    print("发送到 LLM 的提示词:")
    print("-" * 50)
    print(prompt)
    print("=" * 50 + "\n")

    result = ""
    retry_count = 0

    while retry_count < max_retries:
        try:
            result = llm_adapter.invoke(prompt)
            print("\n" + "=" * 50)
            print("LLM 返回的内容:")
            print("-" * 50)
            print(result)
            print("=" * 50 + "\n")

            result = result.replace("```", "").strip()
            if result:
                return result
            retry_count += 1
        except Exception as e:
            print(f"调用失败 ({retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                raise e

    return result


def invoke_stream_with_cleaning(
    llm_adapter,
    prompt: str,
    on_chunk: Optional[Callable[[str], None]] = None,
    max_retries: int = 3,
) -> Generator[str, None, None]:
    """
    流式调用 LLM 并清理返回结果

    Args:
        llm_adapter: LLM适配器实例
        prompt: 输入提示词
        on_chunk: 可选的回调函数，每次收到chunk时调用
        max_retries: 最大重试次数

    Yields:
        清理后的响应文本片段
    """
    print("\n" + "=" * 50)
    print("发送到 LLM 的提示词 (流式):")
    print("-" * 50)
    print(prompt)
    print("=" * 50 + "\n")

    retry_count = 0

    while retry_count < max_retries:
        try:
            full_result = ""
            for chunk in llm_adapter.invoke_stream(prompt):
                if chunk.content:
                    cleaned_content = chunk.content.replace("```", "")
                    full_result += chunk.content
                    if on_chunk:
                        on_chunk(cleaned_content)
                    yield cleaned_content

                if chunk.is_done:
                    print("\n" + "=" * 50)
                    print("LLM 流式返回完成")
                    print("-" * 50)
                    print(f"总长度: {len(full_result)}")
                    print("=" * 50 + "\n")
                    return

        except Exception as e:
            print(f"流式调用失败 ({retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                raise e

    yield ""
