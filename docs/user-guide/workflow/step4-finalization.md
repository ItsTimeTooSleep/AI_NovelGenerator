# 第四步：定稿与状态更新

## 概述

第四步是小说生成流程的最后一步，负责对章节草稿进行最终处理。定稿操作会更新全局摘要、更新角色状态，并将章节内容存入向量库，为后续章节的生成提供上下文支持。

## 定稿流程

### 子步骤详解

定稿过程包含以下子步骤，按顺序执行：

1. **读取章节草稿** - 从 `chapters/chapter_N.txt` 读取章节内容
2. **备份原文件** - 备份 `global_summary.txt` 和 `character_state.txt`
3. **更新全局摘要** - 基于当前章节内容更新全局摘要
4. **更新角色状态** - 基于当前章节内容更新角色状态
5. **向量入库** - 将章节内容向量化存入知识库（可选）
6. **清理备份** - 定稿成功后删除备份文件

### 事务性保存机制

定稿操作采用**事务性保存机制**，确保操作的原子性：

```
┌─────────────────────────────────────────────────────────────┐
│                    定稿流程（事务性）                         │
├─────────────────────────────────────────────────────────────┤
│  1. 备份原文件                                               │
│     ├── global_summary.txt → .backup_temp/global_summary.txt.bak │
│     └── character_state.txt → .backup_temp/character_state.txt.bak │
│                                                              │
│  2. 执行更新操作                                              │
│     ├── 更新全局摘要                                          │
│     ├── 更新角色状态                                          │
│     └── 向量入库（可选）                                       │
│                                                              │
│  3. 结果处理                                                  │
│     ├── 成功 → 清理备份文件                                   │
│     └── 失败 → 恢复备份文件                                   │
└─────────────────────────────────────────────────────────────┘
```

### 失败恢复策略

当定稿过程中任何步骤失败时，系统会：

1. **自动恢复备份** - 将 `global_summary.txt` 和 `character_state.txt` 恢复到定稿前的状态
2. **清理临时文件** - 删除 `.backup_temp` 目录
3. **抛出异常** - 通知调用方定稿失败

这样可以确保重试时不会在已修改的基础上再次修改，保持数据一致性。

## 使用方式

### 前置条件

- 已完成第三步，章节草稿已生成
- 已配置 LLM 模型和 API Key
- （可选）已配置 Embedding 模型用于向量入库

### 操作步骤

1. 在主页选择当前章节编号
2. 点击「Step 4. 定稿章节」按钮
3. 等待定稿完成
4. 系统自动切换到下一章节

### 错误处理

如果定稿失败：

1. 查看日志面板了解失败原因
2. 检查网络连接和 API 配置
3. 修正问题后重新点击定稿按钮
4. 系统会从备份恢复，不会影响原文件

## 配置选项

定稿操作使用以下配置：

| 配置项 | 说明 |
|--------|------|
| `final_chapter_llm` | 用于更新摘要和角色状态的 LLM 模型 |
| `embedding_model` | 用于向量入库的 Embedding 模型（可选） |

## 相关文件

| 文件 | 说明 |
|------|------|
| `chapters/chapter_N.txt` | 章节草稿文件 |
| `global_summary.txt` | 全局摘要文件 |
| `character_state.txt` | 角色状态文件 |
| `.backup_temp/` | 临时备份目录（定稿过程中创建） |

## 技术实现

### 核心类

- `FinalizationError` - 定稿错误异常类，包含失败步骤信息
- `BackupManager` - 文件备份管理器，负责备份和恢复操作

### 核心函数

```python
def finalize_chapter(
    novel_number: int,      # 章节编号
    word_number: int,       # 目标字数
    api_key: str,           # LLM API密钥
    base_url: str,          # LLM API基础URL
    model_name: str,        # LLM模型名称
    temperature: float,     # 生成温度
    filepath: str,          # 项目路径
    embedding_api_key: str, # Embedding API密钥
    embedding_url: str,     # Embedding API URL
    embedding_interface_format: str,  # Embedding接口格式
    embedding_model_name: str,        # Embedding模型名称
    interface_format: str,  # LLM接口格式
    max_tokens: int,        # 最大Token数
    timeout: int = 600,     # 超时时间
) -> None:
    """
    定稿章节，采用事务性保存机制。
    
    异常:
        FinalizationError: 定稿过程中发生错误
    """
```

---

**相关文档:**
- [第一步：生成小说架构](step1-architecture.md)
- [第二步：生成章节目录](step2-directory.md)
- [第三步：生成章节草稿](step3-generation.md)
- [向量库管理](../features/vector-store.md)

---

**返回 [文档导航](../../SUMMARY.md)**
