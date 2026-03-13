# 核心模块

## 概述

本文档详细介绍 `core/` 目录下的核心模块，这些模块提供了系统的基础功能支持。

## 模块列表

### config_manager.py
配置管理模块，负责：
- 加载和保存配置文件
- 管理LLM配置、Embedding配置等
- 提供配置验证功能

### llm/ 目录
LLM适配器模块，提供统一的LLM调用接口。采用模块化设计，便于扩展和维护：

#### 目录结构
```
core/llm/
├── __init__.py          # 统一导出接口
├── base.py              # 基类和数据结构
├── utils.py             # 工具函数
├── factory.py           # 工厂函数
└── adapters/            # 适配器目录
    ├── __init__.py
    ├── deepseek.py      # DeepSeek适配器
    ├── openai.py        # OpenAI适配器
    ├── gemini.py        # Gemini适配器
    ├── azure_openai.py  # Azure OpenAI适配器
    ├── azure_ai.py      # Azure AI适配器
    ├── ollama.py        # Ollama适配器
    ├── ml_studio.py     # ML Studio适配器
    ├── volcano_engine.py# 火山引擎适配器
    ├── silicon_flow.py  # 硅基流动适配器
    └── grok.py          # Grok适配器
```

#### 支持的模型服务商
- OpenAI（及兼容接口）
- DeepSeek
- Azure OpenAI
- Azure AI Inference
- Ollama（本地模型）
- ML Studio
- Google Gemini
- 火山引擎
- 硅基流动
- xAI Grok

#### 核心类
- `StreamChunk`: 流式响应数据块（包含cached_tokens缓存命中字段）
- `UsageInfo`: Token使用信息数据结构
- `UsageExtractor`: Token使用信息提取器，统一处理不同API提供商的usage信息
- `BaseLLMAdapter`: LLM适配器基类
- 各服务商适配器类

#### 使用方法
```python
# 导入方式（推荐）
from core.llm import create_llm_adapter, BaseLLMAdapter, StreamChunk

# 创建适配器
adapter = create_llm_adapter(
    interface_format="openai",
    base_url="https://api.openai.com/v1",
    model_name="gpt-4",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=4000,
    timeout=600
)

# 非流式调用
response = adapter.invoke(prompt)

# 流式调用
for chunk in adapter.invoke_stream(prompt):
    if chunk.content:
        print(chunk.content, end="")
    if chunk.is_done:
        print(f"\n完成! Tokens: {chunk.input_tokens}/{chunk.output_tokens}")
        if chunk.cached_tokens:
            print(f"缓存命中: {chunk.cached_tokens}")
```

### llm_invoker.py
LLM调用辅助模块，提供统一的调用接口：

```python
from core.llm_invoker import invoke_llm

# 根据设置自动选择流式或非流式
response = invoke_llm(
    llm_adapter=adapter,
    prompt=prompt,
    streaming_enabled=True,
    on_chunk=lambda chunk: print(chunk, end="")
)
```

### embedding_adapters.py
Embedding适配器模块，用于文本向量化：
- 支持OpenAI、Azure OpenAI、Ollama等Embedding接口
- 用于知识库向量检索

### tokens_manager.py
Token使用管理模块：
- 记录每次API调用的Token消耗
- 记录缓存命中Token数量（DeepSeek等支持缓存的模型）
- 生成Token使用报告
- 支持成本分析
- 按章节、步骤、模型等维度统计分析

#### Token数据来源优先级
Token统计的数据来源按以下优先级获取：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | API返回信息 | 最准确，直接使用API响应中的usage字段 |
| 2 | 本地tiktoken估算 | 使用tiktoken库精确计算（需安装tiktoken） |
| 3 | 近似估算 | 字符数÷3的简单估算（无tiktoken时） |

#### 本地Token估算配置
用户可在设置中控制是否启用本地Token估算：

```json
{
    "local_token_estimation": true
}
```

- **启用时**：API未返回Token信息时使用本地算法估算，显示为 `数字(估算)`
- **禁用时**：API未返回Token信息时显示为 `未知`

#### TokenUsageRecord 数据结构
每条Token记录包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| step_name | str | 步骤名称 |
| model_name | str | 模型名称 |
| input_tokens | int | 输入Token数量（-1表示未知） |
| output_tokens | int | 输出Token数量（-1表示未知） |
| cached_tokens | int | 缓存命中Token数量 |
| input_estimated | bool | 输入Token是否为估算值 |
| output_estimated | bool | 输出Token是否为估算值 |

### consistency_checker.py
一致性检查模块：
- 检查章节内容与设定的 consistency
- 识别潜在矛盾和问题

### ui_prompts.py
UI提示文本模块：
- 集中管理界面提示信息文本
- 支持HTML格式的富文本提示
- 提供变量替换功能

#### 使用方法
```python
from core.ui_prompts import get_prompt, get_prompt_title

# 获取提示内容（支持变量替换）
content = get_prompt(
    "composer_ai_level_description",
    text_tertiary="#80FFFFFF",
    info_color="#3B82F6",
    primary_color="#8B5CF6",
    pro_color="#EC4899"
)

# 获取提示标题
title = get_prompt_title("composer_ai_level_description")
```

### tooltips.py
工具提示文本模块：
- 定义界面控件的工具提示文本
- 支持多行文本格式

## 流式传输功能

### 概述
系统支持真正的API流式传输，可在设置中开启或关闭。

### 配置项
```json
{
    "streaming_enabled": true
}
```

### 工作原理
1. **API层流式**: 所有LLM适配器都实现了 `invoke_stream()` 方法
2. **UI层实时显示**: `StreamingManager` 处理流式数据的实时显示
3. **自动选择**: 根据 `streaming_enabled` 设置自动选择调用方式

### 支持流式的场景
- 章节草稿生成
- 小说架构生成
- 章节目录生成
- Composer AI功能

---

**相关文档:**
- [系统总览](../overview.md)
- [小说生成器](novel-generator.md)
- [UI 模块](ui-qt.md)

---

**返回 [文档导航](../../SUMMARY.md)**
