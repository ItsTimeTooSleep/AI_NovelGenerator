# 安装指南

本文档详细说明如何安装和配置 AI_NovelGenerator 的运行环境。

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 10 / macOS 10.15 / Linux | Windows 11 / macOS 12+ / Ubuntu 20.04+ |
| **Python** | 3.9 | 3.10 - 3.12 |
| **内存** | 8GB | 16GB+ |
| **磁盘空间** | 2GB | 10GB+ |

## 安装步骤

### 1. 获取源代码

使用 Git 克隆项目：

```bash
git clone https://github.com/YILING0013/AI_NovelGenerator.git
cd AI_NovelGenerator
```

或直接从 GitHub 下载 ZIP 包并解压。

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python.exe -m venv venv
venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

如个别依赖安装失败，可尝试手动安装：

```bash
pip install package_name
```

### 4. 配置文件

复制示例配置文件：

```bash
copy config.example.json config.json
```

或直接运行程序，系统会自动创建默认配置。

### 5. 验证安装

运行以下命令验证安装：

```bash
python.exe main.py --help
```

如果看到帮助信息，说明安装成功！

## 可选组件

### C++ 构建工具

部分依赖可能需要编译，如遇到问题请安装：

**Windows:**
- 下载 [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
- 安装时勾选「C++ 桌面开发」

**macOS:**
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install build-essential
```

### 本地模型（Ollama）

如需使用本地模型，安装 Ollama：

```bash
# Windows/macOS: 从 https://ollama.ai 下载安装
# Linux:
curl -fsSL https://ollama.ai/install.sh | sh
```

下载常用模型：

```bash
ollama pull llama2
ollama pull nomic-embed-text
```

> 更多本地模型使用说明请参考 [配置项详解](../reference/config.md)

## 常见安装问题

### Q: pip 安装速度太慢？

A: 使用国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: PyQt5 安装失败？

A: 尝试：

```bash
pip install PyQt5==5.15.9
```

### Q: 缺少某些系统依赖？

A: 具体错误请参考 [常见问题](../reference/faq.md) 或提交 Issue。

## 下一步

- ✅ 完成安装后，请阅读 [快速上手](quick-start.md)
- 📖 或直接开始您的 [第一个项目](first-project.md)

---

**返回 [文档导航](../SUMMARY.md)**
