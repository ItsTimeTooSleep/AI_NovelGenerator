# -*- coding: utf-8 -*-
"""
章节定稿处理模块

================================================================================
模块功能概述
================================================================================
本模块负责章节的最终处理工作，包括更新全局摘要、更新角色状态、
将章节内容存入向量库等。定稿后的章节将作为后续章节的上下文参考。

================================================================================
核心函数
================================================================================
- finalize_chapter: 章节定稿主函数
- enrich_chapter_text: 章节扩写函数

================================================================================
定稿流程
================================================================================
1. 读取章节草稿内容
2. 备份原文件（global_summary.txt, character_state.txt）
3. 更新全局摘要（global_summary.txt）
4. 更新角色状态（character_state.txt）
5. 将章节内容向量化存入知识库
6. 如果任何步骤失败，恢复备份文件

================================================================================
事务性保存机制
================================================================================
- 定稿操作采用事务性保存，确保原子性
- 在修改任何文件前，先备份原文件
- 如果任何步骤失败，自动恢复所有备份文件
- 向量库更新失败时，不影响摘要和角色状态的更新（已保存的不可回滚）

================================================================================
设计决策
================================================================================
- 定稿操作不可逆，确保章节质量后再执行
- 向量库更新可选，支持禁用Embedding功能
- 扩写功能独立，可在定稿前单独调用

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import shutil

from core.embedding_adapters import create_embedding_adapter
from core.llm import create_llm_adapter
from core.prompt_definitions import summary_prompt, update_character_state_prompt
from core.utils import clear_file_content, read_file, save_string_to_txt
from core import get_logger
from novel_generator.common import invoke_with_cleaning
from novel_generator.vectorstore_utils import update_vector_store

logger = get_logger()


class FinalizationError(Exception):
    """
    定稿过程中的错误异常

    参数:
        message: 错误信息
        step: 失败的步骤名称

    属性:
        step: 失败的步骤名称
    """

    def __init__(self, message: str, step: str = ""):
        super().__init__(message)
        self.step = step


class BackupManager:
    """
    文件备份管理器

    负责在定稿过程中备份和恢复文件，确保事务性操作。

    参数:
        filepath: 项目路径

    属性:
        filepath: 项目路径
        backups: 备份文件路径字典 {原文件路径: 备份文件路径}
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.backups: dict = {}

    def backup_file(self, file_path: str) -> bool:
        """
        备份单个文件

        参数:
            file_path: 要备份的文件路径

        返回值:
            bool: 备份是否成功

        设计说明:
            - 如果文件不存在，创建空备份标记
            - 备份文件存放在项目路径下的 .backup 临时目录
        """
        if not os.path.exists(file_path):
            self.backups[file_path] = None
            return True

        backup_dir = os.path.join(self.filepath, ".backup_temp")
        os.makedirs(backup_dir, exist_ok=True)

        backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}.bak")

        try:
            shutil.copy2(file_path, backup_path)
            self.backups[file_path] = backup_path
            logger.debug("finalization", f"已备份文件: {file_path} -> {backup_path}")
            return True
        except Exception as e:
            logger.error("finalization", f"备份文件失败: {file_path}, 错误: {e}")
            return False

    def backup_files(self, file_paths: list) -> bool:
        """
        批量备份文件

        参数:
            file_paths: 要备份的文件路径列表

        返回值:
            bool: 所有文件是否都备份成功
        """
        for file_path in file_paths:
            if not self.backup_file(file_path):
                return False
        return True

    def restore_all(self):
        """
        恢复所有备份文件

        设计说明:
            - 遍历所有备份，将原文件恢复为备份内容
            - 如果原备份为None（文件不存在），则删除原文件
        """
        for original_path, backup_path in self.backups.items():
            try:
                if backup_path is None:
                    if os.path.exists(original_path):
                        os.remove(original_path)
                        logger.debug(
                            "finalization", f"已删除新创建的文件: {original_path}"
                        )
                else:
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, original_path)
                        logger.info("finalization", f"已恢复文件: {original_path}")
            except Exception as e:
                logger.error(
                    "finalization", f"恢复文件失败: {original_path}, 错误: {e}"
                )

    def cleanup(self):
        """
        清理备份文件

        设计说明:
            - 定稿成功后调用，删除所有备份文件
            - 删除临时备份目录
        """
        backup_dir = os.path.join(self.filepath, ".backup_temp")
        try:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                logger.debug("finalization", "已清理备份文件")
        except Exception as e:
            logger.warn("finalization", f"清理备份目录失败: {e}")

        self.backups.clear()


def finalize_chapter(
    novel_number: int,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    filepath: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    interface_format: str,
    max_tokens: int,
    timeout: int = 600,
):
    """
    对指定章节做最终处理：更新前文摘要、更新角色状态、插入向量库等。

    参数:
        novel_number: 章节编号
        word_number: 目标字数
        api_key: LLM API密钥
        base_url: LLM API基础URL
        model_name: LLM模型名称
        temperature: 生成温度
        filepath: 项目路径
        embedding_api_key: Embedding API密钥
        embedding_url: Embedding API URL
        embedding_interface_format: Embedding接口格式
        embedding_model_name: Embedding模型名称
        interface_format: LLM接口格式
        max_tokens: 最大Token数
        timeout: 超时时间（秒）

    返回值:
        无

    异常:
        FinalizationError: 定稿过程中发生错误

    设计说明:
        - 定稿操作采用事务性保存，确保原子性
        - 如果任何步骤失败，自动恢复所有备份文件
        - 向量库更新是最后一步，失败不影响前面的更新
    """
    logger.info("finalization", f"开始定稿第{novel_number}章")

    chapters_dir = os.path.join(filepath, "chapters")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    chapter_text = read_file(chapter_file).strip()
    if not chapter_text:
        logger.warn("finalization", f"第{novel_number}章内容为空，无法定稿")
        raise FinalizationError(f"第{novel_number}章内容为空，无法定稿", "读取章节")

    global_summary_file = os.path.join(filepath, "global_summary.txt")
    character_state_file = os.path.join(filepath, "character_state.txt")

    backup_manager = BackupManager(filepath)

    try:
        logger.info("finalization", "开始备份原文件...")
        files_to_backup = [global_summary_file, character_state_file]
        if not backup_manager.backup_files(files_to_backup):
            raise FinalizationError("备份文件失败", "备份文件")

        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        old_global_summary = read_file(global_summary_file)
        logger.info("finalization", "开始更新全局摘要...")
        prompt_summary = summary_prompt.format(
            chapter_text=chapter_text, global_summary=old_global_summary
        )
        new_global_summary = invoke_with_cleaning(llm_adapter, prompt_summary)
        if not new_global_summary.strip():
            raise FinalizationError("全局摘要更新失败，LLM返回空内容", "更新全局摘要")

        old_character_state = read_file(character_state_file)
        logger.info("finalization", "开始更新角色状态...")
        prompt_char_state = update_character_state_prompt.format(
            chapter_text=chapter_text, old_state=old_character_state
        )
        new_char_state = invoke_with_cleaning(llm_adapter, prompt_char_state)
        if not new_char_state.strip():
            raise FinalizationError("角色状态更新失败，LLM返回空内容", "更新角色状态")

        logger.info("finalization", "保存更新后的文件...")
        clear_file_content(global_summary_file)
        save_string_to_txt(new_global_summary, global_summary_file)
        clear_file_content(character_state_file)
        save_string_to_txt(new_char_state, character_state_file)

        vector_store_updated = False
        if embedding_interface_format and embedding_interface_format.strip():
            logger.info("finalization", "开始更新向量库...")
            try:
                update_vector_store(
                    embedding_adapter=create_embedding_adapter(
                        embedding_interface_format,
                        embedding_api_key,
                        embedding_url,
                        embedding_model_name,
                    ),
                    new_chapter=chapter_text,
                    filepath=filepath,
                )
                vector_store_updated = True
                logger.info("finalization", f"第{novel_number}章已添加到向量库")
            except Exception as e:
                logger.error("finalization", f"向量库更新失败: {str(e)}")
                import traceback
                traceback.print_exc()
                # 向量库更新失败不应该影响其他定稿步骤，所以不抛出异常
                logger.warning("finalization", "向量库更新失败，但继续完成其他定稿步骤")
        else:
            logger.debug("finalization", f"跳过向量库更新(Embedding未配置)")

        backup_manager.cleanup()
        logger.info("finalization", f"第{novel_number}章定稿完成")

    except FinalizationError as e:
        logger.error("finalization", f"定稿失败 [{e.step}]: {str(e)}")
        logger.info("finalization", "开始恢复备份文件...")
        backup_manager.restore_all()
        backup_manager.cleanup()
        raise

    except Exception as e:
        logger.error("finalization", f"定稿过程发生未知错误: {str(e)}")
        logger.info("finalization", "开始恢复备份文件...")
        backup_manager.restore_all()
        backup_manager.cleanup()
        raise FinalizationError(f"定稿过程发生未知错误: {str(e)}", "未知错误")


def enrich_chapter_text(
    chapter_text: str,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    interface_format: str,
    max_tokens: int,
    timeout: int = 600,
) -> str:
    """
    对章节文本进行扩写，使其更接近目标字数，保持剧情连贯。

    参数:
        chapter_text: 原始章节文本
        word_number: 目标字数
        api_key: API密钥
        base_url: API基础URL
        model_name: 模型名称
        temperature: 生成温度
        interface_format: 接口格式
        max_tokens: 最大Token数
        timeout: 超时时间（秒）

    返回值:
        str: 扩写后的章节文本。如果扩写失败，返回原文

    设计说明:
        - 扩写会保持原有剧情连贯性
        - 扩写结果接近目标字数
    """
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    prompt = f"""以下章节文本较短，请在保持剧情连贯的前提下进行扩写，使其更充实，接近 {word_number} 字左右，仅给出最终文本，不要解释任何内容。：
原内容：
{chapter_text}
"""
    enriched_text = invoke_with_cleaning(llm_adapter, prompt)
    return enriched_text if enriched_text else chapter_text
