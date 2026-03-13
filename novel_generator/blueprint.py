# -*- coding: utf-8 -*-
"""
章节蓝图生成模块

================================================================================
模块功能概述
================================================================================
本模块负责生成小说的章节蓝图（章节目录），定义每章的定位、作用、悬念等元信息。
支持一次性生成和分块生成两种模式，适应不同规模的小说创作需求。

================================================================================
核心函数
================================================================================
- Chapter_blueprint_generate: 章节蓝图生成主函数（生成器）
- compute_chunk_size: 计算分块生成时的块大小
- limit_chapter_blueprint: 限制蓝图长度，避免prompt过长

================================================================================
生成策略
================================================================================
1. 小规模小说（章节数<=块大小）：一次性生成全部章节蓝图
2. 大规模小说（章节数>块大小）：分块生成，每次生成若干章节
3. 断点续传：检测已有蓝图，从最后章节继续生成

================================================================================
设计决策
================================================================================
- 根据max_tokens自动计算分块大小
- 保留最近100章目录作为上下文，平衡信息量和prompt长度
- 生成结果保存到Novel_directory.txt
- 使用生成器模式实现进度反馈

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import re

from core.llm import create_llm_adapter
from core.prompt_definitions import (
    chapter_blueprint_prompt,
    chunked_chapter_blueprint_prompt,
)
from core.utils import clear_file_content, read_file, save_string_to_txt
from core import get_logger
from novel_generator.common import invoke_with_cleaning

logger = get_logger()


def compute_chunk_size(number_of_chapters: int, max_tokens: int) -> int:
    """
    基于"每章约100 tokens"的粗略估算，
    再结合当前max_tokens，计算分块大小：
      chunk_size = (floor(max_tokens/100/10)*10) - 10
    并确保 chunk_size 不会小于1或大于实际章节数。
    """
    tokens_per_chapter = 200.0
    ratio = max_tokens / tokens_per_chapter
    ratio_rounded_to_10 = int(ratio // 10) * 10
    chunk_size = ratio_rounded_to_10 - 10
    if chunk_size < 1:
        chunk_size = 1
    if chunk_size > number_of_chapters:
        chunk_size = number_of_chapters
    return chunk_size


def limit_chapter_blueprint(blueprint_text: str, limit_chapters: int = 100) -> str:
    """
    从已有章节目录中只取最近的 limit_chapters 章，以避免 prompt 超长。
    """
    pattern = r"(第\s*\d+\s*章.*?)(?=第\s*\d+\s*章|$)"
    chapters = re.findall(pattern, blueprint_text, flags=re.DOTALL)
    if not chapters:
        return blueprint_text
    if len(chapters) <= limit_chapters:
        return blueprint_text
    selected = chapters[-limit_chapters:]
    return "\n\n".join(selected).strip()


def Chapter_blueprint_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    number_of_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = 600,
):
    """
    章节蓝图生成主函数（生成器）

    若 Novel_directory.txt 已存在且内容非空，则表示可能是之前的部分生成结果；
      解析其中已有的章节数，从下一个章节继续分块生成；
      对于已有章节目录，传入时仅保留最近100章目录，避免prompt过长。
    否则：
      - 若章节数 <= chunk_size，直接一次性生成
      - 若章节数 > chunk_size，进行分块生成
    生成完成后输出至 Novel_directory.txt。

    Yields:
        (step_index, total_steps, step_name, status_msg): 进度信息
    """
    logger.info("blueprint", f"开始生成章节蓝图，目标章节数: {number_of_chapters}")

    total_steps = 1
    step_name = "章节目录生成"

    yield (0, total_steps, "初始化", "正在初始化生成环境...")

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if not os.path.exists(arch_file):
        logger.warn("blueprint", "Novel_architecture.txt不存在，请先生成架构")
        yield (1, total_steps, step_name, "生成失败：缺少架构文件")
        return

    architecture_text = read_file(arch_file).strip()
    if not architecture_text:
        logger.warn("blueprint", "Novel_architecture.txt为空")
        yield (1, total_steps, step_name, "生成失败：架构文件为空")
        return

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    filename_dir = os.path.join(filepath, "Novel_directory.txt")
    existing_blueprint = ""
    if os.path.exists(filename_dir):
        existing_blueprint = read_file(filename_dir).strip()
    chunk_size = compute_chunk_size(number_of_chapters, max_tokens)
    logger.debug("blueprint", f"章节数={number_of_chapters}, 计算块大小={chunk_size}")

    if existing_blueprint:
        logger.info("blueprint", "检测到已有蓝图内容，将从断点继续生成")
        pattern = r"第\s*(\d+)\s*章"
        existing_chapter_numbers = re.findall(pattern, existing_blueprint)
        existing_chapter_numbers = [
            int(x) for x in existing_chapter_numbers if x.isdigit()
        ]
        max_existing_chap = (
            max(existing_chapter_numbers) if existing_chapter_numbers else 0
        )
        logger.debug("blueprint", f"已有蓝图包含至第{max_existing_chap}章")
        final_blueprint = existing_blueprint
        current_start = max_existing_chap + 1

        total_chunks = (
            number_of_chapters - max_existing_chap + chunk_size - 1
        ) // chunk_size
        chunk_index = 0

        while current_start <= number_of_chapters:
            current_end = min(current_start + chunk_size - 1, number_of_chapters)
            chunk_index += 1

            yield (
                chunk_index,
                total_chunks,
                step_name,
                f"正在生成章节 [{current_start}..{current_end}]...",
            )

            limited_blueprint = limit_chapter_blueprint(final_blueprint, 100)
            chunk_prompt = chunked_chapter_blueprint_prompt.format(
                novel_architecture=architecture_text,
                chapter_list=limited_blueprint,
                number_of_chapters=number_of_chapters,
                n=current_start,
                m=current_end,
                user_guidance=user_guidance,
            )
            logger.info("blueprint", f"生成章节 [{current_start}..{current_end}]")
            chunk_result = invoke_with_cleaning(llm_adapter, chunk_prompt)
            if not chunk_result.strip():
                logger.warn(
                    "blueprint", f"章节 [{current_start}..{current_end}] 生成结果为空"
                )
                clear_file_content(filename_dir)
                save_string_to_txt(final_blueprint.strip(), filename_dir)
                yield (chunk_index, total_chunks, step_name, "生成失败：部分章节为空")
                return
            final_blueprint += "\n\n" + chunk_result.strip()
            clear_file_content(filename_dir)
            save_string_to_txt(final_blueprint.strip(), filename_dir)
            current_start = current_end + 1

        logger.info("blueprint", "所有章节蓝图生成完成(断点续传模式)")
        yield (total_chunks, total_chunks, step_name, "完成")
        return

    if chunk_size >= number_of_chapters:
        logger.debug("blueprint", "使用一次性生成模式")
        yield (1, total_steps, step_name, "正在生成章节目录...")

        prompt = chapter_blueprint_prompt.format(
            novel_architecture=architecture_text,
            number_of_chapters=number_of_chapters,
            user_guidance=user_guidance,
        )
        blueprint_text = invoke_with_cleaning(llm_adapter, prompt)
        if not blueprint_text.strip():
            logger.warn("blueprint", "章节蓝图生成结果为空")
            yield (1, total_steps, step_name, "生成失败：结果为空")
            return

        clear_file_content(filename_dir)
        save_string_to_txt(blueprint_text, filename_dir)
        logger.info("blueprint", "章节蓝图生成成功(一次性模式)")
        yield (1, total_steps, step_name, "完成")
        return

    logger.info("blueprint", "使用分块生成模式")
    final_blueprint = ""
    current_start = 1

    total_chunks = (number_of_chapters + chunk_size - 1) // chunk_size

    while current_start <= number_of_chapters:
        current_end = min(current_start + chunk_size - 1, number_of_chapters)
        chunk_index = (current_start - 1) // chunk_size + 1

        yield (
            chunk_index,
            total_chunks,
            step_name,
            f"正在生成章节 [{current_start}..{current_end}]...",
        )

        limited_blueprint = limit_chapter_blueprint(final_blueprint, 100)
        chunk_prompt = chunked_chapter_blueprint_prompt.format(
            novel_architecture=architecture_text,
            chapter_list=limited_blueprint,
            number_of_chapters=number_of_chapters,
            n=current_start,
            m=current_end,
            user_guidance=user_guidance,
        )
        logger.info("blueprint", f"生成章节 [{current_start}..{current_end}]")
        chunk_result = invoke_with_cleaning(llm_adapter, chunk_prompt)
        if not chunk_result.strip():
            logger.warn(
                "blueprint", f"章节 [{current_start}..{current_end}] 生成结果为空"
            )
            clear_file_content(filename_dir)
            save_string_to_txt(final_blueprint.strip(), filename_dir)
            yield (chunk_index, total_chunks, step_name, "生成失败：部分章节为空")
            return
        if final_blueprint.strip():
            final_blueprint += "\n\n" + chunk_result.strip()
        else:
            final_blueprint = chunk_result.strip()
        clear_file_content(filename_dir)
        save_string_to_txt(final_blueprint.strip(), filename_dir)
        current_start = current_end + 1

    logger.info("blueprint", "章节蓝图生成成功(分块模式)")
    yield (total_chunks, total_chunks, step_name, "完成")
