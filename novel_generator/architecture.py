# -*- coding: utf-8 -*-
"""
小说架构生成模块

================================================================================
模块功能概述
================================================================================
本模块负责生成小说的整体架构，包括核心种子、角色动力学、世界观和情节架构。
采用雪花写作法从核心到细节逐步展开，支持断点续传。

================================================================================
核心函数
================================================================================
- Novel_architecture_generate: 小说架构生成主函数（生成器）
- load_partial_architecture_data: 加载阶段性生成数据
- save_partial_architecture_data: 保存阶段性生成数据

================================================================================
生成步骤
================================================================================
Step 1: 核心种子 - 故事核心单句概括
Step 2: 角色动力学 - 角色设计与关系网络
Step 3: 初始角色状态 - 角色属性初始化
Step 4: 世界观 - 物理/社会/隐喻三维世界
Step 5: 情节架构 - 三幕式剧情结构

================================================================================
设计决策
================================================================================
- 使用生成器模式实现进度反馈
- 支持断点续传，中断后可从上次位置继续
- 生成结果保存到Novel_architecture.txt和character_state.txt

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json
import os

from core.llm import create_llm_adapter
from core.prompt_definitions import (
    character_dynamics_prompt,
    core_seed_prompt,
    create_character_state_prompt,
    plot_architecture_prompt,
    title_generation_prompt,
    world_building_prompt,
)
from core.utils import clear_file_content, save_string_to_txt
from novel_generator.common import invoke_with_cleaning

try:
    from core import get_logger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

if LOGGER_AVAILABLE:
    logger = get_logger()
else:
    logger = None


def load_partial_architecture_data(filepath: str) -> dict:
    """
    从 filepath 下的 partial_architecture.json 读取已有的阶段性数据。
    如果文件不存在或无法解析，返回空 dict。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    if not os.path.exists(partial_file):
        return {}
    try:
        with open(partial_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        if logger:
            logger.warn("architecture", f"加载 partial_architecture.json 失败: {e}")
        return {}


def save_partial_architecture_data(filepath: str, data: dict):
    """
    将阶段性数据写入 partial_architecture.json。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    try:
        with open(partial_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        if logger:
            logger.warn("architecture", f"保存 partial_architecture.json 失败: {e}")


def Novel_architecture_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    title: str,
    topic: str,
    genre: str,
    number_of_chapters: int,
    word_number: int,
    filepath: str,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
):
    """
    这是一个生成器函数，依次生成小说架构的各个部分。
    Yields:
        (step_index, total_steps, step_name, status_msg, extra_data)
        extra_data: 可选的额外数据字典，用于传递生成的书名等信息

    依次调用:
      0. title_generation_prompt (仅当 title 为空时)
      1. core_seed_prompt
      2. character_dynamics_prompt
      3. world_building_prompt
      4. plot_architecture_prompt
    若在中间任何一步报错且重试多次失败，则将已经生成的内容写入 partial_architecture.json 并退出；
    下次调用时可从该步骤继续。
    最终输出 Novel_architecture.txt

    新增：
    - 在完成角色动力学设定后，依据该角色体系，使用 create_character_state_prompt 生成初始角色状态表，
      并存储到 character_state.txt，后续维护更新。
    - 支持书名自动生成：当 title 为空时，自动调用 LLM 生成书名
    """
    if logger:
        logger.info(
            "architecture", f"开始生成小说架构，书名: {title if title else '(待生成)'}"
        )

    total_steps = 6

    yield (0, total_steps, "初始化", "正在初始化生成环境...", None)

    os.makedirs(filepath, exist_ok=True)
    partial_data = load_partial_architecture_data(filepath)
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    if logger:
        logger.debug("architecture", f"LLM适配器创建成功，模型: {llm_model}")

    # Step 0: 书名生成（仅当 title 为空或为临时名称时）
    step_name = "书名生成"
    generated_title = None
    need_generate_title = (
        not title or not title.strip() or title.startswith("未命名小说_")
    )
    if need_generate_title:
        yield (1, total_steps, step_name, "正在生成书名...", None)
        if "generated_title" not in partial_data:
            if logger:
                logger.info("architecture", "Step0: 开始生成书名")
            prompt_title = title_generation_prompt.format(
                topic=topic,
                genre=genre,
                user_guidance=user_guidance,
            )
            title_result = invoke_with_cleaning(llm_adapter, prompt_title)
            if not title_result.strip():
                if logger:
                    logger.error("architecture", "书名生成失败，返回空内容")
                save_partial_architecture_data(filepath, partial_data)
                yield (1, total_steps, step_name, "生成失败", None)
                return
            generated_title = title_result.strip()
            partial_data["generated_title"] = generated_title
            save_partial_architecture_data(filepath, partial_data)
            if logger:
                logger.info("architecture", f"书名生成完成: {generated_title}")
        else:
            generated_title = partial_data["generated_title"]
            if logger:
                logger.debug(
                    "architecture", f"Step0 已完成，跳过，书名: {generated_title}"
                )
        title = generated_title
        yield (1, total_steps, step_name, "完成", {"generated_title": generated_title})
    else:
        if logger:
            logger.debug("architecture", "书名已存在，跳过书名生成步骤")

    # Step1: 核心种子
    step_name = "核心种子生成"
    yield (2, total_steps, step_name, "正在生成核心种子...", None)
    if "core_seed_result" not in partial_data:
        if logger:
            logger.info("architecture", "Step1: 开始生成核心种子")
        prompt_core = core_seed_prompt.format(
            title=title,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            user_guidance=user_guidance,
        )
        core_seed_result = invoke_with_cleaning(llm_adapter, prompt_core)
        if not core_seed_result.strip():
            if logger:
                logger.error("architecture", "核心种子生成失败，返回空内容")
            save_partial_architecture_data(filepath, partial_data)
            yield (2, total_steps, step_name, "生成失败", None)
            return
        partial_data["core_seed_result"] = core_seed_result
        save_partial_architecture_data(filepath, partial_data)
        if logger:
            logger.info("architecture", "核心种子生成完成")
    else:
        if logger:
            logger.debug("architecture", "Step1 已完成，跳过")
    yield (2, total_steps, step_name, "完成", None)

    # Step2: 角色动力学
    step_name = "角色动力学构建"
    yield (3, total_steps, step_name, "正在构建角色动力学...", None)
    if "character_dynamics_result" not in partial_data:
        if logger:
            logger.info("architecture", "Step2: 开始构建角色动力学")
        prompt_character = character_dynamics_prompt.format(
            title=title,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=user_guidance,
        )
        character_dynamics_result = invoke_with_cleaning(llm_adapter, prompt_character)
        if not character_dynamics_result.strip():
            if logger:
                logger.error("architecture", "角色动力学构建失败")
            save_partial_architecture_data(filepath, partial_data)
            yield (3, total_steps, step_name, "生成失败", None)
            return
        partial_data["character_dynamics_result"] = character_dynamics_result
        save_partial_architecture_data(filepath, partial_data)
        if logger:
            logger.info("architecture", "角色动力学构建完成")
    else:
        if logger:
            logger.debug("architecture", "Step2 已完成，跳过")
    yield (3, total_steps, step_name, "完成", None)

    # Step3: 初始角色状态
    step_name = "初始角色状态生成"
    yield (4, total_steps, step_name, "正在生成初始角色状态...", None)
    if (
        "character_dynamics_result" in partial_data
        and "character_state_result" not in partial_data
    ):
        if logger:
            logger.info("architecture", "开始生成初始角色状态")
        prompt_char_state_init = create_character_state_prompt.format(
            character_dynamics=partial_data["character_dynamics_result"].strip()
        )
        character_state_init = invoke_with_cleaning(llm_adapter, prompt_char_state_init)
        if not character_state_init.strip():
            if logger:
                logger.error("architecture", "初始角色状态生成失败")
            save_partial_architecture_data(filepath, partial_data)
            yield (4, total_steps, step_name, "生成失败", None)
            return
        partial_data["character_state_result"] = character_state_init
        character_state_file = os.path.join(filepath, "character_state.txt")
        clear_file_content(character_state_file)
        save_string_to_txt(character_state_init, character_state_file)
        save_partial_architecture_data(filepath, partial_data)
        if logger:
            logger.info("architecture", "初始角色状态创建并保存成功")
    else:
        if logger:
            logger.debug("architecture", "角色状态已完成，跳过")
    yield (4, total_steps, step_name, "完成", None)

    # Step4: 世界观
    step_name = "世界观搭建"
    yield (5, total_steps, step_name, "正在搭建世界观...", None)
    if "world_building_result" not in partial_data:
        if logger:
            logger.info("architecture", "Step3: 开始搭建世界观")
        prompt_world = world_building_prompt.format(
            title=title,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=user_guidance,
        )
        world_building_result = invoke_with_cleaning(llm_adapter, prompt_world)
        if not world_building_result.strip():
            if logger:
                logger.error("architecture", "世界观搭建失败")
            save_partial_architecture_data(filepath, partial_data)
            yield (5, total_steps, step_name, "生成失败", None)
            return
        partial_data["world_building_result"] = world_building_result
        save_partial_architecture_data(filepath, partial_data)
        if logger:
            logger.info("architecture", "世界观搭建完成")
    else:
        if logger:
            logger.debug("architecture", "Step5 已完成，跳过")
    yield (5, total_steps, step_name, "完成", None)

    # Step5: 三幕式情节
    step_name = "情节架构设计"
    yield (6, total_steps, step_name, "正在设计情节架构...", None)
    if "plot_arch_result" not in partial_data:
        if logger:
            logger.info("architecture", "Step4: 开始设计情节架构")
        prompt_plot = plot_architecture_prompt.format(
            title=title,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            core_seed=partial_data["core_seed_result"].strip(),
            character_dynamics=partial_data["character_dynamics_result"].strip(),
            world_building=partial_data["world_building_result"].strip(),
            user_guidance=user_guidance,
        )
        plot_arch_result = invoke_with_cleaning(llm_adapter, prompt_plot)
        if not plot_arch_result.strip():
            if logger:
                logger.error("architecture", "情节架构设计失败")
            save_partial_architecture_data(filepath, partial_data)
            yield (6, total_steps, step_name, "生成失败", None)
            return
        partial_data["plot_arch_result"] = plot_arch_result
        save_partial_architecture_data(filepath, partial_data)
        if logger:
            logger.info("architecture", "情节架构设计完成")
    else:
        if logger:
            logger.debug("architecture", "Step4 已完成，跳过")
    yield (6, total_steps, step_name, "完成", None)

    core_seed_result = partial_data["core_seed_result"]
    character_dynamics_result = partial_data["character_dynamics_result"]
    world_building_result = partial_data["world_building_result"]
    plot_arch_result = partial_data["plot_arch_result"]

    final_content = (
        "#=== 0) 小说设定 ===\n"
        f"书名：{title},主题：{topic},类型：{genre},篇幅：约{number_of_chapters}章（每章{word_number}字）\n\n"
        "#=== 1) 核心种子 ===\n"
        f"{core_seed_result}\n\n"
        "#=== 2) 角色动力学 ===\n"
        f"{character_dynamics_result}\n\n"
        "#=== 3) 世界观 ===\n"
        f"{world_building_result}\n\n"
        "#=== 4) 三幕式情节架构 ===\n"
        f"{plot_arch_result}\n"
    )

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    clear_file_content(arch_file)
    save_string_to_txt(final_content, arch_file)
    if logger:
        logger.info(
            "architecture", f"Novel_architecture.txt 生成成功，路径: {filepath}"
        )

    # 保留 partial_architecture.json 文件，以便 UI 可以读取各步骤的原始 LLM 响应
    # partial_arch_file = os.path.join(filepath, "partial_architecture.json")
    # if os.path.exists(partial_arch_file):
    #     os.remove(partial_arch_file)
    #     if logger:
    #         logger.info("architecture", "partial_architecture.json 已删除（所有步骤完成）")
    if logger:
        logger.info("architecture", "小说架构生成流程完成")
