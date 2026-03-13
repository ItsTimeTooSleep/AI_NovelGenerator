# -*- coding: utf-8 -*-
"""
文本嵌入(Embedding)适配器模块

================================================================================
模块功能概述
================================================================================
本模块提供统一的文本嵌入模型接口适配层，支持多种Embedding服务商的调用。
文本嵌入用于将文本转换为向量表示，支持语义搜索和知识库检索功能。

================================================================================
支持的模型服务商
================================================================================
- OpenAI: text-embedding-ada-002等嵌入模型
- Azure OpenAI: Azure托管的嵌入模型
- Ollama: 本地部署的嵌入模型
- ML Studio: 本地开发环境嵌入模型
- Gemini: Google Gemini嵌入模型
- SiliconFlow: 硅基流动嵌入服务

================================================================================
核心类与函数
================================================================================
- BaseEmbeddingAdapter: Embedding适配器基类
- create_embedding_adapter: 工厂函数，根据接口格式创建对应适配器
- ensure_openai_base_url_has_v1: URL格式处理函数

================================================================================
核心方法
================================================================================
- embed_documents: 批量文本嵌入，返回向量列表
- embed_query: 单个查询文本嵌入，返回向量

================================================================================
设计决策
================================================================================
- 使用适配器模式统一不同服务商的API差异
- 支持批量嵌入以提高效率
- 自动处理URL格式，简化配置

================================================================================
依赖要求
================================================================================
- langchain_openai: OpenAI兼容接口的LangChain封装
- requests: HTTP请求库

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import traceback
from typing import List

from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
import requests
from core import get_logger


def ensure_openai_base_url_has_v1(url: str) -> str:
    """
    若用户输入的 url 不包含 '/v1'，则在末尾追加 '/v1'。
    同时移除末尾多余的 '/embeddings' 后缀，因为 OpenAIEmbeddings 会自动添加。

    Args:
        url: 用户输入的 base_url

    Returns:
        str: 处理后的标准 base_url

    Examples:
        >>> ensure_openai_base_url_has_v1("https://api.openai.com/v1/embeddings")
        "https://api.openai.com/v1"
        >>> ensure_openai_base_url_has_v1("https://api.openai.com")
        "https://api.openai.com/v1"
    """
    import re

    url = url.strip()
    if not url:
        return url

    url = re.sub(r"/embeddings/?$", "", url, flags=re.IGNORECASE)

    if not re.search(r"/v\d+$", url):
        if "/v1" not in url:
            url = url.rstrip("/") + "/v1"
    return url


class BaseEmbeddingAdapter:
    """
    Embedding 接口统一基类
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        raise NotImplementedError


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 OpenAIEmbeddings（或兼容接口）的适配器
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self._embedding = OpenAIEmbeddings(
            openai_api_key=api_key,
            openai_api_base=ensure_openai_base_url_has_v1(base_url),
            model=model_name,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embedding.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self._embedding.embed_query(query)


class AzureOpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 AzureOpenAIEmbeddings（或兼容接口）的适配器
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        import re

        match = re.match(
            r"https://(.+?)/openai/deployments/(.+?)/embeddings\?api-version=(.+)",
            base_url,
        )
        if match:
            self.azure_endpoint = f"https://{match.group(1)}"
            self.azure_deployment = match.group(2)
            self.api_version = match.group(3)
        else:
            raise ValueError("Invalid Azure OpenAI base_url format")

        self._embedding = AzureOpenAIEmbeddings(
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            openai_api_key=api_key,
            api_version=self.api_version,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embedding.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self._embedding.embed_query(query)


class OllamaEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    其接口路径为 /api/embeddings
    """

    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._logger = get_logger()
        self._logger.debug(
            "embedding_adapters",
            f"OllamaEmbeddingAdapter初始化: 模型={model_name}, base_url={self.base_url}",
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            vec = self._embed_single(text)
            embeddings.append(vec)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        return self._embed_single(query)

    def _embed_single(self, text: str) -> List[float]:
        """
        调用 Ollama 本地服务 /api/embeddings 接口，获取文本 embedding
        """
        url = self.base_url.rstrip("/")
        if "/api/embeddings" not in url:
            if "/api" in url:
                url = f"{url}/embeddings"
            else:
                if "/v1" in url:
                    url = url[: url.index("/v1")]
                url = f"{url}/api/embeddings"

        data = {"model": self.model_name, "prompt": text}
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            if "embedding" not in result:
                self._logger.error(
                    "embedding_adapters", "Ollama响应中缺少'embedding'字段"
                )
                raise ValueError("No 'embedding' field in Ollama response.")
            self._logger.debug(
                "embedding_adapters",
                f"Ollama embedding成功，向量维度: {len(result['embedding'])}",
            )
            return result["embedding"]
        except requests.exceptions.RequestException as e:
            self._logger.error(
                "embedding_adapters",
                f"Ollama embeddings请求错误: {e}\n{traceback.format_exc()}",
            )
            return []


class MLStudioEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 LM Studio 的 embedding 适配器
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self._logger = get_logger()
        self.url = ensure_openai_base_url_has_v1(base_url)
        if not self.url.endswith("/embeddings"):
            self.url = f"{self.url}/embeddings"

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.model_name = model_name
        self._logger.debug(
            "embedding_adapters",
            f"MLStudioEmbeddingAdapter初始化: 模型={model_name}, url={self.url}",
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            payload = {"input": texts, "model": self.model_name}
            response = requests.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            if "data" not in result:
                self._logger.error(
                    "embedding_adapters", f"LM Studio API响应格式无效: {result}"
                )
                return [[]] * len(texts)
            embeddings = [item.get("embedding", []) for item in result["data"]]
            self._logger.debug(
                "embedding_adapters",
                f"MLStudio embed_documents成功，数量: {len(embeddings)}",
            )
            return embeddings
        except requests.exceptions.RequestException as e:
            self._logger.error("embedding_adapters", f"LM Studio API请求失败: {str(e)}")
            return [[]] * len(texts)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            self._logger.error(
                "embedding_adapters", f"解析LM Studio API响应错误: {str(e)}"
            )
            return [[]] * len(texts)

    def embed_query(self, query: str) -> List[float]:
        try:
            payload = {"input": query, "model": self.model_name}
            response = requests.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            if "data" not in result or not result["data"]:
                self._logger.error(
                    "embedding_adapters", f"LM Studio API响应格式无效: {result}"
                )
                return []
            embedding = result["data"][0].get("embedding", [])
            self._logger.debug(
                "embedding_adapters",
                f"MLStudio embed_query成功，向量维度: {len(embedding)}",
            )
            return embedding
        except requests.exceptions.RequestException as e:
            self._logger.error("embedding_adapters", f"LM Studio API请求失败: {str(e)}")
            return []
        except (KeyError, IndexError, ValueError, TypeError) as e:
            self._logger.error(
                "embedding_adapters", f"解析LM Studio API响应错误: {str(e)}"
            )
            return []


class GeminiEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 Google Generative AI (Gemini) 接口的 Embedding 适配器
    使用直接 POST 请求方式，URL 示例：
    https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key=YOUR_API_KEY
    """

    def __init__(self, api_key: str, model_name: str, base_url: str):
        """
        :param api_key: 传入的 Google API Key
        :param model_name: 这里一般是 "text-embedding-004"
        :param base_url: e.g. https://generativelanguage.googleapis.com/v1beta/models
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._logger = get_logger()
        self._logger.debug(
            "embedding_adapters", f"GeminiEmbeddingAdapter初始化: 模型={model_name}"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            vec = self._embed_single(text)
            embeddings.append(vec)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        return self._embed_single(query)

    def _embed_single(self, text: str) -> List[float]:
        """
        直接调用 Google Generative Language API (Gemini) 接口，获取文本 embedding
        """
        url = f"{self.base_url}/{self.model_name}:embedContent?key={self.api_key}"
        payload = {"model": self.model_name, "content": {"parts": [{"text": text}]}}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            embedding_data = result.get("embedding", {})
            values = embedding_data.get("values", [])
            self._logger.debug(
                "embedding_adapters", f"Gemini embedding成功，向量维度: {len(values)}"
            )
            return values
        except requests.exceptions.RequestException as e:
            self._logger.error(
                "embedding_adapters",
                f"Gemini embed_content请求错误: {e}\n{traceback.format_exc()}",
            )
            return []
        except Exception as e:
            self._logger.error(
                "embedding_adapters",
                f"Gemini embed_content解析错误: {e}\n{traceback.format_exc()}",
            )
            return []


class SiliconFlowEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 SiliconFlow 的 embedding 适配器
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self._logger = get_logger()
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "https://" + base_url
        self.url = base_url if base_url else "https://api.siliconflow.cn/v1/embeddings"

        self.payload = {
            "model": model_name,
            "input": "Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!",
            "encoding_format": "float",
        }
        self.headers = {
            "Authorization": "Bearer {api_key}".format(api_key=api_key),
            "Content-Type": "application/json",
        }
        self._logger.debug(
            "embedding_adapters", f"SiliconFlowEmbeddingAdapter初始化: url={self.url}"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                self.payload["input"] = text
                response = requests.post(
                    self.url, json=self.payload, headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                if not result or "data" not in result or not result["data"]:
                    self._logger.error(
                        "embedding_adapters", f"SiliconFlow API响应格式无效: {result}"
                    )
                    embeddings.append([])
                    continue
                emb = result["data"][0].get("embedding", [])
                embeddings.append(emb)
            except requests.exceptions.RequestException as e:
                self._logger.error(
                    "embedding_adapters", f"SiliconFlow API请求失败: {str(e)}"
                )
                embeddings.append([])
            except (KeyError, IndexError, ValueError, TypeError) as e:
                self._logger.error(
                    "embedding_adapters", f"解析SiliconFlow API响应错误: {str(e)}"
                )
                embeddings.append([])
        self._logger.debug(
            "embedding_adapters",
            f"SiliconFlow embed_documents成功，数量: {len(embeddings)}",
        )
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        try:
            self.payload["input"] = query
            response = requests.post(self.url, json=self.payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            if not result or "data" not in result or not result["data"]:
                self._logger.error(
                    "embedding_adapters", f"SiliconFlow API响应格式无效: {result}"
                )
                return []
            embedding = result["data"][0].get("embedding", [])
            self._logger.debug(
                "embedding_adapters",
                f"SiliconFlow embed_query成功，向量维度: {len(embedding)}",
            )
            return embedding
        except requests.exceptions.RequestException as e:
            self._logger.error(
                "embedding_adapters", f"SiliconFlow API请求失败: {str(e)}"
            )
            return []
        except (KeyError, IndexError, ValueError, TypeError) as e:
            self._logger.error(
                "embedding_adapters", f"解析SiliconFlow API响应错误: {str(e)}"
            )
            return []


class NvidiaEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 NVIDIA NIM API 的 embedding 适配器

    NVIDIA的embedding模型（如llama-nemotron-embed-vl-1b-v2）是不对称嵌入模型，
    需要明确指定input_type参数：
    - "query": 用于查询文本
    - "document": 用于文档文本
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self._logger = get_logger()
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "https://" + base_url

        self.url = (
            base_url if base_url else "https://integrate.api.nvidia.com/v1/embeddings"
        )
        self.model_name = model_name
        self.api_key = api_key

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._logger.debug(
            "embedding_adapters",
            f"NvidiaEmbeddingAdapter初始化: 模型={model_name}, url={self.url}",
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量文档嵌入

        Args:
            texts: 文档文本列表

        Returns:
            List[List[float]]: 嵌入向量列表，失败时返回空列表
        """
        embeddings = []
        for text in texts:
            try:
                payload = {
                    "model": self.model_name,
                    "input": [text],
                    "input_type": "passage",
                    "encoding_format": "float",
                    "truncate": "NONE",
                }
                response = requests.post(
                    self.url, json=payload, headers=self.headers, timeout=30
                )
                response.raise_for_status()
                result = response.json()

                if not result or "data" not in result or not result["data"]:
                    error_msg = f"NVIDIA API响应格式无效: {result}"
                    self._logger.error("embedding_adapters", error_msg)
                    embeddings.append([])
                    continue

                emb = result["data"][0].get("embedding", [])
                embeddings.append(emb)
                self._logger.debug(
                    "embedding_adapters",
                    f"NVIDIA embed_documents成功，向量维度: {len(emb)}",
                )

            except requests.exceptions.RequestException as e:
                error_msg = f"NVIDIA API请求失败: {str(e)}"
                self._logger.error("embedding_adapters", error_msg)
                embeddings.append([])
            except (KeyError, IndexError, ValueError, TypeError) as e:
                error_msg = f"解析NVIDIA API响应错误: {str(e)}"
                self._logger.error("embedding_adapters", error_msg)
                embeddings.append([])

        self._logger.debug(
            "embedding_adapters", f"NVIDIA embed_documents完成，数量: {len(embeddings)}"
        )
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        查询文本嵌入

        Args:
            query: 查询文本

        Returns:
            List[float]: 嵌入向量，失败时返回空列表
        """
        try:
            payload = {
                "model": self.model_name,
                "input": [query],
                "input_type": "query",
                "encoding_format": "float",
                "truncate": "NONE",
            }
            response = requests.post(
                self.url, json=payload, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if not result or "data" not in result or not result["data"]:
                error_msg = f"NVIDIA API响应格式无效: {result}"
                self._logger.error("embedding_adapters", error_msg)
                return []

            embedding = result["data"][0].get("embedding", [])
            self._logger.debug(
                "embedding_adapters",
                f"NVIDIA embed_query成功，向量维度: {len(embedding)}",
            )
            return embedding

        except requests.exceptions.RequestException as e:
            error_msg = f"NVIDIA API请求失败: {str(e)}"
            self._logger.error("embedding_adapters", error_msg)
            return []
        except (KeyError, IndexError, ValueError, TypeError) as e:
            error_msg = f"解析NVIDIA API响应错误: {str(e)}"
            self._logger.error("embedding_adapters", error_msg)
            return []


def create_embedding_adapter(
    interface_format: str, api_key: str, base_url: str, model_name: str
) -> BaseEmbeddingAdapter:
    """
    工厂函数：根据 interface_format 返回不同的 embedding 适配器实例

    Args:
        interface_format: 接口格式名称（如"OpenAI"、"Nvidia"等）
        api_key: API密钥
        base_url: API基础URL
        model_name: 模型名称

    Returns:
        BaseEmbeddingAdapter: 对应的embedding适配器实例

    Raises:
        ValueError: 未知的接口格式时抛出

    设计说明:
        - 支持多种embedding服务提供商
        - 自动识别接口格式（不区分大小写）
        - 扩展新提供商只需添加新的适配器类和分支判断
    """
    logger = get_logger()
    fmt = interface_format.strip().lower()
    logger.info(
        "embedding_adapters",
        f"创建Embedding适配器: 格式={interface_format}, 模型={model_name}",
    )
    logger.debug(
        "embedding_adapters",
        f"Embedding配置详情: base_url={base_url}, api_key_length={len(api_key) if api_key else 0}",
    )

    if fmt == "openai":
        return OpenAIEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "azure openai":
        return AzureOpenAIEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "ollama":
        return OllamaEmbeddingAdapter(model_name, base_url)
    elif fmt == "ml studio":
        return MLStudioEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "gemini":
        return GeminiEmbeddingAdapter(api_key, model_name, base_url)
    elif fmt == "siliconflow":
        return SiliconFlowEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "nvidia":
        logger.debug("embedding_adapters", "使用NvidiaEmbeddingAdapter")
        return NvidiaEmbeddingAdapter(api_key, base_url, model_name)
    else:
        logger.error(
            "embedding_adapters", f"未知的embedding接口格式: {interface_format}"
        )
        raise ValueError(f"Unknown embedding interface_format: {interface_format}")
