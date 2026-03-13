# -*- coding: utf-8 -*-
"""
项目管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责小说项目的创建、加载、保存等生命周期管理。
每个小说项目是一个独立的文件夹，包含配置文件、章节文件、向量库等。

================================================================================
核心类
================================================================================
- ProjectManager: 项目管理器主类

================================================================================
核心功能
================================================================================
- list_projects: 列出所有现有项目
- create_project: 创建新项目
- load_project: 加载已有项目
- save_project_config: 保存项目配置
- update_current_project: 更新项目配置项

================================================================================
项目结构
================================================================================
项目目录/
├── project.json          # 项目配置文件
├── Novel_architecture.txt # 小说架构
├── Novel_directory.txt   # 章节蓝图
├── character_state.txt   # 角色状态
├── global_summary.txt    # 全局摘要
├── chapters/             # 章节文件目录
├── characters/           # 角色文件目录
└── vectorstore/          # 向量库目录

================================================================================
设计决策
================================================================================
- 使用JSON格式存储项目配置，便于读写
- 支持封面图片存储
- 集成Token管理器，统计项目消耗
- 向后兼容旧版本项目配置

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import json
import os
import shutil
from typing import Dict, List, Optional

try:
    from core.tokens_manager import TokensManager

    TOKENS_MANAGER_AVAILABLE = True
except ImportError:
    TOKENS_MANAGER_AVAILABLE = False

try:
    from core import get_logger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class ProjectManager:
    def __init__(self, base_dir: str = "novels"):
        """
        初始化项目管理器
        :param base_dir: 小说存储的根目录
        """
        if LOGGER_AVAILABLE:
            self.logger = get_logger()
        else:
            self.logger = None

        # 获取绝对路径，确保在不同环境下都能正确定位
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.getcwd(), base_dir)

        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        self.current_project: Optional[Dict] = None
        self.tokens_manager: Optional[TokensManager] = None

        if self.logger:
            self.logger.info(
                "project_manager", f"项目管理器初始化完成，基础目录: {base_dir}"
            )

    def list_projects(self) -> List[Dict]:
        """
        列出所有现有项目
        :return: 项目配置列表
        """
        projects = []
        if not os.path.exists(self.base_dir):
            return projects

        for name in os.listdir(self.base_dir):
            path = os.path.join(self.base_dir, name)
            config_path = os.path.join(path, "project.json")

            if os.path.isdir(path) and os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 确保基本字段存在
                        if "name" not in data:
                            data["name"] = name
                        data["path"] = path
                        projects.append(data)
                except Exception as e:
                    print(f"Error loading project {name}: {e}")

        # 按修改时间排序（可选）
        return projects

    def create_project(self, name: str, **kwargs) -> str:
        """
        创建新项目

        Args:
            name: 项目名称（书名），可为空（将自动生成临时名称）
            **kwargs: 其他配置参数 (author, genre, topic, cover_path, etc.)

        Returns:
            str: 项目路径

        Raises:
            FileExistsError: 项目已存在
        """
        if self.logger:
            self.logger.info(
                "project_manager", f"开始创建新项目: {name if name else '(待生成)'}"
            )

        if not name or not name.strip():
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"未命名小说_{timestamp}"
            if self.logger:
                self.logger.info("project_manager", f"书名为空，使用临时名称: {name}")

        # 清理文件名中的非法字符
        safe_name = "".join(
            [
                c
                for c in name
                if c.isalnum() or c in (" ", "-", "_", "(", ")", "《", "》")
            ]
        ).strip()
        if not safe_name:
            if self.logger:
                self.logger.error("project_manager", f"项目名称无效: {name}")
            raise ValueError("无效的项目名称")

        project_path = os.path.join(self.base_dir, safe_name)

        if os.path.exists(project_path):
            if self.logger:
                self.logger.error("project_manager", f"项目已存在: {safe_name}")
            raise FileExistsError(f"项目 '{safe_name}' 已存在")

        os.makedirs(project_path)
        if self.logger:
            self.logger.debug("project_manager", f"创建项目目录: {project_path}")

        # 处理封面图片
        cover_path = kwargs.get("cover_path")
        saved_cover_path = ""
        if cover_path and os.path.exists(cover_path):
            try:
                ext = os.path.splitext(cover_path)[1]
                saved_cover_name = f"cover{ext}"
                saved_cover_path = saved_cover_name
                shutil.copy2(cover_path, os.path.join(project_path, saved_cover_name))
                if self.logger:
                    self.logger.info("project_manager", "复制封面图片成功")
            except Exception as e:
                if self.logger:
                    self.logger.error("project_manager", f"复制封面图片失败: {e}")
                else:
                    print(f"Failed to copy cover image: {e}")

        # 默认配置结构
        config = {
            "name": name,
            "created_at": __import__("datetime").datetime.now().isoformat(),
            "updated_at": __import__("datetime").datetime.now().isoformat(),
            "genre": kwargs.get("genre", "未分类"),
            "topic": kwargs.get("topic", ""),
            "author": kwargs.get("author", "未知"),
            "cover_image": saved_cover_path,
            # 不可变参数
            "total_chapters_plan": kwargs.get("total_chapters_plan", 100),
            "words_per_chapter_plan": kwargs.get("words_per_chapter_plan", 3000),
            # 可变参数
            "current_chapter": 1,
            "user_guidance": kwargs.get("user_guidance", ""),
        }

        self.save_project_config(project_path, config)

        # 创建必要的子目录
        os.makedirs(os.path.join(project_path, "chapters"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "characters"), exist_ok=True)

        if self.logger:
            self.logger.info(
                "project_manager", f"项目创建成功: {name}, 路径: {project_path}"
            )

        return project_path

    def load_project(self, path: str) -> Dict:
        """
        加载项目
        :param path: 项目路径
        :return: 项目配置
        """
        if self.logger:
            self.logger.info("project_manager", f"开始加载项目: {path}")

        config_path = os.path.join(path, "project.json")
        if not os.path.exists(config_path):
            if self.logger:
                self.logger.error(
                    "project_manager", f"项目配置文件不存在: {config_path}"
                )
            raise FileNotFoundError(f"项目配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.current_project = json.load(f)
            self.current_project["path"] = path

        if self.logger:
            self.logger.info("project_manager", "项目配置读取成功")

        # 初始化Token管理器
        if TOKENS_MANAGER_AVAILABLE:
            self.tokens_manager = TokensManager(path)

            # 设置全局Token管理器
            try:
                from core.llm import set_global_tokens_manager

                set_global_tokens_manager(path)
            except Exception:
                pass

        if self.logger:
            self.logger.info(
                "project_manager", f"项目加载完成: {self.current_project.get('name')}"
            )

        return self.current_project

    def save_project_config(self, path: str = None, config: Dict = None):
        """
        保存项目配置
        :param path: 项目路径（如果为None则使用current_project的路径）
        :param config: 配置字典（如果为None则使用current_project）
        """
        if self.logger:
            self.logger.debug("project_manager", "开始保存项目配置")

        if config is None:
            config = self.current_project

        if path is None:
            if config and "path" in config:
                path = config["path"]
            else:
                if self.logger:
                    self.logger.error("project_manager", "未指定保存路径")
                raise ValueError("未指定保存路径")

        # 移除临时字段（如 path）再保存
        save_config = config.copy()
        if "path" in save_config:
            del save_config["path"]

        save_config["updated_at"] = __import__("datetime").datetime.now().isoformat()

        with open(os.path.join(path, "project.json"), "w", encoding="utf-8") as f:
            json.dump(save_config, f, indent=4, ensure_ascii=False)

        if self.logger:
            self.logger.debug("project_manager", f"项目配置保存成功: {path}")

    def update_current_project(self, key: str, value):
        """
        更新当前项目的配置
        """
        if self.current_project:
            self.current_project[key] = value
            self.save_project_config()
