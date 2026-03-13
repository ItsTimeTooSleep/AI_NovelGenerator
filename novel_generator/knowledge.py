# -*- coding: utf-8 -*-
"""
知识库导入模块

================================================================================
模块功能概述
================================================================================
本模块负责将外部知识文件导入到向量库中，为小说创作提供参考资料支持。
支持txt等文本格式的知识文件导入。

================================================================================
核心函数
================================================================================
- import_knowledge_file: 知识文件导入主函数
- advanced_split_content: 智能文本分段函数

================================================================================
导入流程
================================================================================
1. 读取知识文件内容
2. 使用NLTK进行句子分割
3. 按长度分段，每段不超过max_length
4. 创建或更新向量库

================================================================================
设计决策
================================================================================
- 使用NLTK进行语义级别的句子分割
- 分段长度可配置，默认500字符
- 支持追加模式，不覆盖已有知识库内容
- 禁用tokenizer并行警告，避免日志污染

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import logging
import os
import traceback
import warnings

from langchain.docstore.document import Document
import nltk

from core.utils import read_file
from novel_generator.vectorstore_utils import init_vector_store, load_vector_store

warnings.filterwarnings(
    "ignore", message=".*Torch was not compiled with flash attention.*"
)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(
    filename="app.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def advanced_split_content(
    content: str, similarity_threshold: float = 0.7, max_length: int = 500
) -> list:
    """
    使用基本分段策略对文本进行分段。

    参数:
        content: 待分段的文本内容
        similarity_threshold: 相似度阈值（保留参数，暂未使用）
        max_length: 每段的最大长度

    返回值:
        list: 分段后的文本列表

    设计说明:
        - 使用NLTK进行句子级别的分割
        - 按长度限制合并句子为段落
    """
    sentences = nltk.sent_tokenize(content)
    if not sentences:
        return []

    final_segments = []
    current_segment = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length:
            if current_segment:
                final_segments.append(" ".join(current_segment))
            current_segment = [sentence]
            current_length = sentence_length
        else:
            current_segment.append(sentence)
            current_length += sentence_length

    if current_segment:
        final_segments.append(" ".join(current_segment))

    return final_segments


def import_knowledge_file(
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    file_path: str,
    filepath: str,
):
    """
    将知识文件导入到向量库中。

    参数:
        embedding_api_key: Embedding API密钥
        embedding_url: Embedding API URL
        embedding_interface_format: Embedding接口格式
        embedding_model_name: Embedding模型名称
        file_path: 知识文件路径
        filepath: 项目路径（向量库存储位置）

    返回值:
        无

    设计说明:
        - 支持追加模式，不覆盖已有内容
        - 文件不存在或内容为空时会跳过
        - 向量库不存在时会自动创建
    """
    logging.info(
        f"开始导入知识库文件: {file_path}, 接口格式: {embedding_interface_format}, 模型: {embedding_model_name}"
    )
    if not os.path.exists(file_path):
        logging.warning(f"知识库文件不存在: {file_path}")
        return
    content = read_file(file_path)
    if not content.strip():
        logging.warning("知识库文件内容为空。")
        return
    paragraphs = advanced_split_content(content)
    from core.embedding_adapters import create_embedding_adapter

    embedding_adapter = create_embedding_adapter(
        embedding_interface_format,
        embedding_api_key,
        embedding_url if embedding_url else "http://localhost:11434/api",
        embedding_model_name,
    )
    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info(
            "Vector store does not exist or load failed. Initializing a new one for knowledge import..."
        )
        store = init_vector_store(embedding_adapter, paragraphs, filepath)
        if store:
            logging.info("知识库文件已成功导入至向量库(新初始化)。")
        else:
            logging.warning("知识库导入失败，跳过。")
    else:
        try:
            docs = [Document(page_content=str(p)) for p in paragraphs]
            store.add_documents(docs)
            logging.info("知识库文件已成功导入至向量库(追加模式)。")
        except Exception as e:
            logging.warning(f"知识库导入失败: {e}")
            traceback.print_exc()
