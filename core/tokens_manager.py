# -*- coding: utf-8 -*-
"""
Token消耗记录管理器
=====================

本模块实现了Token消耗记录和管理功能，包括：
- Token记录数据结构定义
- Token记录的添加、查询和统计
- Token数据的持久化存储
- 按章节、步骤、模型等维度的统计分析
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional
from core import get_logger


class TokenUsageRecord:
    """
    Token使用记录数据结构

    用于记录单次LLM调用的Token消耗信息
    """

    def __init__(
        self,
        step_name: str,
        model_name: str,
        model_version: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        total_tokens: int = 0,
        chapter_number: Optional[int] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        input_estimated: bool = False,
        output_estimated: bool = False,
    ):
        """
        初始化Token使用记录

        Args:
            step_name: 步骤名称（如"架构生成"、"第三章草稿"等）
            model_name: 使用的模型名称
            model_version: 模型版本（可选）
            input_tokens: 输入Token数量
            output_tokens: 输出Token数量
            cached_tokens: 缓存Token数量
            total_tokens: 总Token数量
            chapter_number: 关联的章节编号（可选）
            timestamp: 时间戳（可选，默认为当前时间）
            metadata: 额外的元数据（可选）
            input_estimated: 输入Token是否为估算值
            output_estimated: 输出Token是否为估算值
        """
        self.step_name = step_name
        self.model_name = model_name
        self.model_version = model_version
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cached_tokens = cached_tokens
        self.total_tokens = (
            total_tokens if total_tokens > 0 else input_tokens + output_tokens
        )
        self.chapter_number = chapter_number
        self.timestamp = timestamp or datetime.now().isoformat()
        self.metadata = metadata or {}
        self.input_estimated = input_estimated
        self.output_estimated = output_estimated

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Token记录的字典表示
        """
        return {
            "step_name": self.step_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": self.total_tokens,
            "chapter_number": self.chapter_number,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "input_estimated": self.input_estimated,
            "output_estimated": self.output_estimated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsageRecord":
        """
        从字典创建Token记录

        Args:
            data: Token记录的字典数据

        Returns:
            TokenUsageRecord实例
        """
        return cls(
            step_name=data.get("step_name", ""),
            model_name=data.get("model_name", ""),
            model_version=data.get("model_version"),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            cached_tokens=data.get("cached_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            chapter_number=data.get("chapter_number"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata"),
            input_estimated=data.get("input_estimated", False),
            output_estimated=data.get("output_estimated", False),
        )


class TokensManager:
    """
    Token记录管理器

    负责管理小说项目的Token消耗记录
    """

    def __init__(self, project_path: Optional[str] = None):
        """
        初始化Token记录管理器

        Args:
            project_path: 项目路径（可选，用于持久化存储）
        """
        self.records: List[TokenUsageRecord] = []
        self.project_path = project_path
        self.tokens_file: Optional[str] = None
        self._logger = get_logger()

        if project_path:
            self.tokens_file = os.path.join(project_path, "token_usage.json")
            self.load_records()
            self._logger.debug(
                "tokens_manager", f"TokensManager初始化: 项目路径={project_path}"
            )

    def add_record(self, record: TokenUsageRecord) -> None:
        """
        添加一条Token使用记录

        Args:
            record: Token使用记录
        """
        self.records.append(record)
        self.save_records()
        self._logger.debug(
            "tokens_manager",
            f"添加Token记录: 步骤={record.step_name}, 模型={record.model_name}, 总Token={record.total_tokens}",
        )

    def get_records_by_chapter(self, chapter_number: int) -> List[TokenUsageRecord]:
        """
        获取指定章节的所有Token记录

        Args:
            chapter_number: 章节编号

        Returns:
            该章节的Token记录列表
        """
        return [r for r in self.records if r.chapter_number == chapter_number]

    def get_records_by_step(self, step_name: str) -> List[TokenUsageRecord]:
        """
        获取指定步骤的所有Token记录

        Args:
            step_name: 步骤名称

        Returns:
            该步骤的Token记录列表
        """
        return [r for r in self.records if r.step_name == step_name]

    def get_records_by_model(self, model_name: str) -> List[TokenUsageRecord]:
        """
        获取指定模型的所有Token记录

        Args:
            model_name: 模型名称

        Returns:
            该模型的Token记录列表
        """
        return [r for r in self.records if r.model_name == model_name]

    def get_total_stats(self) -> Dict[str, Any]:
        """
        获取总体统计信息

        Returns:
            包含总体统计的字典
        """
        if not self.records:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cached_tokens": 0,
                "total_tokens": 0,
                "record_count": 0,
                "unknown_input_count": 0,
                "unknown_output_count": 0,
            }

        total_input = sum(r.input_tokens for r in self.records if r.input_tokens >= 0)
        total_output = sum(
            r.output_tokens for r in self.records if r.output_tokens >= 0
        )
        unknown_input_count = sum(1 for r in self.records if r.input_tokens == -1)
        unknown_output_count = sum(1 for r in self.records if r.output_tokens == -1)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cached_tokens": sum(r.cached_tokens for r in self.records),
            "total_tokens": sum(
                r.total_tokens for r in self.records if r.total_tokens >= 0
            ),
            "record_count": len(self.records),
            "unknown_input_count": unknown_input_count,
            "unknown_output_count": unknown_output_count,
        }

    def get_chapter_stats(self, chapter_number: int) -> Dict[str, Any]:
        """
        获取指定章节的统计信息

        Args:
            chapter_number: 章节编号

        Returns:
            包含章节统计的字典
        """
        chapter_records = self.get_records_by_chapter(chapter_number)

        if not chapter_records:
            return {
                "chapter_number": chapter_number,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cached_tokens": 0,
                "total_tokens": 0,
                "record_count": 0,
                "unknown_input_count": 0,
                "unknown_output_count": 0,
            }

        return {
            "chapter_number": chapter_number,
            "total_input_tokens": sum(
                r.input_tokens for r in chapter_records if r.input_tokens >= 0
            ),
            "total_output_tokens": sum(
                r.output_tokens for r in chapter_records if r.output_tokens >= 0
            ),
            "total_cached_tokens": sum(r.cached_tokens for r in chapter_records),
            "total_tokens": sum(
                r.total_tokens for r in chapter_records if r.total_tokens >= 0
            ),
            "record_count": len(chapter_records),
            "unknown_input_count": sum(
                1 for r in chapter_records if r.input_tokens == -1
            ),
            "unknown_output_count": sum(
                1 for r in chapter_records if r.output_tokens == -1
            ),
        }

    def get_model_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取按模型分类的统计信息

        Returns:
            按模型名称分组的统计字典
        """
        model_stats: Dict[str, Dict[str, Any]] = {}

        for record in self.records:
            if record.model_name not in model_stats:
                model_stats[record.model_name] = {
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cached_tokens": 0,
                    "total_tokens": 0,
                    "record_count": 0,
                    "unknown_input_count": 0,
                    "unknown_output_count": 0,
                }

            if record.input_tokens >= 0:
                model_stats[record.model_name][
                    "total_input_tokens"
                ] += record.input_tokens
            else:
                model_stats[record.model_name]["unknown_input_count"] += 1

            if record.output_tokens >= 0:
                model_stats[record.model_name][
                    "total_output_tokens"
                ] += record.output_tokens
            else:
                model_stats[record.model_name]["unknown_output_count"] += 1

            model_stats[record.model_name][
                "total_cached_tokens"
            ] += record.cached_tokens
            if record.total_tokens >= 0:
                model_stats[record.model_name]["total_tokens"] += record.total_tokens
            model_stats[record.model_name]["record_count"] += 1

        return model_stats

    def get_step_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取按步骤分类的统计信息

        Returns:
            按步骤名称分组的统计字典
        """
        step_stats: Dict[str, Dict[str, Any]] = {}

        for record in self.records:
            if record.step_name not in step_stats:
                step_stats[record.step_name] = {
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cached_tokens": 0,
                    "total_tokens": 0,
                    "record_count": 0,
                    "chapter_number": record.chapter_number,
                    "unknown_input_count": 0,
                    "unknown_output_count": 0,
                }

            if record.input_tokens >= 0:
                step_stats[record.step_name][
                    "total_input_tokens"
                ] += record.input_tokens
            else:
                step_stats[record.step_name]["unknown_input_count"] += 1

            if record.output_tokens >= 0:
                step_stats[record.step_name][
                    "total_output_tokens"
                ] += record.output_tokens
            else:
                step_stats[record.step_name]["unknown_output_count"] += 1

            step_stats[record.step_name]["total_cached_tokens"] += record.cached_tokens
            if record.total_tokens >= 0:
                step_stats[record.step_name]["total_tokens"] += record.total_tokens
            step_stats[record.step_name]["record_count"] += 1

        return step_stats

    def get_all_chapters_stats(self) -> Dict[int, Dict[str, Any]]:
        """
        获取所有章节的统计信息

        Returns:
            按章节编号分组的统计字典
        """
        chapter_numbers = sorted(
            set(r.chapter_number for r in self.records if r.chapter_number is not None)
        )
        return {num: self.get_chapter_stats(num) for num in chapter_numbers}

    def get_all_records(
        self, sort_by_timestamp: bool = True, descending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取所有记录的字典列表

        Args:
            sort_by_timestamp: 是否按时间戳排序
            descending: 是否降序排列（最新记录在前）

        Returns:
            Token记录字典列表
        """
        records_dict = [r.to_dict() for r in self.records]

        if sort_by_timestamp:
            records_dict.sort(key=lambda x: x.get("timestamp", ""), reverse=descending)

        return records_dict

    def save_records(self) -> bool:
        """
        保存Token记录到文件

        Returns:
            是否保存成功
        """
        if not self.tokens_file:
            return False

        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "records": [r.to_dict() for r in self.records],
            }

            with open(self.tokens_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self._logger.debug(
                "tokens_manager",
                f"Token记录保存成功: {self.tokens_file}, 记录数={len(self.records)}",
            )
            return True
        except Exception as e:
            self._logger.error("tokens_manager", f"保存Token记录失败: {e}")
            return False

    def load_records(self) -> bool:
        """
        从文件加载Token记录

        Returns:
            是否加载成功
        """
        if not self.tokens_file or not os.path.exists(self.tokens_file):
            return False

        try:
            with open(self.tokens_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.records = [
                TokenUsageRecord.from_dict(record_data)
                for record_data in data.get("records", [])
            ]

            self._logger.debug(
                "tokens_manager",
                f"Token记录加载成功: {self.tokens_file}, 记录数={len(self.records)}",
            )
            return True
        except Exception as e:
            self._logger.error("tokens_manager", f"加载Token记录失败: {e}")
            return False

    def clear_records(self) -> None:
        """
        清空所有Token记录
        """
        self.records = []
        self.save_records()


# 全局Token上下文，用于在LLM调用过程中传递Token记录信息
_token_context: Optional[Dict[str, Any]] = None


def set_token_context(
    step_name: str,
    chapter_number: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    设置当前Token上下文

    Args:
        step_name: 步骤名称
        chapter_number: 章节编号（可选）
        metadata: 额外元数据（可选）
    """
    global _token_context
    _token_context = {
        "step_name": step_name,
        "chapter_number": chapter_number,
        "metadata": metadata or {},
    }


def get_token_context() -> Optional[Dict[str, Any]]:
    """
    获取当前Token上下文

    Returns:
        Token上下文字典，如果没有设置则返回None
    """
    return _token_context


def clear_token_context() -> None:
    """
    清除当前Token上下文
    """
    global _token_context
    _token_context = None
