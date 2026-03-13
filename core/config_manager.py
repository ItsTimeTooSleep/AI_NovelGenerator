# -*- coding: utf-8 -*-
"""
配置管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责AI小说生成器应用程序的配置文件管理，包括：
- 配置文件的加载与保存
- 默认配置的创建
- LLM和Embedding配置的测试验证

================================================================================
核心功能
================================================================================
1. load_config: 加载配置文件，不存在时自动创建默认配置
2. save_config: 保存配置数据到JSON文件
3. create_config: 创建默认配置文件
4. test_llm_config: 测试LLM配置是否可用
5. test_embedding_config: 测试Embedding配置是否可用

================================================================================
配置文件结构
================================================================================
配置文件(config.json)包含以下主要配置项：
- last_interface_format: 上次使用的LLM接口格式
- last_embedding_interface_format: 上次使用的Embedding接口格式
- streaming_enabled: 是否启用流式输出
- novels_directory: 小说项目存储目录
- llm_configs: LLM配置集合
- embedding_configs: Embedding配置集合
- other_params: 其他参数（主题、题材、章节数等）
- proxy_setting: 代理设置
- webdav_config: WebDAV同步配置
- theme: 界面主题
- composer_settings: 编辑器设置

================================================================================
设计决策
================================================================================
- 使用JSON格式存储配置，便于人工阅读和编辑
- 配置文件不存在时自动创建默认配置，提升用户体验
- 测试功能使用独立线程执行，避免阻塞UI
- 支持多套LLM/Embedding配置，便于切换不同模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json
import os
import threading
import inspect

from core.embedding_adapters import create_embedding_adapter
from core.llm import create_llm_adapter
from core import get_logger


def load_config(config_file: str) -> dict:
    """
    从指定文件加载配置，若文件不存在则创建默认配置。

    该函数尝试从指定的配置文件加载JSON格式的配置数据。
    如果配置文件不存在，会自动创建一个包含默认值的配置文件。

    参数:
        config_file: 配置文件的路径，相对于程序运行目录或绝对路径

    返回值:
        dict: 配置数据的字典对象。如果加载失败则返回空字典

    异常:
        无直接抛出异常，内部捕获所有异常并返回空字典

    使用示例:
        >>> config = load_config("config.json")
        >>> print(config.get("theme", "Light"))
        Light

    设计说明:
        - 配置文件不存在时自动创建，避免首次运行报错
        - 确保novels_directory配置项始终存在
        - 加载失败时返回空字典而非抛出异常，保证程序稳定性
    """
    logger = get_logger()
    if not os.path.exists(config_file):
        logger.info("config_manager", f"配置文件不存在，创建默认配置: {config_file}")
        create_config(config_file)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "novels_directory" not in config:
            default_novels_dir = os.path.join(os.getcwd(), "novels")
            config["novels_directory"] = default_novels_dir
            save_config(config, config_file)
            logger.debug(
                "config_manager", f"添加默认novels_directory: {default_novels_dir}"
            )

        caller_frame = inspect.currentframe()
        caller_module = "unknown"
        if caller_frame and caller_frame.f_back:
            caller_module = caller_frame.f_back.f_globals.get("__name__", "unknown")
        logger.debug(
            "config_manager", f"配置加载成功: {config_file} (调用模块: {caller_module})"
        )
        return config
    except Exception as e:
        logger.error("config_manager", f"加载配置文件失败: {e}")
        return {}


def create_config(config_file: str) -> dict:
    """
    创建默认配置文件。

    该函数生成一个包含所有默认配置项的字典，并将其保存到指定文件。
    默认配置包含LLM、Embedding、代理、WebDAV等各项设置。

    参数:
        config_file: 要创建的配置文件路径

    返回值:
        dict: 创建的默认配置字典

    异常:
        可能抛出IOError（文件写入失败时）

    使用示例:
        >>> create_config("config.json")

    设计说明:
        - LLM配置默认为空，需要用户自行配置
        - Embedding配置默认使用OpenAI接口
        - novels_directory默认为程序目录下的novels文件夹
        - 使用UUID为配置项生成唯一标识符
    """
    import datetime
    import os
    import uuid

    default_novels_dir = os.path.join(os.getcwd(), "novels")

    config = {
        "last_interface_format": "OpenAI",
        "last_embedding_interface_format": "OpenAI",
        "streaming_enabled": True,
        "novels_directory": default_novels_dir,
        "llm_configs": {},
        "embedding_configs": {
            "OpenAI": {
                "id": str(uuid.uuid4()),
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "text-embedding-ada-002",
                "retrieval_k": 4,
                "interface_format": "OpenAI",
                "created_at": datetime.datetime.now().isoformat(),
            }
        },
        "other_params": {
            "topic": "",
            "genre": "",
            "num_chapters": 0,
            "word_number": 0,
            "filepath": "",
            "chapter_num": "120",
            "user_guidance": "",
            "characters_involved": "",
            "key_items": "",
            "scene_location": "",
            "time_constraint": "",
        },
        "choose_configs": {},
        "proxy_setting": {"proxy_url": "127.0.0.1", "proxy_port": "", "enabled": False},
        "webdav_config": {
            "webdav_url": "",
            "webdav_username": "",
            "webdav_password": "",
        },
        "theme": "Light",
        "composer_settings": {"ai_level": "standard", "auto_save": True},
        "enable_wheel_tab_switch": True,
        "developer_mode": False,
        "local_token_estimation": True,
    }
    save_config(config, config_file)


def save_config(config_data: dict, config_file: str) -> bool:
    """
    将配置数据保存到指定文件。

    该函数将配置字典序列化为JSON格式并写入文件。
    使用UTF-8编码确保中文等非ASCII字符正确保存。

    参数:
        config_data: 要保存的配置数据字典
        config_file: 目标配置文件路径

    返回值:
        bool: 保存成功返回True，失败返回False

    异常:
        无直接抛出异常，内部捕获所有异常并返回False

    使用示例:
        >>> config = {"theme": "Dark"}
        >>> success = save_config(config, "config.json")
        >>> print(success)
        True

    设计说明:
        - 使用ensure_ascii=False保留非ASCII字符的原样输出
        - 使用indent=4格式化输出，便于人工阅读
        - 捕获所有异常避免程序崩溃
    """
    logger = get_logger()
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        logger.debug("config_manager", f"配置保存成功: {config_file}")
        return True
    except Exception as e:
        logger.error("config_manager", f"保存配置文件失败: {e}")
        return False


def test_llm_config(
    interface_format,
    api_key,
    base_url,
    model_name,
    temperature,
    max_tokens,
    timeout,
    log_func,
    handle_exception_func,
    success_callback=None,
):
    """
    测试LLM配置是否可用。

    该函数创建一个LLM适配器实例，发送测试提示词并验证响应。
    测试在独立线程中执行，避免阻塞用户界面。

    参数:
        interface_format: 接口格式（如"OpenAI"、"DeepSeek"等）
        api_key: API密钥
        base_url: API基础URL
        model_name: 模型名称
        temperature: 生成温度参数
        max_tokens: 最大Token数
        timeout: 请求超时时间（秒）
        log_func: 日志输出函数，用于显示测试进度和结果
        handle_exception_func: 异常处理函数
        success_callback: 成功回调函数，测试成功时调用

    返回值:
        无（异步执行，结果通过回调函数返回）

    异常:
        无直接抛出异常，异常通过handle_exception_func处理

    使用示例:
        >>> test_llm_config(
        ...     "OpenAI", "sk-xxx", "https://api.openai.com/v1",
        ...     "gpt-4", 0.7, 4096, 600,
        ...     print, lambda x: print(f"Error: {x}"), lambda: print("Success!")
        ... )

    设计说明:
        - 使用守护线程执行测试，程序退出时自动结束
        - 测试提示词为简单的"Please reply 'OK'"
        - 通过log_func回调实现UI友好的进度显示
    """

    def task():
        try:
            log_func("开始测试LLM配置...")
            llm_adapter = create_llm_adapter(
                interface_format=interface_format,
                base_url=base_url,
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            test_prompt = "Please reply 'OK'"
            response = llm_adapter.invoke(test_prompt)
            if response:
                log_func("✅ LLM配置测试成功！")
                log_func(f"测试回复: {response}")
                if success_callback:
                    success_callback()
            else:
                log_func("❌ LLM配置测试失败：未获取到响应")
                handle_exception_func("未获取到响应")
        except Exception as e:
            log_func(f"❌ LLM配置测试出错: {str(e)}")
            handle_exception_func(str(e))

    threading.Thread(target=task, daemon=True).start()


def test_embedding_config(
    api_key,
    base_url,
    interface_format,
    model_name,
    log_func,
    handle_exception_func,
    success_callback=None,
):
    """
    测试Embedding配置是否可用。

    该函数创建一个Embedding适配器实例，发送测试文本并验证返回的向量。
    测试在独立线程中执行，避免阻塞用户界面。

    参数:
        api_key: API密钥
        base_url: API基础URL
        interface_format: 接口格式（如"OpenAI"、"Ollama"等）
        model_name: Embedding模型名称
        log_func: 日志输出函数，用于显示测试进度和结果
        handle_exception_func: 异常处理函数
        success_callback: 成功回调函数，测试成功时调用

    返回值:
        无（异步执行，结果通过回调函数返回）

    异常:
        无直接抛出异常，异常通过handle_exception_func处理

    使用示例:
        >>> test_embedding_config(
        ...     "sk-xxx", "https://api.openai.com/v1",
        ...     "OpenAI", "text-embedding-ada-002",
        ...     print, lambda x: print(f"Error: {x}"), lambda: print("Success!")
        ... )

    设计说明:
        - 使用守护线程执行测试，程序退出时自动结束
        - 测试文本为简单的"测试文本"
        - 验证返回向量的维度，确保Embedding服务正常
    """

    def task():
        try:
            log_func("开始测试Embedding配置...")
            embedding_adapter = create_embedding_adapter(
                interface_format=interface_format,
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
            )

            test_text = "测试文本"
            embeddings = embedding_adapter.embed_query(test_text)
            if embeddings and len(embeddings) > 0:
                log_func("✅ Embedding配置测试成功！")
                log_func(f"生成的向量维度: {len(embeddings)}")
                if success_callback:
                    success_callback()
            else:
                log_func("❌ Embedding配置测试失败：未获取到向量")
                handle_exception_func("未获取到向量")
        except Exception as e:
            log_func(f"❌ Embedding配置测试出错: {str(e)}")
            handle_exception_func(str(e))

    threading.Thread(target=task, daemon=True).start()
