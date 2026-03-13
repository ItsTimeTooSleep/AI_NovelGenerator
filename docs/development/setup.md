# 开发环境配置

本指南帮助开发者搭建 AI_NovelGenerator 的开发环境。

## 前置要求

- Python 3.9+ (推荐 3.10-3.12)
- Git
- 代码编辑器（推荐 VS Code 或 PyCharm）

## 步骤 1: 克隆代码库

```bash
git clone https://github.com/YILING0013/AI_NovelGenerator.git
cd AI_NovelGenerator
```

## 步骤 2: 创建虚拟环境

### Windows
```bash
python.exe -m venv venv
venv\Scripts\Activate.ps1
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

## 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

安装开发依赖（可选但推荐）：
```bash
pip install black flake8 isort pytest
```

## 步骤 4: 安装预提交钩子（可选）

项目使用 pre-commit 进行代码质量检查：

```bash
pip install pre-commit
pre-commit install
```

## 步骤 5: 配置开发环境

复制示例配置文件：
```bash
copy config.example.json config.json
```

编辑 `config.json`，填入您的开发用 API Key。

## 步骤 6: 验证安装

运行应用验证环境：
```bash
python.exe main.py
```

运行代码检查：
```bash
flake8 .
black --check .
isort --check .
```

## 推荐的 VS Code 扩展

- Python
- Pylance
- Black Formatter
- Flake8
- GitLens
- markdownlint

## 项目结构说明

```
AI_NovelGenerator/
├── core/                    # 核心模块
│   ├── config_manager.py    # 配置管理
│   ├── llm_adapters.py      # LLM 适配器
│   └── ...
├── novel_generator/         # 小说生成逻辑
│   ├── architecture.py      # 架构生成
│   ├── chapter.py           # 章节生成
│   └── ...
├── ui_qt/                   # Qt UI
│   ├── main_window.py       # 主窗口
│   ├── tabs/                # 标签页
│   └── ...
├── docs/                    # 文档（本目录）
└── tests/                   # 测试（待添加）
```

## 常见开发问题

### Q: 如何添加新的 LLM 提供商？

**A:** 在 `core/llm_adapters.py` 中添加新的适配器类，继承基础适配器并实现必要方法。

### Q: 如何调试 UI？

**A:** 使用 PyQt5 的调试工具，或在代码中添加 `print()` 语句输出调试信息。

### Q: 代码格式化有什么要求？

**A:** 项目使用：
- `black` 进行代码格式化
- `isort` 进行导入排序
- `flake8` 进行代码检查

## 打包发布

项目提供两种打包方式：PyInstaller 和 Nuitka。

### 方式一：PyInstaller 打包

PyInstaller 是传统的打包方式，打包速度快，兼容性好。

```bash
python.exe build_qt.py
```

打包完成后，可执行文件位于 `dist/AI小说生成器/` 目录下。

### 方式二：Nuitka 打包（推荐）

Nuitka 将 Python 代码编译为 C/C++ 后再编译为机器码，具有更好的运行性能和更小的打包体积。

**安装依赖：**
```bash
pip install nuitka ordered-set zstandard
```

**打包命令：**

standalone 模式（推荐，启动快）：
```bash
python.exe build_nuitka.py
```

单文件模式（便于分发，启动较慢）：
```bash
python.exe build_nuitka.py --onefile
```

打包完成后：
- standalone 模式：可执行文件位于 `dist/AI小说生成器.dist/` 目录
- 单文件模式：可执行文件位于 `dist/AI小说生成器.exe`

### Nuitka 与 PyInstaller 对比

| 特性 | PyInstaller | Nuitka |
|------|-------------|--------|
| 打包速度 | 快 | 慢 |
| 运行性能 | 一般 | 更好 |
| 打包体积 | 较大 | 较小 |
| 代码保护 | 低 | 高（编译为机器码） |
| 启动速度 | 一般 | standalone快，onefile慢 |

### 版本信息配置

版本信息在 `core/version.py` 中配置：

| 变量 | 说明 |
|------|------|
| `__version__` | 版本号 |
| `PRODUCT_NAME_CN` | 产品中文名称（exe名称） |
| `PRODUCT_NAME_EN` | 产品英文名称 |
| `LEGAL_COPYRIGHT` | 版权声明 |
| `AUTHOR` | 作者信息 |
| `GITHUB_REPO_URL` | 项目主页 |

### 打包后的 exe 属性

打包后的 exe 文件将包含以下属性：
- 文件说明：产品中文名称
- 产品名称：产品中文名称
- 文件版本/产品版本：当前版本号
- 公司名称：作者信息
- 版权信息：版权声明
- 许可证：AGPL-3.0
- 备注：项目主页链接

---

**返回 [文档导航](../SUMMARY.md)**
