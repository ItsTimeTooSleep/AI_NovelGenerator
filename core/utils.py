# -*- coding: utf-8 -*-
"""
工具函数模块

================================================================================
模块功能概述
================================================================================
本模块提供AI小说生成器中常用的文件操作工具函数，包括：
- 文件读取与写入
- 文件内容追加
- JSON数据保存

================================================================================
核心函数
================================================================================
1. read_file: 读取文件全部内容
2. append_text_to_file: 在文件末尾追加文本
3. clear_file_content: 清空文件内容
4. save_string_to_txt: 将字符串保存为txt文件
5. save_data_to_json: 将字典数据保存为JSON文件

================================================================================
设计决策
================================================================================
- 所有函数统一使用UTF-8编码，确保中文等字符正确处理
- 异常处理采用打印错误信息而非抛出异常，简化调用方处理
- 函数设计简洁，专注于单一功能

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json


def read_file(filename: str) -> str:
    """
    读取文件的全部内容。

    该函数尝试读取指定文件的全部文本内容。如果文件不存在或读取失败，
    返回空字符串而不是抛出异常。

    参数:
        filename: 要读取的文件路径

    返回值:
        str: 文件的全部文本内容。如果文件不存在或读取失败，返回空字符串

    异常:
        无直接抛出异常，内部捕获FileNotFoundError和其他异常

    使用示例:
        >>> content = read_file("novel.txt")
        >>> if content:
        ...     print(f"文件内容长度: {len(content)}")

    设计说明:
        - 使用UTF-8编码读取文件
        - 文件不存在时静默返回空字符串，便于调用方处理
        - 错误信息打印到控制台，便于调试
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[read_file] 读取文件时发生错误: {e}")
        return ""


def append_text_to_file(text_to_append: str, file_path: str):
    """
    在文件末尾追加文本。

    该函数将文本追加到指定文件的末尾。如果文本不以换行符开头，
    会自动在文本前添加换行符，确保追加内容在新行开始。

    参数:
        text_to_append: 要追加的文本内容
        file_path: 目标文件路径

    返回值:
        无

    异常:
        无直接抛出异常，内部捕获IOError并打印错误信息

    使用示例:
        >>> append_text_to_file("新的一行内容", "novel.txt")

    设计说明:
        - 使用追加模式('a')打开文件，保留原有内容
        - 自动添加换行符确保格式规范
        - 使用UTF-8编码写入
    """
    if text_to_append and not text_to_append.startswith("\n"):
        text_to_append = "\n" + text_to_append

    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(text_to_append)
    except IOError as e:
        print(f"[append_text_to_file] 发生错误：{e}")


def clear_file_content(filename: str):
    """
    清空指定文件的内容。

    该函数以写入模式打开文件，会清空文件原有内容但保留文件本身。

    参数:
        filename: 要清空的文件路径

    返回值:
        无

    异常:
        无直接抛出异常，内部捕获IOError并打印错误信息

    使用示例:
        >>> clear_file_content("temp.txt")

    设计说明:
        - 使用写入模式('w')打开文件，自动清空内容
        - 文件不存在时会创建空文件
    """
    try:
        with open(filename, "w", encoding="utf-8"):
            pass
    except IOError as e:
        print(f"[clear_file_content] 无法清空文件 '{filename}' 的内容：{e}")


def save_string_to_txt(content: str, filename: str):
    """
    将字符串保存为txt文件。

    该函数将字符串内容写入指定文件，会覆盖文件原有内容。

    参数:
        content: 要保存的字符串内容
        filename: 目标文件路径

    返回值:
        无

    异常:
        无直接抛出异常，内部捕获所有异常并打印错误信息

    使用示例:
        >>> save_string_to_txt("这是小说内容", "chapter1.txt")

    设计说明:
        - 使用覆盖写入模式，原有内容会被替换
        - 使用UTF-8编码确保中文正确保存
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        print(f"[save_string_to_txt] 保存文件时发生错误: {e}")


def save_data_to_json(data: dict, file_path: str) -> bool:
    """
    将字典数据保存为JSON文件。

    该函数将Python字典序列化为JSON格式并保存到文件。
    使用格式化输出，便于人工阅读。

    参数:
        data: 要保存的字典数据
        file_path: 目标JSON文件路径

    返回值:
        bool: 保存成功返回True，失败返回False

    异常:
        无直接抛出异常，内部捕获所有异常并返回False

    使用示例:
        >>> config = {"theme": "Dark", "language": "zh-CN"}
        >>> success = save_data_to_json(config, "config.json")
        >>> print(f"保存{'成功' if success else '失败'}")

    设计说明:
        - 使用ensure_ascii=False保留非ASCII字符
        - 使用indent=4格式化输出，提高可读性
        - 返回布尔值便于调用方判断保存结果
    """
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"[save_data_to_json] 保存数据到JSON文件时出错: {e}")
        return False


def is_placeholder_text(text: str) -> bool:
    """
    检查文本是否是占位符/提示文本。

    该函数用于识别系统生成的提示信息，这些文本不应被视为有效的章节内容。

    参数:
        text: 要检查的文本内容

    返回值:
        bool: True表示是占位符文本，False表示是有效内容

    使用示例:
        >>> is_placeholder_text("第1章还未生成，请先生成草稿")
        True
        >>> is_placeholder_text("第一章 开始\\n\\n这是一个关于...")
        False

    设计说明:
        - 检查常见的占位符模式
        - 空文本被视为占位符
        - 用于章节内容有效性验证
    """
    if not text:
        return True

    text = text.strip()
    if not text:
        return True

    placeholder_patterns = [
        "还未生成，请先生成草稿",
        "内容为空",
        "正在加载第",
        "没有打开的项目",
        "加载失败:",
    ]

    for pattern in placeholder_patterns:
        if pattern in text:
            return True

    return False


def check_file_has_valid_content(file_path: str) -> bool:
    """
    检查文件是否存在且包含有效内容（非占位符文本）。

    该函数结合文件存在性检查和内容有效性验证，
    用于判断章节文件是否真正包含用户生成的内容。

    参数:
        file_path: 要检查的文件路径

    返回值:
        bool: True表示文件存在且包含有效内容，False表示文件不存在或只有占位符

    异常:
        无直接抛出异常，内部捕获所有异常并返回False

    使用示例:
        >>> if check_file_has_valid_content("chapters/chapter_1.txt"):
        ...     print("章节已生成")
        ... else:
        ...     print("章节未生成或为空")

    设计说明:
        - 先检查文件是否存在
        - 再检查内容是否为占位符
        - 统一的文件内容验证逻辑
    """
    import os

    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return False
            return not is_placeholder_text(content)
    except Exception:
        return False
