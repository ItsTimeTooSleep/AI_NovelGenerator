# -*- coding: utf-8 -*-
"""
小说生成器模块包

================================================================================
模块功能概述
================================================================================
本包是AI小说生成器的核心业务逻辑层，实现小说从构思到成稿的完整生成流程。
采用分阶段生成策略，支持断点续传和增量生成。

================================================================================
模块结构
================================================================================
- architecture: 小说架构生成（核心种子、角色、世界观、情节）
- blueprint: 章节蓝图生成（章节目录规划）
- chapter: 章节草稿生成（正文内容创作）
- finalization: 章节定稿处理（摘要更新、状态同步、向量入库）
- knowledge: 知识库导入（外部资料向量化）
- vectorstore_utils: 向量存储工具（语义检索支持）
- composer: AI写作助手（语法修正、润色、扩写）
- project_manager: 项目管理器（项目创建、加载、保存）
- common: 通用工具函数（重试机制、日志记录）

================================================================================
生成流程
================================================================================
Step 1: 小说架构生成
    ├── 核心种子：故事核心单句概括
    ├── 角色动力学：角色设计与关系网络
    ├── 初始角色状态：角色属性初始化
    ├── 世界观：物理/社会/隐喻三维世界
    └── 情节架构：三幕式剧情结构

Step 2: 章节蓝图生成
    └── 生成所有章节的定位、作用、悬念等元信息

Step 3: 章节内容生成
    ├── 知识库检索：获取相关参考资料
    ├── 摘要生成：前文摘要更新
    └── 正文创作：基于蓝图生成章节内容

Step 4: 章节定稿
    ├── 更新全局摘要
    ├── 更新角色状态
    └── 向量入库：支持后续检索

================================================================================
设计决策
================================================================================
- 采用生成器模式实现步骤进度反馈
- 支持断点续传，中断后可从上次位置继续
- 集成向量检索，实现知识库辅助创作
- 分层架构，业务逻辑与UI解耦

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

from .architecture import Novel_architecture_generate
from .blueprint import Chapter_blueprint_generate
from .chapter import build_chapter_prompt, generate_chapter_draft
from .finalization import finalize_chapter, FinalizationError
from .knowledge import import_knowledge_file
from .vectorstore_utils import clear_vector_store

__all__ = [
    "Novel_architecture_generate",
    "Chapter_blueprint_generate",
    "build_chapter_prompt",
    "generate_chapter_draft",
    "finalize_chapter",
    "FinalizationError",
    "import_knowledge_file",
    "clear_vector_store",
]
