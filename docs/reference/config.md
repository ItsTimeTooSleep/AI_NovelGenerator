# 配置项详解

本文档详细说明 config.json 中所有配置项的含义和用法。

## 配置文件位置

配置文件位于项目根目录：
```
config.json
```

## 配置文件结构

```json
{
  "llm_configs": {...},
  "embedding_configs": {...},
  "choose_configs": {...},
  "other_params": {...},
  "proxy_setting": {...},
  "webdav_config": {...}
}
```

---

## llm_configs - LLM 配置

存储多个 LLM 配置，支持随时切换。

### 配置结构

```json
{
  "配置名称": {
    "api_key": "sk-xxxxx",
    "base_url": "https://api.example.com/v1",
    "interface_format": "OpenAI",
    "model_name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 600
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_key` | string | ✅ | API 密钥 |
| `base_url` | string | ✅ | API 基础地址 |
| `interface_format` | string | ✅ | 接口格式，支持 "OpenAI"、"Ollama"、"Gemini"、"Azure" 等 |
| `model_name` | string | ✅ | 模型名称 |
| `temperature` | number | ❌ | 温度参数，范围 0-1，默认 0.7<br/>- 较低值：更确定、更保守<br/>- 较高值：更有创意、更多样 |
| `max_tokens` | number | ❌ | 单次最大生成 Token 数，默认 4096 |
| `timeout` | number | ❌ | 请求超时时间（秒），默认 600 |

### 常用模型配置示例

#### DeepSeek
```json
{
  "DeepSeek V3": {
    "api_key": "sk-xxxxx",
    "base_url": "https://api.deepseek.com/v1",
    "interface_format": "OpenAI",
    "model_name": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 8192,
    "timeout": 600
  }
}
```

#### OpenAI
```json
{
  "OpenAI GPT-4o": {
    "api_key": "sk-xxxxx",
    "base_url": "https://api.openai.com/v1",
    "interface_format": "OpenAI",
    "model_name": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 600
  }
}
```

#### Google Gemini
```json
{
  "Gemini 2.5 Pro": {
    "api_key": "your-gemini-api-key",
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    "interface_format": "OpenAI",
    "model_name": "gemini-2.5-pro",
    "temperature": 0.7,
    "max_tokens": 32768,
    "timeout": 600
  }
}
```

#### 本地 Ollama
```json
{
  "Ollama Llama3": {
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "interface_format": "Ollama",
    "model_name": "llama3",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 600
  }
}
```

---

## embedding_configs - Embedding 配置

存储多个 Embedding 配置。

### 配置结构

```json
{
  "配置名称": {
    "api_key": "sk-xxxxx",
    "base_url": "https://api.example.com/v1",
    "interface_format": "OpenAI",
    "model_name": "text-embedding-ada-002",
    "retrieval_k": 4
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_key` | string | ✅ | API 密钥 |
| `base_url` | string | ✅ | API 基础地址（注意：不要包含 `/embeddings` 后缀，程序会自动添加） |
| `interface_format` | string | ✅ | 接口格式 |
| `model_name` | string | ✅ | Embedding 模型名称 |
| `retrieval_k` | number | ❌ | 向量检索返回的相关上下文数量，默认 4 |

> ⚠️ **重要提示**：`base_url` 应该只包含到 `/v1` 为止，不要添加 `/embeddings` 后缀。例如：
> - ✅ 正确：`https://api.openai.com/v1`
> - ❌ 错误：`https://api.openai.com/v1/embeddings`

### 常用配置示例

#### OpenAI Embedding
```json
{
  "OpenAI Ada-002": {
    "api_key": "sk-xxxxx",
    "base_url": "https://api.openai.com/v1",
    "interface_format": "OpenAI",
    "model_name": "text-embedding-ada-002",
    "retrieval_k": 4
  }
}
```

#### 本地 Ollama Embedding
```json
{
  "Ollama Nomic": {
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "interface_format": "OpenAI",
    "model_name": "nomic-embed-text",
    "retrieval_k": 4
  }
}
```

---

## choose_configs - 各阶段模型选择

指定各生成阶段使用的 LLM 配置。

### 配置结构

```json
{
  "prompt_draft_llm": "配置名称",
  "chapter_outline_llm": "配置名称",
  "architecture_llm": "配置名称",
  "final_chapter_llm": "配置名称",
  "consistency_review_llm": "配置名称"
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `prompt_draft_llm` | 生成提示草稿使用的 LLM |
| `chapter_outline_llm` | 生成章节大纲使用的 LLM |
| `architecture_llm` | 生成小说架构使用的 LLM |
| `final_chapter_llm` | 生成最终章节使用的 LLM |
| `consistency_review_llm` | 一致性审校使用的 LLM |

### 示例

```json
{
  "choose_configs": {
    "prompt_draft_llm": "DeepSeek V3",
    "chapter_outline_llm": "DeepSeek V3",
    "architecture_llm": "Gemini 2.5 Pro",
    "final_chapter_llm": "GPT 5",
    "consistency_review_llm": "DeepSeek V3"
  }
}
```

---

## other_params - 其他参数

### 配置结构

```json
{
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
  "time_constraint": ""
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `topic` | string | 小说主题 |
| `genre` | string | 小说类型 |
| `num_chapters` | number | 总章节数 |
| `word_number` | number | 单章目标字数 |
| `filepath` | string | 输出路径 |
| `chapter_num` | string | 章节编号 |
| `user_guidance` | string | 用户指导说明 |
| `characters_involved` | string | 涉及角色 |
| `key_items` | string | 关键物品 |
| `scene_location` | string | 场景位置 |
| `time_constraint` | string | 时间约束 |

### 系统参数

```json
{
  "embedding_retrieval_k": 4,
  "theme": "Auto",
  "streaming_enabled": true,
  "novels_directory": "D:\\path\\to\\novels",
  "enable_wheel_tab_switch": false,
  "developer_mode": false,
  "local_token_estimation": true
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding_retrieval_k` | number | 4 | 向量检索返回的相关上下文数量 |
| `theme` | string | "Auto" | UI 主题，可选值："Auto"、"Light"、"Dark" |
| `streaming_enabled` | boolean | true | 是否启用流式传输模式 |
| `novels_directory` | string | - | 小说项目存储目录 |
| `enable_wheel_tab_switch` | boolean | false | 是否启用滚轮切换标签页 |
| `developer_mode` | boolean | false | 是否启用开发者模式 |
| `local_token_estimation` | boolean | true | 是否启用本地Token估算 |

---

## proxy_setting - 代理设置

### 配置结构

```json
{
  "proxy_setting": {
    "proxy_url": "127.0.0.1",
    "proxy_port": "7890",
    "enabled": false
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `proxy_url` | string | 代理服务器地址 |
| `proxy_port` | string | 代理端口 |
| `enabled` | boolean | 是否启用代理 |

---

## webdav_config - WebDAV 云同步配置

### 配置结构

```json
{
  "webdav_config": {
    "webdav_url": "",
    "webdav_username": "",
    "webdav_password": ""
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `webdav_url` | string | WebDAV 服务地址 |
| `webdav_username` | string | WebDAV 用户名 |
| `webdav_password` | string | WebDAV 密码 |

---

## composer_settings - Composer AI 相关配置

### 配置结构

```json
{
  "composer_settings": {
    "diff_preview_mode": "dialog",
    "ai_level": "standard"
  }
}
```

### 字段说明

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `diff_preview_mode` | string | "dialog" | 差异预览模式，可选值：<br/>- "dialog": 弹窗模式，在独立窗口中显示差异<br/>- "inline": 行内模式，在编辑器中直接显示差异 |
| `ai_level` | string | "standard" | AI 处理等级，可选值："mini"、"standard"、"pro" |

---

## 完整配置示例

```json
{
  "last_interface_format": "OpenAI",
  "last_embedding_interface_format": "OpenAI",
  "llm_configs": {
    "DeepSeek V3": {
      "api_key": "sk-xxxxx",
      "base_url": "https://api.deepseek.com/v1",
      "model_name": "deepseek-chat",
      "temperature": 0.7,
      "max_tokens": 8192,
      "timeout": 600,
      "interface_format": "OpenAI"
    },
    "GPT 4o": {
      "api_key": "sk-xxxxx",
      "base_url": "https://api.openai.com/v1",
      "model_name": "gpt-4o",
      "temperature": 0.7,
      "max_tokens": 4096,
      "timeout": 600,
      "interface_format": "OpenAI"
    }
  },
  "embedding_configs": {
    "OpenAI": {
      "api_key": "sk-xxxxx",
      "base_url": "https://api.openai.com/v1",
      "model_name": "text-embedding-ada-002",
      "retrieval_k": 4,
      "interface_format": "OpenAI"
    }
  },
  "choose_configs": {
    "prompt_draft_llm": "DeepSeek V3",
    "chapter_outline_llm": "DeepSeek V3",
    "architecture_llm": "GPT 4o",
    "final_chapter_llm": "GPT 4o",
    "consistency_review_llm": "DeepSeek V3"
  },
  "proxy_setting": {
    "proxy_url": "127.0.0.1",
    "proxy_port": "7890",
    "enabled": false
  },
  "webdav_config": {
    "webdav_url": "",
    "webdav_username": "",
    "webdav_password": ""
  }
}
```

---

## 安全提示

⚠️ **重要安全提示：**
1. 切勿将包含真实 API Key 的 config.json 提交到公开仓库
2. 建议使用 config.example.json 作为模板
3. 定期轮换 API Key
4. WebDAV 密码建议使用应用专用密码

---

**返回 [文档导航](../SUMMARY.md)**
