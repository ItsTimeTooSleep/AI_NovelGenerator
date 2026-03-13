# -*- coding: utf-8 -*-
"""
项目状态数据管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责统一管理项目的所有状态信息，包括：
- Step 1/2 的完成状态和阶段性数据
- 章节的草稿/定稿状态
- 生成步骤的时间记录

采用统一的 project_status.json 文件存储，支持一致性检查。

================================================================================
核心类
================================================================================
- ProjectStatusManager: 项目状态数据管理器
- StepStatus: 步骤状态数据类
- ChapterStatus: 章节状态数据类

================================================================================
状态文件格式
================================================================================
文件位置: {project_path}/project_status.json
文件格式: JSON

{
    "version": 1,
    "step1": {
        "completed": false,
        "current_step": 3,
        "total_steps": 6,
        "steps_time": {
            "书名生成": 12.5,
            "核心种子生成": 45.2
        },
        "partial_data": {
            "generated_title": "...",
            "core_seed_result": "..."
        }
    },
    "step2": {
        "completed": false,
        "current_step": 0,
        "total_steps": 3,
        "steps_time": {},
        "partial_data": {}
    },
    "chapters": {
        "1": {
            "draft_generated": true,
            "draft_generated_at": "2026-03-09T10:30:00",
            "finalized": false,
            "finalized_at": null,
            "word_count": 3500
        }
    },
    "last_finalized_chapter": 0
}

================================================================================
一致性检查策略
================================================================================
状态优先级: 文件实际状态 > 状态文件记录

检查规则:
1. Step 1 完成状态: 检查 Novel_architecture.txt 是否存在且有内容
2. Step 2 完成状态: 检查 Novel_directory.txt 是否存在且有内容
3. 章节草稿状态: 检查 chapter_{num}.txt 是否存在且有内容
4. 章节定稿状态: 检查 global_summary.txt 是否包含该章节信息

================================================================================
设计决策
================================================================================
- 统一状态文件，减少文件碎片
- 支持断点续传，中断后可从上次位置继续
- 一致性检查确保状态可靠性
- 与现有设计兼容

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.utils import check_file_has_valid_content, read_file

from ..core import BaseManager


@dataclass
class StepStatus:
    """
    步骤状态数据类

    Attributes:
        completed: 是否已完成
        current_step: 当前步骤索引（从0开始）
        total_steps: 总步骤数
        steps_time: 各步骤耗时记录 {步骤名: 耗时秒数}
        partial_data: 阶段性生成数据
    """

    completed: bool = False
    current_step: int = 0
    total_steps: int = 0
    steps_time: Dict[str, float] = field(default_factory=dict)
    partial_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChapterStatus:
    """
    章节状态数据类

    Attributes:
        draft_generated: 是否已生成草稿
        draft_generated_at: 草稿生成时间（ISO格式字符串）
        finalized: 是否已定稿
        finalized_at: 定稿时间（ISO格式字符串）
        word_count: 章节字数
    """

    draft_generated: bool = False
    draft_generated_at: Optional[str] = None
    finalized: bool = False
    finalized_at: Optional[str] = None
    word_count: int = 0


class ProjectStatusManager(BaseManager):
    """
    项目状态数据管理器

    负责统一管理项目的所有状态信息，包括：
    - Step 1/2 的完成状态和阶段性数据
    - 章节的草稿/定稿状态
    - 生成步骤的时间记录

    状态文件存储在项目根目录下，文件名为 project_status.json
    """

    STATUS_FILE_NAME = "project_status.json"
    FILE_VERSION = 1

    STEP1_TOTAL_STEPS = 6
    STEP2_TOTAL_STEPS = 3

    def __init__(self, home_tab):
        """
        初始化项目状态数据管理器

        Args:
            home_tab: HomeTab 实例，用于访问项目路径等
        """
        super().__init__(home_tab)
        self._project_path: Optional[str] = None
        self._step1_status: StepStatus = StepStatus(total_steps=self.STEP1_TOTAL_STEPS)
        self._step2_status: StepStatus = StepStatus(total_steps=self.STEP2_TOTAL_STEPS)
        self._chapters: Dict[str, ChapterStatus] = {}
        self._last_finalized_chapter: int = 0
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        初始化项目状态数据管理器

        加载状态文件并执行一致性检查。
        """
        self._initialized = True

    def set_project(self, project_path: str) -> None:
        """
        设置当前项目路径

        Args:
            project_path: 项目路径
        """
        self._project_path = project_path
        self._reset_status()
        if project_path:
            self._load_status_file()

    def _reset_status(self) -> None:
        """
        重置所有状态
        """
        self._step1_status = StepStatus(total_steps=self.STEP1_TOTAL_STEPS)
        self._step2_status = StepStatus(total_steps=self.STEP2_TOTAL_STEPS)
        self._chapters.clear()
        self._last_finalized_chapter = 0

    def _get_status_file_path(self) -> Optional[str]:
        """
        获取状态文件路径

        Returns:
            Optional[str]: 状态文件路径，如果项目路径未设置则返回 None
        """
        if not self._project_path:
            return None
        return os.path.join(self._project_path, self.STATUS_FILE_NAME)

    def _load_status_file(self) -> None:
        """
        加载状态文件

        如果文件不存在，创建默认状态文件。
        加载后执行一致性检查。
        """
        status_file_path = self._get_status_file_path()
        if not status_file_path:
            return

        if os.path.exists(status_file_path):
            try:
                with open(status_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                version = data.get("version", 1)

                step1_data = data.get("step1", {})
                self._step1_status = StepStatus(
                    completed=step1_data.get("completed", False),
                    current_step=step1_data.get("current_step", 0),
                    total_steps=step1_data.get("total_steps", self.STEP1_TOTAL_STEPS),
                    steps_time=step1_data.get("steps_time", {}),
                    partial_data=step1_data.get("partial_data", {}),
                )

                step2_data = data.get("step2", {})
                self._step2_status = StepStatus(
                    completed=step2_data.get("completed", False),
                    current_step=step2_data.get("current_step", 0),
                    total_steps=step2_data.get("total_steps", self.STEP2_TOTAL_STEPS),
                    steps_time=step2_data.get("steps_time", {}),
                    partial_data=step2_data.get("partial_data", {}),
                )

                chapters_data = data.get("chapters", {})
                for chap_num, chap_data in chapters_data.items():
                    self._chapters[chap_num] = ChapterStatus(
                        draft_generated=chap_data.get("draft_generated", False),
                        draft_generated_at=chap_data.get("draft_generated_at"),
                        finalized=chap_data.get("finalized", False),
                        finalized_at=chap_data.get("finalized_at"),
                        word_count=chap_data.get("word_count", 0),
                    )

                self._last_finalized_chapter = data.get("last_finalized_chapter", 0)

            except Exception as e:
                self._reset_status()

        self._run_consistency_check()

    def _save_status_file(self) -> bool:
        """
        保存状态文件

        Returns:
            bool: 保存是否成功
        """
        status_file_path = self._get_status_file_path()
        if not status_file_path:
            return False

        data = {
            "version": self.FILE_VERSION,
            "step1": asdict(self._step1_status),
            "step2": asdict(self._step2_status),
            "chapters": {
                chap_num: asdict(status) for chap_num, status in self._chapters.items()
            },
            "last_finalized_chapter": self._last_finalized_chapter,
        }

        try:
            with open(status_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False

    def _run_consistency_check(self) -> Dict[str, List[str]]:
        """
        执行一致性检查

        检查状态文件与实际文件是否一致，如果不一致则自动修正状态文件。

        Returns:
            Dict[str, List[str]]: 各类修正项的列表
        """
        if not self._project_path:
            return {}

        corrections: Dict[str, List[str]] = {
            "step1": [],
            "step2": [],
            "chapters": [],
        }

        arch_path = os.path.join(self._project_path, "Novel_architecture.txt")
        dir_path = os.path.join(self._project_path, "Novel_directory.txt")

        has_arch = check_file_has_valid_content(arch_path)
        has_dir = check_file_has_valid_content(dir_path)

        if self._step1_status.completed and not has_arch:
            self._step1_status.completed = False
            corrections["step1"].append("completed -> False")

        if has_arch and not self._step1_status.completed:
            self._step1_status.completed = True
            corrections["step1"].append("completed -> True")

        if self._step2_status.completed and not has_dir:
            self._step2_status.completed = False
            corrections["step2"].append("completed -> False")

        if has_dir and not self._step2_status.completed:
            self._step2_status.completed = True
            corrections["step2"].append("completed -> True")

        chapters_dir = os.path.join(self._project_path, "chapters")

        for chap_num, status in list(self._chapters.items()):
            chapter_file = os.path.join(chapters_dir, f"chapter_{chap_num}.txt")
            file_exists = check_file_has_valid_content(chapter_file)

            if status.draft_generated and not file_exists:
                status.draft_generated = False
                status.draft_generated_at = None
                status.word_count = 0
                status.finalized = False
                status.finalized_at = None
                corrections["chapters"].append(
                    f"chapter_{chap_num}: draft_generated -> False"
                )

            elif status.finalized and file_exists:
                if not self._check_chapter_in_summary(chap_num):
                    status.finalized = False
                    status.finalized_at = None
                    corrections["chapters"].append(
                        f"chapter_{chap_num}: finalized -> False"
                    )

        if os.path.exists(chapters_dir):
            for filename in os.listdir(chapters_dir):
                if filename.startswith("chapter_") and filename.endswith(".txt"):
                    try:
                        chap_num = filename.split("_")[1].split(".")[0]
                        chapter_file = os.path.join(chapters_dir, filename)
                        if check_file_has_valid_content(chapter_file):
                            if chap_num not in self._chapters:
                                self._chapters[chap_num] = ChapterStatus(
                                    draft_generated=True,
                                    draft_generated_at=None,
                                    finalized=False,
                                    finalized_at=None,
                                    word_count=self._count_words(chapter_file),
                                )
                                corrections["chapters"].append(
                                    f"chapter_{chap_num}: added"
                                )
                            elif not self._chapters[chap_num].draft_generated:
                                self._chapters[chap_num].draft_generated = True
                                self._chapters[chap_num].word_count = self._count_words(
                                    chapter_file
                                )
                                corrections["chapters"].append(
                                    f"chapter_{chap_num}: draft_generated -> True"
                                )
                    except (IndexError, ValueError):
                        pass

        self._last_finalized_chapter = self._calculate_last_finalized_chapter()

        has_corrections = any(corrections.values())
        if has_corrections:
            self._save_status_file()

        return corrections

    def _check_chapter_in_summary(self, chapter_num: str) -> bool:
        """
        检查章节是否在全局摘要中

        Args:
            chapter_num: 章节号

        Returns:
            bool: 是否在摘要中
        """
        if not self._project_path:
            return False

        summary_file = os.path.join(self._project_path, "global_summary.txt")
        if not os.path.exists(summary_file):
            return False

        try:
            summary_content = read_file(summary_file)
            return f"第{chapter_num}章" in summary_content
        except Exception:
            return False

    def _count_words(self, file_path: str) -> int:
        """
        统计文件字数

        Args:
            file_path: 文件路径

        Returns:
            int: 字数
        """
        try:
            content = read_file(file_path)
            return len(content.strip())
        except Exception:
            return 0

    def _calculate_last_finalized_chapter(self) -> int:
        """
        计算最后定稿的章节号

        Returns:
            int: 最后定稿的章节号
        """
        max_finalized = 0
        for chap_num, status in self._chapters.items():
            if status.finalized:
                try:
                    num = int(chap_num)
                    if num > max_finalized:
                        max_finalized = num
                except ValueError:
                    pass
        return max_finalized

    # ==================== Step 1 状态管理 ====================

    def is_step1_completed(self) -> bool:
        """
        检查 Step 1 是否已完成

        Returns:
            bool: 是否已完成
        """
        return self._step1_status.completed

    def get_step1_current_step(self) -> int:
        """
        获取 Step 1 当前步骤索引

        Returns:
            int: 当前步骤索引（从0开始）
        """
        return self._step1_status.current_step

    def get_step1_partial_data(self) -> Dict[str, Any]:
        """
        获取 Step 1 阶段性数据

        Returns:
            Dict[str, Any]: 阶段性数据
        """
        return self._step1_status.partial_data.copy()

    def get_step1_steps_time(self) -> Dict[str, float]:
        """
        获取 Step 1 各步骤耗时

        Returns:
            Dict[str, float]: 步骤耗时记录
        """
        return self._step1_status.steps_time.copy()

    def update_step1_progress(
        self,
        step_index: int,
        step_name: str,
        step_time: float,
        step_data_key: str,
        step_data_value: str,
    ) -> bool:
        """
        更新 Step 1 进度

        Args:
            step_index: 步骤索引（从0开始）
            step_name: 步骤名称
            step_time: 步骤耗时（秒）
            step_data_key: 数据键名
            step_data_value: 数据值

        Returns:
            bool: 操作是否成功
        """
        self._step1_status.current_step = step_index + 1
        self._step1_status.steps_time[step_name] = step_time
        self._step1_status.partial_data[step_data_key] = step_data_value
        return self._save_status_file()

    def mark_step1_completed(self) -> bool:
        """
        标记 Step 1 已完成

        Returns:
            bool: 操作是否成功
        """
        self._step1_status.completed = True
        self._step1_status.current_step = self._step1_status.total_steps
        return self._save_status_file()

    def reset_step1(self) -> bool:
        """
        重置 Step 1 状态

        Returns:
            bool: 操作是否成功
        """
        self._step1_status = StepStatus(total_steps=self.STEP1_TOTAL_STEPS)
        return self._save_status_file()

    # ==================== Step 2 状态管理 ====================

    def is_step2_completed(self) -> bool:
        """
        检查 Step 2 是否已完成

        Returns:
            bool: 是否已完成
        """
        return self._step2_status.completed

    def get_step2_current_step(self) -> int:
        """
        获取 Step 2 当前步骤索引

        Returns:
            int: 当前步骤索引（从0开始）
        """
        return self._step2_status.current_step

    def get_step2_partial_data(self) -> Dict[str, Any]:
        """
        获取 Step 2 阶段性数据

        Returns:
            Dict[str, Any]: 阶段性数据
        """
        return self._step2_status.partial_data.copy()

    def get_step2_steps_time(self) -> Dict[str, float]:
        """
        获取 Step 2 各步骤耗时

        Returns:
            Dict[str, float]: 步骤耗时记录
        """
        return self._step2_status.steps_time.copy()

    def update_step2_progress(
        self,
        step_index: int,
        step_name: str,
        step_time: float,
        step_data_key: str,
        step_data_value: str,
    ) -> bool:
        """
        更新 Step 2 进度

        Args:
            step_index: 步骤索引（从0开始）
            step_name: 步骤名称
            step_time: 步骤耗时（秒）
            step_data_key: 数据键名
            step_data_value: 数据值

        Returns:
            bool: 操作是否成功
        """
        self._step2_status.current_step = step_index + 1
        self._step2_status.steps_time[step_name] = step_time
        self._step2_status.partial_data[step_data_key] = step_data_value
        return self._save_status_file()

    def mark_step2_completed(self) -> bool:
        """
        标记 Step 2 已完成

        Returns:
            bool: 操作是否成功
        """
        self._step2_status.completed = True
        self._step2_status.current_step = self._step2_status.total_steps
        return self._save_status_file()

    def reset_step2(self) -> bool:
        """
        重置 Step 2 状态

        Returns:
            bool: 操作是否成功
        """
        self._step2_status = StepStatus(total_steps=self.STEP2_TOTAL_STEPS)
        return self._save_status_file()

    # ==================== 章节状态管理 ====================

    def get_chapter_status(self, chapter_num: int) -> ChapterStatus:
        """
        获取章节状态

        Args:
            chapter_num: 章节号

        Returns:
            ChapterStatus: 章节状态
        """
        chap_key = str(chapter_num)
        if chap_key not in self._chapters:
            self._chapters[chap_key] = ChapterStatus()
        return self._chapters[chap_key]

    def is_draft_generated(self, chapter_num: int) -> bool:
        """
        检查章节草稿是否已生成

        Args:
            chapter_num: 章节号

        Returns:
            bool: 是否已生成草稿
        """
        return self.get_chapter_status(chapter_num).draft_generated

    def is_finalized(self, chapter_num: int) -> bool:
        """
        检查章节是否已定稿

        Args:
            chapter_num: 章节号

        Returns:
            bool: 是否已定稿
        """
        return self.get_chapter_status(chapter_num).finalized

    def mark_draft_generated(self, chapter_num: int, word_count: int = 0) -> bool:
        """
        标记章节草稿已生成

        Args:
            chapter_num: 章节号
            word_count: 章节字数

        Returns:
            bool: 操作是否成功
        """
        chap_key = str(chapter_num)
        if chap_key not in self._chapters:
            self._chapters[chap_key] = ChapterStatus()

        self._chapters[chap_key].draft_generated = True
        self._chapters[chap_key].draft_generated_at = datetime.now().isoformat()
        self._chapters[chap_key].word_count = word_count

        return self._save_status_file()

    def mark_finalized(self, chapter_num: int) -> bool:
        """
        标记章节已定稿

        Args:
            chapter_num: 章节号

        Returns:
            bool: 操作是否成功
        """
        chap_key = str(chapter_num)
        if chap_key not in self._chapters:
            self._chapters[chap_key] = ChapterStatus()

        self._chapters[chap_key].finalized = True
        self._chapters[chap_key].finalized_at = datetime.now().isoformat()

        self._last_finalized_chapter = self._calculate_last_finalized_chapter()

        return self._save_status_file()

    def mark_draft_regenerating(self, chapter_num: int) -> bool:
        """
        标记章节正在重新生成草稿

        将定稿状态重置，因为重新生成草稿后需要重新定稿。

        Args:
            chapter_num: 章节号

        Returns:
            bool: 操作是否成功
        """
        chap_key = str(chapter_num)
        if chap_key not in self._chapters:
            self._chapters[chap_key] = ChapterStatus()

        self._chapters[chap_key].finalized = False
        self._chapters[chap_key].finalized_at = None

        self._last_finalized_chapter = self._calculate_last_finalized_chapter()

        return self._save_status_file()

    def get_last_finalized_chapter(self) -> int:
        """
        获取最后定稿的章节号

        Returns:
            int: 最后定稿的章节号，如果没有定稿的章节则返回 0
        """
        return self._last_finalized_chapter

    def get_all_chapters_status(self) -> Dict[int, ChapterStatus]:
        """
        获取所有章节状态

        Returns:
            Dict[int, ChapterStatus]: 章节状态字典
        """
        return {int(chap_num): status for chap_num, status in self._chapters.items()}

    def get_next_chapter_to_work_on(self) -> int:
        """
        获取下一个需要处理的章节号

        优先返回第一个未定稿的已生成章节，如果没有则返回第一个未生成的章节。

        Returns:
            int: 下一个需要处理的章节号，如果没有则返回 1
        """
        for chap_num in sorted(self._chapters.keys(), key=lambda x: int(x)):
            status = self._chapters[chap_num]
            if status.draft_generated and not status.finalized:
                return int(chap_num)

        max_chapter = 0
        for chap_num in self._chapters.keys():
            try:
                num = int(chap_num)
                if num > max_chapter:
                    max_chapter = num
            except ValueError:
                pass

        return max_chapter + 1 if max_chapter > 0 else 1

    # ==================== 公共方法 ====================

    def run_consistency_check(self) -> Dict[str, List[str]]:
        """
        公开的一致性检查方法

        Returns:
            Dict[str, List[str]]: 各类修正项的列表
        """
        return self._run_consistency_check()

    def save(self) -> bool:
        """
        保存状态文件

        Returns:
            bool: 保存是否成功
        """
        return self._save_status_file()

    def cleanup(self) -> None:
        """
        清理资源
        """
        self._reset_status()
        self._project_path = None
        self._initialized = False
