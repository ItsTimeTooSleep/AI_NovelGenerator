# -*- coding: utf-8 -*-
"""
向量存储工具模块

================================================================================
模块功能概述
================================================================================
本模块提供向量数据库（ChromaDB）的操作封装，支持文本向量化存储和语义检索。
向量库用于存储章节内容和知识库资料，支持基于语义相似度的内容检索。

================================================================================
核心函数
================================================================================
- init_vector_store: 初始化向量库
- load_vector_store: 加载已有向量库
- update_vector_store: 更新向量库（添加新内容）
- clear_vector_store: 清空向量库
- get_relevant_context_from_vector_store: 语义检索

================================================================================
技术架构
================================================================================
- 使用ChromaDB作为向量数据库
- 通过LangChain封装，支持多种Embedding模型
- 向量库存储在项目目录下的vectorstore文件夹

================================================================================
设计决策
================================================================================
- 使用重试机制提高Embedding调用稳定性
- 检索结果限制2000字符，避免prompt过长
- 禁用遥测和并行警告，减少日志噪音
- 支持自定义Embedding适配器
- 使用线程锁保护ChromaDB操作，避免多线程竞争

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import logging
import os
import ssl
import threading
import traceback
import warnings

from langchain_chroma import Chroma
import nltk

logging.basicConfig(
    filename="app.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
warnings.filterwarnings(
    "ignore", message=".*Torch was not compiled with flash attention.*"
)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chromadb.config import Settings
from langchain.docstore.document import Document

from .common import call_with_retry

_vectorstore_lock = threading.RLock()


def get_vectorstore_dir(filepath: str) -> str:
    """获取 vectorstore 路径"""
    return os.path.join(filepath, "vectorstore")


def clear_vector_store(filepath: str) -> bool:
    """清空 清空向量库"""
    import shutil

    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("No vector store found to clear.")
        return False
    with _vectorstore_lock:
        try:
            shutil.rmtree(store_dir)
            logging.info(f"Vector store directory '{store_dir}' removed.")
            return True
        except Exception as e:
            logging.error(
                f"无法删除向量库文件夹，请关闭程序后手动删除 {store_dir}。\n {str(e)}"
            )
            traceback.print_exc()
            return False


def init_vector_store(embedding_adapter, texts, filepath: str):
    """
    在 filepath 下创建/加载一个 Chroma 向量库并插入 texts。
    如果Embedding失败，则抛出异常。

    Args:
        embedding_adapter: 嵌入适配器
        texts: 文本列表
        filepath: 项目路径

    Returns:
        Chroma: 向量库实例

    Raises:
        Exception: 初始化失败时抛出异常
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_vectorstore_dir(filepath)
    os.makedirs(store_dir, exist_ok=True)
    documents = [Document(page_content=str(t)) for t in texts]

    with _vectorstore_lock:
        try:

            class LCEmbeddingWrapper(LCEmbeddings):
                def embed_documents(self, texts):
                    return call_with_retry(
                        func=embedding_adapter.embed_documents,
                        max_retries=3,
                        sleep_time=2,
                        texts=texts,
                    )

                def embed_query(self, query: str):
                    return call_with_retry(
                        func=embedding_adapter.embed_query,
                        max_retries=3,
                        sleep_time=2,
                        query=query,
                    )

            chroma_embedding = LCEmbeddingWrapper()
            vectorstore = Chroma.from_documents(
                documents,
                embedding=chroma_embedding,
                persist_directory=store_dir,
                client_settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                ),
                collection_name="novel_collection",
            )
            return vectorstore
        except Exception as e:
            error_msg = f"Init vector store failed: {e}"
            logging.warning(error_msg)
            traceback.print_exc()
            raise Exception(error_msg)


def load_vector_store(embedding_adapter, filepath: str):
    """
    读取已存在的 Chroma 向量库。若不存在则返回 None。
    如果加载失败（embedding 或IO问题），则抛出异常。

    Args:
        embedding_adapter: 嵌入适配器
        filepath: 项目路径

    Returns:
        Chroma: 向量库实例，如果不存在则返回None

    Raises:
        Exception: 加载失败时抛出异常
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("Vector store not found. Will return None.")
        return None

    with _vectorstore_lock:
        try:

            class LCEmbeddingWrapper(LCEmbeddings):
                def embed_documents(self, texts):
                    return call_with_retry(
                        func=embedding_adapter.embed_documents,
                        max_retries=3,
                        sleep_time=2,
                        texts=texts,
                    )

                def embed_query(self, query: str):
                    return call_with_retry(
                        func=embedding_adapter.embed_query,
                        max_retries=3,
                        sleep_time=2,
                        query=query,
                    )

            chroma_embedding = LCEmbeddingWrapper()
            return Chroma(
                persist_directory=store_dir,
                embedding_function=chroma_embedding,
                client_settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                ),
                collection_name="novel_collection",
            )
        except Exception as e:
            error_msg = f"Failed to load vector store: {e}"
            logging.warning(error_msg)
            traceback.print_exc()
            raise Exception(error_msg)


def split_by_length(text: str, max_length: int = 500):
    """按照 max_length 切分文本"""
    segments = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + max_length, len(text))
        segment = text[start_idx:end_idx]
        segments.append(segment.strip())
        start_idx = end_idx
    return segments


def split_text_for_vectorstore(
    chapter_text: str, max_length: int = 500, similarity_threshold: float = 0.7
):
    """
    对新的章节文本进行分段后,再用于存入向量库。
    使用 embedding 进行文本相似度计算。
    """
    if not chapter_text.strip():
        return []

    # 尝试使用nltk进行句子分割，如果失败则使用简单的换行符和句号分割
    sentences = []
    try:
        # 尝试下载nltk数据（如果需要）
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        sentences = nltk.sent_tokenize(chapter_text)
    except Exception as e:
        logging.warning(f"nltk句子分割失败，使用备用方法: {str(e)}")
        # 备用方法：使用换行符和句号分割
        import re
        # 先按换行符分割
        lines = chapter_text.split('\n')
        for line in lines:
            if line.strip():
                # 再按句号、问号、感叹号分割
                parts = re.split(r'([。！？.!?])', line)
                for i in range(0, len(parts)-1, 2):
                    sentence = parts[i] + parts[i+1]
                    if sentence.strip():
                        sentences.append(sentence)
                # 处理最后一部分（如果没有标点结尾）
                if len(parts) % 2 == 1 and parts[-1].strip():
                    sentences.append(parts[-1])

    if not sentences:
        return []

    # 直接按长度分段,不做相似度合并
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


def update_vector_store(embedding_adapter, new_chapter: str, filepath: str):
    """
    将最新章节文本插入到向量库中。
    若库不存在则初始化；若初始化/更新失败，则抛出异常。

    Args:
        embedding_adapter: 嵌入适配器
        new_chapter: 新章节文本
        filepath: 项目路径

    Raises:
        Exception: 向量库更新失败时抛出异常
    """
    splitted_texts = split_text_for_vectorstore(new_chapter)
    if not splitted_texts:
        error_msg = "No valid text to insert into vector store."
        logging.warning(error_msg)
        raise Exception(error_msg)

    with _vectorstore_lock:
        store = load_vector_store(embedding_adapter, filepath)
        if not store:
            logging.info(
                "Vector store does not exist or failed to load. Initializing a new one for new chapter..."
            )
            store = init_vector_store(embedding_adapter, splitted_texts, filepath)
            if not store:
                error_msg = "Init vector store failed"
                logging.warning(error_msg)
                raise Exception(error_msg)
            else:
                logging.info("New vector store created successfully.")
            return

        try:
            docs = [Document(page_content=str(t)) for t in splitted_texts]
            store.add_documents(docs)
            logging.info("Vector store updated with the new chapter splitted segments.")
        except Exception as e:
            error_msg = f"Failed to update vector store: {e}"
            logging.warning(error_msg)
            traceback.print_exc()
            raise Exception(error_msg)


def get_relevant_context_from_vector_store(
    embedding_adapter, query: str, filepath: str, k: int = 2
) -> str:
    """
    从向量库中检索与 query 最相关的 k 条文本，拼接后返回。
    如果向量库加载/检索失败，则返回空字符串。
    最终只返回最多2000字符的检索片段。
    """
    with _vectorstore_lock:
        store = load_vector_store(embedding_adapter, filepath)
        if not store:
            logging.info("No vector store found or load failed. Returning empty context.")
            return ""

        try:
            docs = store.similarity_search(query, k=k)
            if not docs:
                logging.info(
                    f"No relevant documents found for query '{query}'. Returning empty context."
                )
                return ""
            combined = "\n".join([d.page_content for d in docs])
            if len(combined) > 2000:
                combined = combined[:2000]
            return combined
        except Exception as e:
            logging.warning(f"Similarity search failed: {e}")
            traceback.print_exc()
            return ""


def _get_sentence_transformer(model_name: str = "paraphrase-MiniLM-L6-v2"):
    """获取sentence transformer模型，处理SSL问题"""
    try:
        # 设置torch环境变量
        os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
        os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "0"

        # 禁用SSL验证
        ssl._create_default_https_context = ssl._create_unverified_context

        # ...existing code...
    except Exception as e:
        logging.error(f"Failed to load sentence transformer model: {e}")
        traceback.print_exc()
        return None
