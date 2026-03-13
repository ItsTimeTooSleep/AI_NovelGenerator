# -*- coding: utf-8 -*-
"""
章节草稿生成模块

================================================================================
模块功能概述
================================================================================
本模块负责生成小说章节的正文内容，是小说创作的核心环节。
集成知识库检索、摘要生成、上下文管理等功能，确保章节内容连贯且有深度。

================================================================================
核心函数
================================================================================
- build_chapter_prompt: 构建章节生成提示词
- generate_chapter_draft: 生成章节草稿
- summarize_recent_chapters: 生成当前章节摘要
- get_filtered_knowledge_context: 获取过滤后的知识库内容

================================================================================
生成流程
================================================================================
1. 第一章：直接基于小说设定生成
2. 后续章节：
   - 获取前3章内容和摘要
   - 知识库检索相关内容
   - 构建完整提示词
   - 调用LLM生成正文

================================================================================
知识库应用规则
================================================================================
- 优先使用写作技法类知识
- 历史章节内容需改写30%以上
- 近3章内容跳过，避免重复

================================================================================
设计决策
================================================================================
- 第一章特殊处理，无需前文摘要
- 知识库检索结果经过过滤和规则处理
- 支持自定义提示词覆盖

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import re

from core.chapter_directory_parser import get_chapter_info_from_blueprint
from core.llm import create_llm_adapter
from core.prompt_definitions import (
    first_chapter_draft_prompt,
    knowledge_filter_prompt,
    knowledge_search_prompt,
    next_chapter_draft_prompt,
    summarize_recent_chapters_prompt,
)
from core.utils import clear_file_content, read_file, save_string_to_txt
from core import get_logger
from novel_generator.common import invoke_with_cleaning, invoke_stream_with_cleaning
from novel_generator.vectorstore_utils import get_relevant_context_from_vector_store
from novel_generator.vectorstore_utils import load_vector_store

logger = get_logger()


def build_optional_elements_section(
    characters_involved: str,
    key_items: str,
    scene_location: str,
    time_constraint: str,
) -> str:
    """
    构建可选元素部分，若用户未输入则自动剔除对应字段。

    Args:
        characters_involved: 核心人物（用户手动输入，可能为空）
        key_items: 关键道具（用户手动输入，可能为空）
        scene_location: 场景地点（用户手动输入，可能为空）
        time_constraint: 时间压力（用户手动输入，可能为空）

    Returns:
        str: 格式化的可选元素部分字符串，若全部为空则返回空字符串
    """
    elements = []

    if characters_involved and characters_involved.strip():
        elements.append(f"├── 核心人物：{characters_involved.strip()}")
    if key_items and key_items.strip():
        elements.append(f"├── 关键道具：{key_items.strip()}")
    if scene_location and scene_location.strip():
        elements.append(f"├── 场景地点：{scene_location.strip()}")
    if time_constraint and time_constraint.strip():
        elements.append(f"└── 时间压力：{time_constraint.strip()}")

    if not elements:
        return ""

    if len(elements) > 0:
        elements[-1] = elements[-1].replace("├──", "└──", 1)

    return "【可用元素】\n" + "\n".join(elements) + "\n"


def build_user_guidance_section(user_guidance: str) -> str:
    """
    构建用户指导部分，若用户未输入则自动剔除。

    Args:
        user_guidance: 用户指导（用户手动输入，可能为空）

    Returns:
        str: 格式化的用户指导部分字符串，若为空则返回空字符串
    """
    if user_guidance and user_guidance.strip():
        return f"【用户指导】\n{user_guidance.strip()}\n"
    return ""


def get_last_n_chapters_text(
    chapters_dir: str, current_chapter_num: int, n: int = 3
) -> list:
    """
    从目录 chapters_dir 中获取最近 n 章的文本内容，返回文本列表。
    """
    texts = []
    start_chap = max(1, current_chapter_num - n)
    for c in range(start_chap, current_chapter_num):
        chap_file = os.path.join(chapters_dir, f"chapter_{c}.txt")
        if os.path.exists(chap_file):
            text = read_file(chap_file).strip()
            texts.append(text)
        else:
            texts.append("")
    return texts


def summarize_recent_chapters(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    chapters_text_list: list,
    novel_number: int,
    chapter_info: dict,
    next_chapter_info: dict,
    timeout: int = 600,
) -> str:
    """
    根据前三章内容生成当前章节的精准摘要。
    如果解析失败，则返回空字符串。
    """
    try:
        combined_text = "\n".join(chapters_text_list).strip()
        if not combined_text:
            return ""

        max_combined_length = 4000
        if len(combined_text) > max_combined_length:
            combined_text = combined_text[-max_combined_length:]

        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        chapter_info = chapter_info or {}
        next_chapter_info = next_chapter_info or {}

        prompt = summarize_recent_chapters_prompt.format(
            combined_text=combined_text,
            novel_number=novel_number,
            chapter_title=chapter_info.get("chapter_title", "未命名"),
            chapter_role=chapter_info.get("chapter_role", "常规章节"),
            chapter_purpose=chapter_info.get("chapter_purpose", "内容推进"),
            suspense_level=chapter_info.get("suspense_level", "中等"),
            foreshadowing=chapter_info.get("foreshadowing", "无"),
            plot_twist_level=chapter_info.get("plot_twist_level", "★☆☆☆☆"),
            chapter_summary=chapter_info.get("chapter_summary", ""),
            next_chapter_number=novel_number + 1,
            next_chapter_title=next_chapter_info.get("chapter_title", "（未命名）"),
            next_chapter_role=next_chapter_info.get("chapter_role", "过渡章节"),
            next_chapter_purpose=next_chapter_info.get("chapter_purpose", "承上启下"),
            next_chapter_summary=next_chapter_info.get(
                "chapter_summary", "衔接过渡内容"
            ),
            next_chapter_suspense_level=next_chapter_info.get("suspense_level", "中等"),
            next_chapter_foreshadowing=next_chapter_info.get(
                "foreshadowing", "无特殊伏笔"
            ),
            next_chapter_plot_twist_level=next_chapter_info.get(
                "plot_twist_level", "★☆☆☆☆"
            ),
        )

        response_text = invoke_with_cleaning(llm_adapter, prompt)
        summary = extract_summary_from_response(response_text)

        if not summary:
            logger.warn("chapter", "提取摘要失败，使用完整响应")
            return response_text[:2000]

        logger.debug("chapter", f"章节摘要生成成功，长度: {len(summary)}")
        return summary[:2000]

    except Exception as e:
        logger.error("chapter", f"生成章节摘要失败: {str(e)}")
        return ""


def extract_summary_from_response(response_text: str) -> str:
    """从响应文本中提取摘要部分"""
    if not response_text:
        return ""

    # 查找摘要标记
    summary_markers = ["当前章节摘要:", "章节摘要:", "摘要:", "本章摘要:"]

    for marker in summary_markers:
        if marker in response_text:
            parts = response_text.split(marker, 1)
            if len(parts) > 1:
                return parts[1].strip()

    return response_text.strip()


def format_chapter_info(chapter_info: dict) -> str:
    """将章节信息字典格式化为文本"""
    template = """
章节编号：第{number}章
章节标题：《{title}》
章节定位：{role}
核心作用：{purpose}
主要人物：{characters}
关键道具：{items}
场景地点：{location}
伏笔设计：{foreshadow}
悬念密度：{suspense}
转折程度：{twist}
章节简述：{summary}
"""
    return template.format(
        number=chapter_info.get("chapter_number", "未知"),
        title=chapter_info.get("chapter_title", "未知"),
        role=chapter_info.get("chapter_role", "未知"),
        purpose=chapter_info.get("chapter_purpose", "未知"),
        characters=chapter_info.get("characters_involved", "未指定"),
        items=chapter_info.get("key_items", "未指定"),
        location=chapter_info.get("scene_location", "未指定"),
        foreshadow=chapter_info.get("foreshadowing", "无"),
        suspense=chapter_info.get("suspense_level", "一般"),
        twist=chapter_info.get("plot_twist_level", "★☆☆☆☆"),
        summary=chapter_info.get("chapter_summary", "未提供"),
    )


def parse_search_keywords(response_text: str) -> list:
    """解析新版关键词格式（示例输入：'科技公司·数据泄露\n地下实验室·基因编辑'）"""
    return [
        line.strip().replace("·", " ")
        for line in response_text.strip().split("\n")
        if "·" in line
    ][
        :5
    ]  # 最多取5组


def apply_content_rules(texts: list, novel_number: int) -> list:
    """应用内容处理规则"""
    processed = []
    for text in texts:
        if re.search(r"第[\d]+章", text) or re.search(r"chapter_[\d]+", text):
            chap_nums = list(map(int, re.findall(r"\d+", text)))
            recent_chap = max(chap_nums) if chap_nums else 0
            time_distance = novel_number - recent_chap

            if time_distance <= 2:
                processed.append(f"[SKIP] 跳过近章内容：{text[:120]}...")
            elif 3 <= time_distance <= 5:
                processed.append(f"[MOD40%] {text}（需修改≥40%）")
            else:
                processed.append(f"[OK] {text}（可引用核心）")
        else:
            processed.append(f"[PRIOR] {text}（优先使用）")
    return processed


def apply_knowledge_rules(contexts: list, chapter_num: int) -> list:
    """应用知识库使用规则"""
    processed = []
    for text in contexts:
        # 检测历史章节内容
        if "第" in text and "章" in text:
            # 提取章节号判断时间远近
            chap_nums = [int(s) for s in text.split() if s.isdigit()]
            recent_chap = max(chap_nums) if chap_nums else 0
            time_distance = chapter_num - recent_chap

            # 相似度处理规则
            if time_distance <= 3:  # 近三章内容
                processed.append(f"[历史章节限制] 跳过近期内容: {text[:50]}...")
                continue

            # 允许引用但需要转换
            processed.append(f"[历史参考] {text} (需进行30%以上改写)")
        else:
            # 第三方知识优先处理
            processed.append(f"[外部知识] {text}")
    return processed


def get_filtered_knowledge_context(
    api_key: str,
    base_url: str,
    model_name: str,
    interface_format: str,
    embedding_adapter,
    filepath: str,
    chapter_info: dict,
    retrieved_texts: list,
    max_tokens: int = 2048,
    timeout: int = 600,
) -> str:
    """优化后的知识过滤处理"""
    if not retrieved_texts:
        return "（无相关知识库内容）"

    try:
        processed_texts = apply_knowledge_rules(
            retrieved_texts, chapter_info.get("chapter_number", 0)
        )
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=0.3,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        formatted_texts = []
        max_text_length = 600
        for i, text in enumerate(processed_texts, 1):
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            formatted_texts.append(f"[预处理结果{i}]\n{text}")

        formatted_chapter_info = (
            f"当前章节定位：{chapter_info.get('chapter_role', '')}\n"
            f"核心目标：{chapter_info.get('chapter_purpose', '')}\n"
            f"关键要素：{chapter_info.get('characters_involved', '')} | "
            f"{chapter_info.get('key_items', '')} | "
            f"{chapter_info.get('scene_location', '')}"
        )

        prompt = knowledge_filter_prompt.format(
            chapter_info=formatted_chapter_info,
            retrieved_texts=(
                "\n\n".join(formatted_texts) if formatted_texts else "（无检索结果）"
            ),
        )

        filtered_content = invoke_with_cleaning(llm_adapter, prompt)
        logger.debug(
            "chapter",
            f"知识库内容过滤完成，输入: {len(retrieved_texts)}条，输出长度: {len(filtered_content) if filtered_content else 0}",
        )
        return filtered_content if filtered_content else "（知识内容过滤失败）"

    except Exception as e:
        logger.error("chapter", f"知识库过滤错误: {str(e)}")
        return "（内容过滤过程出错）"


def build_chapter_prompt(
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    novel_number: int,
    word_number: int,
    temperature: float,
    user_guidance: str,
    characters_involved: str,
    key_items: str,
    scene_location: str,
    time_constraint: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    embedding_retrieval_k: int = 2,
    interface_format: str = "openai",
    max_tokens: int = 2048,
    timeout: int = 600,
) -> str:
    """
    构造当前章节的请求提示词（完整实现版）
    修改重点：
    1. 优化知识库检索流程
    2. 新增内容重复检测机制
    3. 集成提示词应用规则
    """
    logger.info("chapter", f"开始构建章节提示词: 第{novel_number}章")

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    novel_architecture_text = read_file(arch_file)
    directory_file = os.path.join(filepath, "Novel_directory.txt")
    blueprint_text = read_file(directory_file)
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary_text = read_file(global_summary_file)
    character_state_file = os.path.join(filepath, "character_state.txt")
    character_state_text = read_file(character_state_file)

    chapter_info = get_chapter_info_from_blueprint(blueprint_text, novel_number)
    chapter_title = chapter_info["chapter_title"]
    chapter_role = chapter_info["chapter_role"]
    chapter_purpose = chapter_info["chapter_purpose"]
    suspense_level = chapter_info["suspense_level"]
    foreshadowing = chapter_info["foreshadowing"]
    plot_twist_level = chapter_info["plot_twist_level"]
    chapter_summary = chapter_info["chapter_summary"]

    next_chapter_number = novel_number + 1
    next_chapter_info = get_chapter_info_from_blueprint(
        blueprint_text, next_chapter_number
    )
    next_chapter_title = next_chapter_info.get("chapter_title", "（未命名）")
    next_chapter_role = next_chapter_info.get("chapter_role", "过渡章节")
    next_chapter_purpose = next_chapter_info.get("chapter_purpose", "承上启下")
    next_chapter_suspense = next_chapter_info.get("suspense_level", "中等")
    next_chapter_foreshadow = next_chapter_info.get("foreshadowing", "无特殊伏笔")
    next_chapter_twist = next_chapter_info.get("plot_twist_level", "★☆☆☆☆")
    next_chapter_summary = next_chapter_info.get("chapter_summary", "衔接过渡内容")

    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    if novel_number == 1:
        logger.info("chapter", "第一章特殊处理，直接返回初始章节提示词")
        optional_elements = build_optional_elements_section(
            characters_involved, key_items, scene_location, time_constraint
        )
        user_guidance_section = build_user_guidance_section(user_guidance)
        return first_chapter_draft_prompt.format(
            novel_number=novel_number,
            word_number=word_number,
            chapter_title=chapter_title,
            chapter_role=chapter_role,
            chapter_purpose=chapter_purpose,
            suspense_level=suspense_level,
            foreshadowing=foreshadowing,
            plot_twist_level=plot_twist_level,
            chapter_summary=chapter_summary,
            optional_elements=optional_elements,
            user_guidance_section=user_guidance_section,
            novel_setting=novel_architecture_text,
        )

    recent_texts = get_last_n_chapters_text(chapters_dir, novel_number, n=3)

    try:
        logger.debug("chapter", "开始生成前文摘要")
        short_summary = summarize_recent_chapters(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            chapters_text_list=recent_texts,
            novel_number=novel_number,
            chapter_info=chapter_info,
            next_chapter_info=next_chapter_info,
            timeout=timeout,
        )
        logger.debug("chapter", "前文摘要生成成功")
    except Exception as e:
        logger.error("chapter", f"生成前文摘要失败: {str(e)}")
        short_summary = "（摘要生成失败）"

    previous_excerpt = ""
    for text in reversed(recent_texts):
        if text.strip():
            previous_excerpt = text[-800:] if len(text) > 800 else text
            break

    try:
        from core.embedding_adapters import create_embedding_adapter

        embedding_adapter = create_embedding_adapter(
            embedding_interface_format,
            embedding_api_key,
            embedding_url,
            embedding_model_name,
        )

        store = load_vector_store(embedding_adapter, filepath)

        if store and store._collection.count() > 0:
            logger.debug(
                "chapter",
                f"向量库存在，记录数: {store._collection.count()}，开始知识库检索",
            )
            llm_adapter = create_llm_adapter(
                interface_format=interface_format,
                base_url=base_url,
                model_name=model_name,
                api_key=api_key,
                temperature=0.3,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            search_prompt = knowledge_search_prompt.format(
                chapter_number=novel_number,
                chapter_title=chapter_title,
                characters_involved=characters_involved,
                key_items=key_items,
                scene_location=scene_location,
                chapter_role=chapter_role,
                chapter_purpose=chapter_purpose,
                foreshadowing=foreshadowing,
                short_summary=short_summary,
                user_guidance=user_guidance,
                time_constraint=time_constraint,
            )

            search_response = invoke_with_cleaning(llm_adapter, search_prompt)
            keyword_groups = parse_search_keywords(search_response)

            all_contexts = []
            collection_size = store._collection.count()
            actual_k = min(embedding_retrieval_k, max(1, collection_size))

            for group in keyword_groups:
                try:
                    context = get_relevant_context_from_vector_store(
                        embedding_adapter=embedding_adapter,
                        query=group,
                        filepath=filepath,
                        k=actual_k,
                    )
                    if context:
                        if any(kw in group.lower() for kw in ["技法", "手法", "模板"]):
                            all_contexts.append(f"[TECHNIQUE] {context}")
                        elif any(kw in group.lower() for kw in ["设定", "技术", "世界观"]):
                            all_contexts.append(f"[SETTING] {context}")
                        else:
                            all_contexts.append(f"[GENERAL] {context}")
                except Exception as e:
                    logger.error("chapter", f"检索关键词 '{group}' 时发生错误: {str(e)}")
                    continue

            processed_contexts = apply_content_rules(all_contexts, novel_number)

            chapter_info_for_filter = {
                "chapter_number": novel_number,
                "chapter_title": chapter_title,
                "chapter_role": chapter_role,
                "chapter_purpose": chapter_purpose,
                "characters_involved": characters_involved,
                "key_items": key_items,
                "scene_location": scene_location,
                "foreshadowing": foreshadowing,
                "suspense_level": suspense_level,
                "plot_twist_level": plot_twist_level,
                "chapter_summary": chapter_summary,
                "time_constraint": time_constraint,
            }

            filtered_context = get_filtered_knowledge_context(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
                interface_format=interface_format,
                embedding_adapter=embedding_adapter,
                filepath=filepath,
                chapter_info=chapter_info_for_filter,
                retrieved_texts=processed_contexts,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            logger.debug(
                "chapter", f"知识库检索完成，获取上下文: {len(filtered_context)}字符"
            )
        else:
            filtered_context = "（无知识库内容或知识库未创建）"
            logger.debug("chapter", "向量库不存在或为空，跳过知识库检索")

    except Exception as e:
        logger.error("chapter", f"知识处理流程异常: {str(e)}")
        import traceback
        traceback.print_exc()
        filtered_context = "（知识库处理失败）"

    optional_elements = build_optional_elements_section(
        characters_involved, key_items, scene_location, time_constraint
    )
    user_guidance_section = build_user_guidance_section(user_guidance)

    logger.info("chapter", f"章节提示词构建完成: 第{novel_number}章《{chapter_title}》")
    return next_chapter_draft_prompt.format(
        novel_architecture=novel_architecture_text,
        chapter_blueprint=blueprint_text,
        user_guidance_section=user_guidance_section,
        global_summary=global_summary_text,
        previous_chapter_excerpt=previous_excerpt,
        character_state=character_state_text,
        short_summary=short_summary,
        novel_number=novel_number,
        chapter_title=chapter_title,
        chapter_role=chapter_role,
        chapter_purpose=chapter_purpose,
        suspense_level=suspense_level,
        foreshadowing=foreshadowing,
        plot_twist_level=plot_twist_level,
        chapter_summary=chapter_summary,
        word_number=word_number,
        optional_elements=optional_elements,
        next_chapter_number=next_chapter_number,
        next_chapter_title=next_chapter_title,
        next_chapter_role=next_chapter_role,
        next_chapter_purpose=next_chapter_purpose,
        next_chapter_summary=next_chapter_summary,
        filtered_context=filtered_context,
    )


def generate_chapter_draft(
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    novel_number: int,
    word_number: int,
    temperature: float,
    user_guidance: str,
    characters_involved: str,
    key_items: str,
    scene_location: str,
    time_constraint: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    embedding_retrieval_k: int = 2,
    interface_format: str = "openai",
    max_tokens: int = 2048,
    timeout: int = 600,
    custom_prompt_text: str = None,
    _stream_callback=None,
) -> str:
    """
    生成章节草稿，支持自定义提示词和流式输出

    Args:
        api_key: API密钥
        base_url: API基础URL
        model_name: 模型名称
        filepath: 项目路径
        novel_number: 章节号
        word_number: 目标字数
        temperature: 温度参数
        user_guidance: 用户指导
        characters_involved: 涉及角色
        key_items: 关键物品
        scene_location: 场景位置
        time_constraint: 时间约束
        embedding_api_key: Embedding API密钥
        embedding_url: Embedding URL
        embedding_interface_format: Embedding接口格式
        embedding_model_name: Embedding模型名称
        embedding_retrieval_k: 检索数量
        interface_format: 接口格式
        max_tokens: 最大token数
        timeout: 超时时间
        custom_prompt_text: 自定义提示词
        _stream_callback: 流式回调函数（内部使用）

    Returns:
        str: 生成的章节内容
    """
    logger.info("chapter", f"开始生成章节草稿: 第{novel_number}章")

    if custom_prompt_text is None:
        prompt_text = build_chapter_prompt(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            filepath=filepath,
            novel_number=novel_number,
            word_number=word_number,
            temperature=temperature,
            user_guidance=user_guidance,
            characters_involved=characters_involved,
            key_items=key_items,
            scene_location=scene_location,
            time_constraint=time_constraint,
            embedding_api_key=embedding_api_key,
            embedding_url=embedding_url,
            embedding_interface_format=embedding_interface_format,
            embedding_model_name=embedding_model_name,
            embedding_retrieval_k=embedding_retrieval_k,
            interface_format=interface_format,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    else:
        prompt_text = custom_prompt_text
        logger.debug("chapter", "使用自定义提示词")

    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    if _stream_callback:
        chapter_content = ""
        for chunk in invoke_stream_with_cleaning(llm_adapter, prompt_text):
            chapter_content += chunk
            _stream_callback(chunk)
    else:
        chapter_content = invoke_with_cleaning(llm_adapter, prompt_text)

    if not chapter_content.strip():
        logger.warn("chapter", f"第{novel_number}章草稿生成内容为空")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    clear_file_content(chapter_file)
    save_string_to_txt(chapter_content, chapter_file)
    logger.info("chapter", f"第{novel_number}章草稿生成完成，保存至: {chapter_file}")
    return chapter_content
