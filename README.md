# AI Novel Generator - AI小说生成器

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**基于大语言模型的多阶段智能小说生成系统**

[快速开始](#-快速开始) · [功能特性](#-功能特性) · [安装指南](#-安装指南) · [使用文档](docs/README.md)

</div>

---

## 项目简介

本工具是一款基于大语言模型（LLM）的**多阶段智能小说生成系统**，支持设定构建、章节生成、上下文追踪、一致性校验与向量检索增强，帮助创作者高效完成结构清晰、逻辑严谨、设定统一的中长篇小说创作。

> 本项目基于 **[YILING0013/AI_NovelGenerator](https://github.com/YILING0013/AI_NovelGenerator)** 进行深度二次开发与系统级重构。

---

## ✨ 功能特性

### 🎨 现代化界面

- 基于 **PyQt5 + qfluentwidgets** 构建的 Fluent Design 风格界面
- 支持亮色/暗色/自动主题切换
- 高DPI支持，适配高分辨率显示器
- 流畅的启动画面与动画效果

### 🤖 多模型支持

支持多种主流AI模型服务商：

| 服务商 | 模型示例 | 特点 |
|--------|----------|------|
| OpenAI | GPT-4o, GPT-4-turbo | 官方API，稳定可靠 |
| DeepSeek | DeepSeek-V3 | 国产大模型，性价比高 |
| Google Gemini | Gemini 2.5 Pro | 多模态能力 |
| Azure OpenAI | GPT系列 | 企业级部署 |
| Azure AI | 各类模型 | 灵活部署 |
| Ollama | 本地模型 | 完全离线运行 |
| 火山引擎 | 字节云模型 | 国内访问快 |
| 硅基流动 | SiliconFlow | 多模型聚合 |
| Grok | xAI Grok | xAI出品 |

### 📖 四阶段生成流程

```
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
```

### 🧠 智能辅助功能

- **向量语义检索**：长程上下文一致性维护
- **本地知识库**：支持外部文档参考
- **自动一致性审校**：检测逻辑冲突与设定矛盾
- **角色状态追踪**：角色成长记录与伏笔管理
- **Token消耗统计**：章节与整本小说成本分析

### ✏️ 编辑器增强

- 支持 `Ctrl+Z` 撤销 / `Ctrl+Y` 重做
- 全文搜索与替换功能
- AI写作助手（语法修正、润色、扩写）
- 差异对比预览

### 📚 图书馆管理

- 项目统一管理
- 多项目切换
- 项目状态追踪
- WebDAV云同步支持

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+（推荐 3.10-3.12）
- **操作系统**: Windows
- **API Key**: 至少一种有效API密钥

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/Doctor-Shadow/AI_NovelGenerator.git
cd AI_NovelGenerator
```

2. **创建虚拟环境（推荐）**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置API**

复制配置模板并填写API密钥：

```bash
copy config.example.json config.json
```

编辑 `config.json`，填入你的API Key。

5. **启动程序**

```bash
python.exe main.py
```

---

## 📁 项目架构

```
AI_NovelGenerator/
├── main.py                      # 程序入口
├── config.json                  # 用户配置文件
├── config.example.json          # 配置模板
├── requirements.txt             # 依赖列表
│
├── core/                        # 核心模块
│   ├── llm/                     # LLM适配器
│   │   ├── adapters/            # 各服务商适配器实现
│   │   ├── base.py              # 适配器基类
│   │   ├── factory.py           # 适配器工厂
│   │   └── utils.py             # 工具函数
│   ├── config_manager.py        # 配置管理
│   ├── consistency_checker.py   # 一致性检查
│   ├── embedding_adapters.py    # Embedding接口
│   ├── log_manager.py           # 日志管理
│   ├── tokens_manager.py        # Token统计
│   └── version.py               # 版本信息
│
├── novel_generator/             # 小说生成核心
│   ├── architecture.py          # 架构生成
│   ├── blueprint.py             # 章节蓝图
│   ├── chapter.py               # 章节生成
│   ├── finalization.py          # 章节定稿
│   ├── knowledge.py             # 知识库导入
│   ├── vectorstore_utils.py     # 向量存储
│   ├── composer.py              # AI写作助手
│   └── project_manager.py       # 项目管理
│
├── ui_qt/                       # Qt图形界面
│   ├── main_window.py           # 主窗口
│   ├── tabs/                    # 功能标签页
│   │   ├── home_tab.py          # 首页/生成台
│   │   ├── library_tab.py       # 图书馆
│   │   ├── project_tab.py       # 项目设定
│   │   ├── settings_tab.py      # 设置
│   │   ├── architecture_tab.py  # 架构编辑
│   │   ├── directory_tab.py     # 目录编辑
│   │   ├── character_tab.py     # 角色管理
│   │   ├── summary_tab.py       # 摘要管理
│   │   └── writing_tab.py       # 写作编辑
│   ├── widgets/                 # UI组件
│   ├── utils/                   # UI工具
│   ├── home/                    # 首页模块
│   └── settings/                # 设置模块
│
├── novels/                      # 小说项目存储
│   └── {project_name}/
│       ├── project.json         # 项目配置
│       ├── project_status.json  # 项目状态
│       ├── Novel_architecture.txt
│       ├── Novel_directory.txt
│       ├── chapters/            # 章节文件
│       └── ...
│
└── docs/                        # 文档目录
    ├── getting-started/         # 入门指南
    ├── user-guide/              # 用户手册
    ├── architecture/            # 架构文档
    └── development/             # 开发文档
```

---

## ⚙️ 配置说明

### 配置文件结构

```json
{
    "llm_configs": {
        "配置名称": {
            "api_key": "your-api-key",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 8192,
            "timeout": 600,
            "interface_format": "OpenAI"
        }
    },
    "embedding_configs": {
        "配置名称": {
            "api_key": "your-api-key",
            "base_url": "https://api.openai.com/v1",
            "model_name": "text-embedding-ada-002",
            "retrieval_k": 4,
            "interface_format": "OpenAI"
        }
    },
    "choose_configs": {
        "prompt_draft_llm": "DeepSeek V3",
        "chapter_outline_llm": "DeepSeek V3",
        "architecture_llm": "Gemini 2.5 Pro",
        "final_chapter_llm": "GPT 5",
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

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `llm_configs` | LLM模型配置，可配置多个模型 |
| `embedding_configs` | Embedding模型配置 |
| `choose_configs` | 各阶段使用的模型选择 |
| `proxy_setting` | 代理设置 |
| `webdav_config` | WebDAV云同步配置 |

---

## 📦 打包发布

使用 PyInstaller 打包为可执行文件：

```bash
pip install pyinstaller
pyinstaller main.spec
```

生成的可执行文件位于 `dist/` 目录。

---

## 📖 使用文档

详细使用文档请参阅 [docs/README.md](docs/README.md)

- [快速上手](docs/getting-started/quick-start.md)
- [安装指南](docs/getting-started/installation.md)
- [第一个项目](docs/getting-started/first-project.md)
- [配置详解](docs/reference/config.md)
- [常见问题](docs/reference/faq.md)

---

## 🔧 开发指南

### 开发环境配置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行程序
python.exe main.py
```

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 函数级文档注释（包含参数、返回值、异常说明）

详见 [代码规范](docs/development/coding-standards.md)

---

## ❓ 常见问题

### Q1: `Expecting value: line 1 column 1 (char 0)`

API返回异常，请检查：
- API Key 是否正确
- Base URL 是否填写正确
- 网络是否稳定

### Q2: `HTTP 504 Gateway Timeout`

可能原因：
- 模型响应过慢
- 服务器不稳定
- 请求Token过大

建议减少 `max_tokens` 或检查网络。

### Q3: 如何使用本地模型？

1. 安装并启动 Ollama
2. 拉取模型：`ollama pull llama3`
3. 在配置中添加：
```json
{
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model_name": "llama3",
    "interface_format": "Ollama"
}
```

### Q4: 如何切换Embedding模型？

在GUI设置中修改Embedding配置即可。切换后建议清空 `vectorstore/` 目录。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

详见 [贡献指南](docs/development/contributing.md)

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- 原项目 [YILING0013/AI_NovelGenerator](https://github.com/YILING0013/AI_NovelGenerator)
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [qfluentwidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！**

</div>
