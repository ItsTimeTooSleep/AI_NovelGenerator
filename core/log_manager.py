# -*- coding: utf-8 -*-
"""
统一日志管理器模块

================================================================================
模块功能概述
================================================================================
本模块提供统一的日志管理功能，支持：
- 毫秒级时间戳（精确到微秒）
- 结构化日志格式
- 日志分级（DEBUG/INFO/WARN/ERROR）
- 同时输出到文件和UI日志面板
- 支持日志时间轴功能

================================================================================
核心类与函数
================================================================================
- LogLevel: 日志级别枚举
- LogManager: 日志管理器主类
- get_logger: 获取全局日志管理器实例

================================================================================
日志格式
================================================================================
[YYYY-MM-DD HH:MM:SS.ffffff [LEVEL] [模块名] 消息内容

例如：
[2026-03-03 14:30:45.123456] [INFO] [main_qt] 应用程序启动

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import os
import sys
from threading import Lock
from typing import Callable, Optional


class LogLevel(Enum):
    """
    日志级别枚举

    Attributes:
        DEBUG: 调试信息，用于开发调试
        INFO: 一般信息，用于记录正常流程
        WARN: 警告信息，用于记录非严重问题
        ERROR: 错误信息，用于记录错误和异常
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR


@dataclass
class LogRecord:
    """
    日志记录数据类

    Attributes:
        timestamp: 时间戳（datetime对象）
        level: 日志级别
        module: 模块名
        message: 日志消息
        extra: 额外信息（可选）
    """

    timestamp: datetime
    level: LogLevel
    module: str
    message: str
    extra: Optional[dict] = None

    def to_formatted_string(self) -> str:
        """
        将日志记录转换为格式化字符串

        Returns:
            str: 格式化后的日志字符串
        """
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        level_str = self.level.name
        return f"[{timestamp_str}] [{level_str}] [{self.module}] {self.message}"


class LogManager:
    """
    统一日志管理器

    负责管理日志的初始化、记录和分发。

    Attributes:
        _instance: 单例实例
        _lock: 线程锁
        _logger: 标准logging.Logger实例
        _ui_callback: UI日志回调函数
        _log_records: 日志记录列表（用于时间轴）
        _max_records: 最大保留记录数
    """

    _instance: Optional["LogManager"] = None
    _lock: Lock = Lock()

    def __new__(cls):
        """
        单例模式创建实例

        Returns:
            LogManager: 日志管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化日志管理器

        注意：由于使用单例模式，此方法可能被多次调用，但只会初始化一次。
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._logger: Optional[logging.Logger] = None
        self._ui_callback: Optional[Callable[[LogRecord], None]] = None
        self._log_records: list[LogRecord] = []
        self._max_records: int = 1000
        self._configured_level: LogLevel = LogLevel.INFO
        self._initialized: bool = True

    def initialize(
        self,
        log_file: str = "app.log",
        level: LogLevel = LogLevel.INFO,
        max_records: int = 1000,
        log_dir: Optional[str] = None,
    ) -> None:
        """
        初始化日志系统

        Args:
            log_file: 日志文件名
            level: 日志级别（用于文件和UI显示）
            max_records: 内存中保留的最大记录数
            log_dir: 日志目录（可选，默认为当前目录）

        Returns:
            None
        """
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, log_file) if log_dir else log_file

        self._max_records = max_records
        self._configured_level = level

        self._logger = logging.getLogger("AI_NovelGenerator")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()

        class CustomFormatter(logging.Formatter):
            def format(self, record):
                record.asctime = self.formatTime(record, self.datefmt)
                msecs = int(record.msecs)
                timestamp = f"{record.asctime}.{msecs:03d}"
                return f"[{timestamp}] [{record.levelname}] [{getattr(record, 'custom_module', 'unknown')}] {record.getMessage()}"

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level.value)

        formatter = CustomFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        self.info("log_manager", "日志系统初始化完成")

    def set_ui_callback(self, callback: Callable[[LogRecord], None]) -> None:
        """
        设置UI日志回调函数

        Args:
            callback: 回调函数，接收LogRecord对象
        """
        self._ui_callback = callback

    def _add_record(self, record: LogRecord) -> None:
        """
        添加日志记录到内存列表

        Args:
            record: 日志记录
        """
        self._log_records.append(record)

        if len(self._log_records) > self._max_records:
            self._log_records = self._log_records[-self._max_records :]

    def _log(
        self, level: LogLevel, module: str, message: str, extra: Optional[dict] = None
    ) -> None:
        """
        内部日志记录方法

        Args:
            level: 日志级别
            module: 模块名
            message: 日志消息
            extra: 额外信息
        """
        timestamp = datetime.now()
        record = LogRecord(
            timestamp=timestamp,
            level=level,
            module=module,
            message=message,
            extra=extra,
        )

        self._add_record(record)

        if self._logger:
            log_method = getattr(self._logger, level.name.lower())
            log_method(message, extra={"custom_module": module})

        if self._ui_callback:
            try:
                self._ui_callback(record)
            except Exception as e:
                print(f"UI日志回调失败: {e}")

    def debug(self, module: str, message: str, extra: Optional[dict] = None) -> None:
        """
        记录DEBUG级别日志

        Args:
            module: 模块名
            message: 日志消息
            extra: 额外信息
        """
        self._log(LogLevel.DEBUG, module, message, extra)

    def info(self, module: str, message: str, extra: Optional[dict] = None) -> None:
        """
        记录INFO级别日志

        Args:
            module: 模块名
            message: 日志消息
            extra: 额外信息
        """
        self._log(LogLevel.INFO, module, message, extra)

    def warn(self, module: str, message: str, extra: Optional[dict] = None) -> None:
        """
        记录WARN级别日志

        Args:
            module: 模块名
            message: 日志消息
            extra: 额外信息
        """
        self._log(LogLevel.WARN, module, message, extra)

    def error(self, module: str, message: str, extra: Optional[dict] = None) -> None:
        """
        记录ERROR级别日志

        Args:
            module: 模块名
            message: 日志消息
            extra: 额外信息
        """
        self._log(LogLevel.ERROR, module, message, extra)

    def get_log_records(
        self,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[LogRecord]:
        """
        获取日志记录

        Args:
            level: 过滤日志级别（可选）
            module: 过滤模块名（可选）
            limit: 返回记录数限制（可选）

        Returns:
            list[LogRecord]: 日志记录列表
        """
        records = self._log_records.copy()

        if level:
            records = [r for r in records if r.level == level]

        if module:
            records = [r for r in records if r.module == module]

        if limit:
            records = records[-limit:]

        return records

    def clear_records(self) -> None:
        """
        清空内存中的日志记录"""
        self._log_records.clear()

    def set_level(self, level: LogLevel) -> None:
        """
        设置日志级别（仅影响文件处理器）

        Args:
            level: 日志级别
        """
        self._configured_level = level
        if self._logger:
            for handler in self._logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.setLevel(level.value)

    def get_configured_level(self) -> LogLevel:
        """
        获取配置的日志级别

        Returns:
            LogLevel: 配置的日志级别
        """
        if hasattr(self, "_configured_level"):
            return self._configured_level
        return LogLevel.INFO

    def is_debug_enabled(self) -> bool:
        """
        检查是否启用了DEBUG级别日志

        Returns:
            bool: 如果当前日志级别为DEBUG则返回True
        """
        if self._logger:
            return self._logger.level <= logging.DEBUG
        return False


def get_logger() -> LogManager:
    """
    获取全局日志管理器实例

    Returns:
        LogManager: 日志管理器单例
    """
    return LogManager()
