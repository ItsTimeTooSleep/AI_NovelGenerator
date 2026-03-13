# 系统总览

本文档介绍 AI_NovelGenerator 的整体架构设计和核心概念。

## 项目定位

AI_NovelGenerator 是一款基于大语言模型（LLM）的多阶段智能小说生成系统，帮助创作者高效完成结构清晰、逻辑严谨、设定统一的中长篇小说创作。

## 核心设计理念

1. **模块化架构**: 各功能模块独立，便于维护和扩展
2. **多阶段生成**: 将小说创作分解为多个可控步骤
3. **状态追踪**: 自动追踪角色状态、剧情进展和伏笔
4. **向量增强**: 使用向量数据库实现长程上下文记忆
5. **一致性保障**: 自动检测和修正设定矛盾

## 系统分层架构

```
┌─────────────────────────────────────────┐
│           UI 层 (ui_qt/)                │
│  - main_window                          │
│  - 各标签页 (home, project, etc.)      │
│  - 组件与对话框                         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        业务逻辑层                        │
│  - config_manager.py                    │
│  - project_manager.py                   │
│  - consistency_checker.py               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      核心生成层 (novel_generator/)      │
│  - architecture.py (架构生成)           │
│  - blueprint.py (目录生成)              │
│  - chapter.py (章节生成)                │
│  - finalization.py (定稿处理)           │
│  - vectorstore_utils.py (向量库)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        适配器层 (core/)                  │
│  - llm_adapters.py                      │
│  - embedding_adapters.py                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        数据存储层                        │
│  - config.json                          │
│  - novels/ (项目文件)                   │
│  - vectorstore/ (向量数据库)            │
└─────────────────────────────────────────┘
```

## 核心模块说明

### UI 层
负责用户交互和界面展示，基于 PyQt5 + qfluentwidgets 构建。

**主要组件:**
- `main_window.py`: 主窗口和标签页管理
- `home_tab.py`: 首页（生成台）
- `project_tab.py`: 项目设定
- `writing_tab.py`: 写作编辑
- `settings_tab.py`: 系统设置

> 详细说明请参考 [UI 模块](modules/ui-qt.md)

### 业务逻辑层
处理配置、项目管理和一致性检查等核心业务逻辑。

**主要模块:**
- `config_manager.py`: 配置文件的加载、保存和验证
- `project_manager.py`: 项目的创建、加载和列表管理
- `consistency_checker.py`: 人物设定、剧情逻辑和时间线检查

> 详细说明请参考 [核心模块](modules/core.md)

### 核心生成层
小说生成的核心逻辑，包含架构、目录、章节生成等。

**主要模块:**
- `architecture.py`: 生成小说世界观、角色设定和主线剧情
- `blueprint.py`: 生成章节目录和节奏规划
- `chapter.py`: 生成章节草稿
- `finalization.py`: 定稿处理，更新状态和知识库
- `vectorstore_utils.py`: 向量数据库操作

> 详细说明请参考 [小说生成器](modules/novel-generator.md)

### 适配器层
封装 LLM 和 Embedding 接口，支持多种后端。

**主要模块:**
- `llm_adapters.py`: 统一的 LLM 调用接口
- `embedding_adapters.py`: 统一的 Embedding 调用接口

支持的后端:
- OpenAI 兼容接口
- 本地 Ollama
- 其他兼容 API

### 数据存储层
管理所有数据持久化。

**主要文件:**
- `config.json`: 系统配置
- `novels/{project_name}/`: 项目文件
  - `project.json`: 项目元数据
  - `Novel_architecture.txt`: 小说架构
  - `Novel_directory.txt`: 章节目录
  - `character_state.txt`: 角色状态
  - `global_summary.txt`: 全局摘要
  - `chapters/`: 章节文件
- `vectorstore/`: Chroma 向量数据库

## 核心工作流

完整的小说创作工作流包含以下步骤：

1. **项目创建**: 在图书馆新建项目，填写基本信息
2. **架构生成**: 生成世界观、角色设定和主线剧情
3. **目录生成**: 生成章节目录和节奏规划
4. **章节生成**: 逐章生成草稿
5. **定稿更新**: 每章定稿后更新状态和知识库
6. **一致性检查** (可选): 检测设定矛盾

> 详细工作流请参考 [用户手册 - 工作流指南](../user-guide/workflow/)

## 关键技术栈

| 类别 | 技术选型 |
|------|---------|
| **GUI 框架** | PyQt5 + qfluentwidgets |
| **LLM 集成** | OpenAI API 兼容接口 |
| **向量数据库** | Chroma DB |
| **Embedding** | OpenAI / Ollama 兼容 |
| **语言** | Python 3.9+ |

## 相关文档

- [数据流向](data-flow.md) - 完整数据流和交互关系图
- [模块文档](modules/) - 各模块详细说明
- [配置项详解](../reference/config.md) - 所有配置项说明

---

**返回 [文档导航](../SUMMARY.md)**
