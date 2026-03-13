# 日志系统规范文档

## 概述

本文档定义了AI小说生成器项目的日志系统规范，包括日志格式、日志级别、使用场景和最佳实践。

## 日志格式

### 标准日志格式

所有日志必须遵循以下格式：

```
[YYYY-MM-DD HH:MM:SS.ffffff] [LEVEL] [MODULE] 消息内容
```

#### 格式说明

| 字段 | 说明 | 示例 |
|------|------|------|
| 时间戳 | 精确到微秒的时间 | `2026-03-03 14:30:45.123456` |
| 日志级别 | 日志级别（DEBUG/INFO/WARN/ERROR） | `[INFO]` |
| 模块名 | 发出日志的模块名称 | `[project_manager]` |
| 消息内容 | 详细的日志消息 | `项目创建成功：《神笔马良》` |

#### 示例

```
[2026-03-03 14:30:45.123456] [INFO] [main] 应用程序启动
[2026-03-03 14:30:46.789012] [INFO] [project_manager] 开始创建新项目：《神笔马良》
[2026-03-03 14:30:47.345678] [INFO] [project_manager] 项目创建成功，路径: novels/神笔马良
[2026-03-03 14:31:00.901234] [INFO] [architecture] Step1: 开始生成核心种子
[2026-03-03 14:31:15.567890] [ERROR] [architecture] 核心种子生成失败，返回空内容
```

## 日志级别

### 级别定义

| 级别 | 值 | 用途 | 示例 |
|------|-----|------|------|
| **DEBUG** | 10 | 详细的调试信息，开发阶段使用 | `创建项目目录: novels/神笔马良` |
| **INFO** | 20 | 一般信息，记录正常流程 | `应用程序启动`、`项目创建成功` |
| **WARN** | 30 | 警告信息，记录非严重问题 | `加载 partial_architecture.json 失败` |
| **ERROR** | 40 | 错误信息，记录错误和异常 | `项目已存在`、`核心种子生成失败` |

### 级别使用指南

#### DEBUG 级别
- **使用场景**：
  - 函数进入和退出
  - 变量值的详细记录
  - 中间步骤的执行状态
  - 开发调试信息

- **示例**：
  ```python
  logger.debug("module_name", f"函数参数: {param}")
  logger.debug("module_name", "中间计算结果: 42")
  ```

#### INFO 级别
- **使用场景**：
  - 应用程序启动和关闭
  - 主要业务流程的开始和结束
  - 重要配置的加载
  - 用户操作的关键步骤

- **示例**：
  ```python
  logger.info("module_name", "应用程序启动")
  logger.info("module_name", "开始生成小说架构，书名: 《神笔马良》")
  logger.info("module_name", "项目创建成功")
  ```

#### WARN 级别
- **使用场景**：
  - 非致命错误
  - 可恢复的异常
  - 配置项缺失但有默认值
  - 性能警告

- **示例**：
  ```python
  logger.warn("module_name", "配置项缺失，使用默认值")
  logger.warn("module_name", "加载文件失败，将跳过")
  ```

#### ERROR 级别
- **使用场景**：
  - 致命错误
  - 无法恢复的异常
  - 关键操作失败
  - 数据验证失败

- **示例**：
  ```python
  logger.error("module_name", "项目已存在")
  logger.error("module_name", "LLM调用失败")
  ```

## 使用指南

### 基础使用

#### 1. 导入日志管理器

```python
try:
    from core import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

if LOGGER_AVAILABLE:
    logger = get_logger()
else:
    logger = None
```

#### 2. 初始化日志系统（仅在应用入口）

```python
from core import get_logger, LogLevel

logger = get_logger()
logger.initialize(
    log_file="app.log",
    level=LogLevel.INFO,
    max_records=1000
)
```

#### 3. 记录日志

```python
# INFO 级别
if logger:
    logger.info("module_name", "这是一条信息日志")

# DEBUG 级别
if logger:
    logger.debug("module_name", "这是一条调试日志")

# WARN 级别
if logger:
    logger.warn("module_name", "这是一条警告日志")

# ERROR 级别
if logger:
    logger.error("module_name", "这是一条错误日志")
```

### 模块命名规范

模块名应使用小写，多个单词用下划线分隔：

| 模块 | 模块名 |
|------|--------|
| 主入口 | `main` |
| 项目管理 | `project_manager` |
| 架构生成 | `architecture` |
| 章节生成 | `chapter` |
| LLM适配器 | `llm_adapters` |
| UI日志面板 | `ui_log_panel` |
| 自动保存管理器 | `autosave_manager` |

### 最佳实践

#### 1. 防御性编程

始终检查 logger 是否可用：

```python
if logger:
    logger.info("module", "消息内容")
```

#### 2. 日志消息规范

- **清晰明确**：消息应清晰说明发生了什么
- **包含关键信息**：如文件名、项目名、步骤等
- **避免敏感信息**：不要记录 API 密钥、密码等
- **使用中文**：项目使用中文，日志也应使用中文

```python
# 好的示例
logger.info("project_manager", f"项目创建成功，书名: {name}, 路径: {path}")

# 不好的示例
logger.info("project_manager", "done")
```

#### 3. 关键操作日志

在以下关键操作点必须记录日志：

- 应用程序启动和关闭
- 项目创建、加载、保存
- 架构生成的每个步骤
- 章节生成的开始和完成
- LLM 调用的开始和结果
- 文件读写操作
- 错误和异常

#### 4. 异常处理中的日志

```python
try:
    # 一些操作
    do_something()
except Exception as e:
    if logger:
        logger.error("module_name", f"操作失败: {e}")
    raise  # 重新抛出异常
```

## 核心业务流程日志

### 1. 项目创建流程

```
[时间] [INFO] [project_manager] 开始创建新项目：《书名》
[时间] [DEBUG] [project_manager] 创建项目目录: 路径
[时间] [INFO] [project_manager] 项目创建成功，路径: 路径
```

### 2. 架构生成流程

```
[时间] [INFO] [architecture] 开始生成小说架构，书名: 《书名》
[时间] [DEBUG] [architecture] LLM适配器创建成功，模型: 模型名
[时间] [INFO] [architecture] Step1: 开始生成核心种子
[时间] [INFO] [architecture] 核心种子生成完成
[时间] [INFO] [architecture] Step2: 开始构建角色动力学
[时间] [INFO] [architecture] 角色动力学构建完成
[时间] [INFO] [architecture] 开始生成初始角色状态
[时间] [INFO] [architecture] 初始角色状态创建并保存成功
[时间] [INFO] [architecture] Step3: 开始搭建世界观
[时间] [INFO] [architecture] 世界观搭建完成
[时间] [INFO] [architecture] Step4: 开始设计情节架构
[时间] [INFO] [architecture] 情节架构设计完成
[时间] [INFO] [architecture] Novel_architecture.txt 生成成功，路径: 路径
[时间] [INFO] [architecture] 小说架构生成流程完成
```

### 3. 章节生成流程

```
[时间] [INFO] [chapter] 开始生成第 N 章
[时间] [DEBUG] [chapter] 读取依赖文件
[时间] [INFO] [chapter] 构建提示词完成
[时间] [INFO] [chapter] 调用LLM生成章节内容
[时间] [INFO] [chapter] 章节生成完成，保存到: 路径
```

### 4. 自动保存流程

自动保存功能在触发时会输出详细的调试日志，包含保存前后的文件内容变化信息：

```
[时间] [DEBUG] [autosave_manager] 加载模式启用，暂停自动保存
[时间] [DEBUG] [autosave_manager] 加载期间跳过Step1自动保存调度
[时间] [DEBUG] [autosave_manager] 加载期间跳过Step2自动保存调度
[时间] [DEBUG] [autosave_manager] 触发Step1自动保存: 小说架构
[时间] [DEBUG] [autosave_manager] [Step1自动保存] === 保存前原始文件状态 ===
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 文件路径: novels/书名/Novel_architecture.txt
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 原始文件长度: 1234 字符
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 原始内容前10字符: "第一章 开头..."
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 原始内容后10字符: "...故事结束。"
[时间] [DEBUG] [autosave_manager] [Step1自动保存] === 保存后文件最终状态 ===
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 文件路径: novels/书名/Novel_architecture.txt
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 更新后文件长度: 1567 字符
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 更新后内容前10字符: "第一章 开头..."
[时间] [DEBUG] [autosave_manager] [Step1自动保存] 更新后内容后10字符: "...新的结局。"
[时间] [DEBUG] [autosave_manager] [Step1自动保存] === 保存操作完成 ===

[时间] [DEBUG] [autosave_manager] 触发Step2自动保存: 章节目录
[时间] [DEBUG] [autosave_manager] [Step2自动保存] === 保存前原始文件状态 ===
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 文件路径: novels/书名/Novel_directory.txt
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 原始文件长度: 500 字符
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 原始内容前10字符: "第一章 相遇..."
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 原始内容后10字符: "...第十章 结局"
[时间] [DEBUG] [autosave_manager] [Step2自动保存] === 保存后文件最终状态 ===
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 文件路径: novels/书名/Novel_directory.txt
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 更新后文件长度: 650 字符
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 更新后内容前10字符: "第一章 相遇..."
[时间] [DEBUG] [autosave_manager] [Step2自动保存] 更新后内容后10字符: "...第十二章 终章"
[时间] [DEBUG] [autosave_manager] [Step2自动保存] === 保存操作完成 ===
[时间] [WARN] [autosave_manager] [Step1自动保存] 警告：新内容为空但原始文件有内容，将清空文件
```

#### 日志字段说明

| 字段 | 说明 |
|------|------|
| 文件路径 | 保存操作的目标文件完整路径 |
| 原始文件长度 | 保存前文件内容的字符数 |
| 原始内容前10字符 | 保存前文件内容的前10个字符（换行符显示为 `\n`） |
| 原始内容后10字符 | 保存前文件内容的后10个字符（换行符显示为 `\n`） |
| 更新后文件长度 | 保存后文件内容的字符数 |
| 更新后内容前10字符 | 保存后文件内容的前10个字符（换行符显示为 `\n`） |
| 更新后内容后10字符 | 保存后文件内容的后10个字符（换行符显示为 `\n`） |

#### 特殊情况处理

- 当文件内容为空时，显示 `(空)`
- 当文件不存在时，原始文件长度为 0，原始内容显示 `(空)`
- 换行符在日志中显示为 `\n`，便于识别内容边界

## 日志文件

### 文件位置

- **主日志文件**：`app.log`（位于项目根目录）
- **调试日志文件**：`debug.log`（可选）

### 日志轮转

当前版本暂不支持自动日志轮转，建议定期手动清理或备份日志文件。

## UI 日志面板

### 功能特性

- 支持按日志级别着色显示
- 自动滚动到底部
- 支持展开/折叠
- 时间轴顺序显示

### 颜色编码

| 级别 | 颜色 |
|------|------|
| DEBUG | 灰色 |
| INFO | 绿色 |
| WARN | 橙色 |
| ERROR | 红色 |

## 测试验证

### 验证清单

- [ ] 所有关键操作都有对应的日志记录
- [ ] 日志时间戳精确到毫秒
- [ ] 日志格式符合规范
- [ ] 日志级别使用正确
- [ ] UI 日志面板正确显示日志
- [ ] 日志同时输出到文件和UI
- [ ] 错误处理中有适当的日志记录

## 附录

### 常见问题

**Q: 如何在新模块中添加日志？**
A: 按照"基础使用"部分的步骤导入和使用 logger。

**Q: 日志级别应该如何选择？**
A: 参考"日志级别"部分的使用指南。

**Q: 如何查看历史日志？**
A: 可以直接打开 `app.log` 文件查看，或在UI日志面板中查看。

### 更新记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.5 | 2026-03-08 | 增加加载模式日志说明，增加空内容保护日志说明 |
| 1.4 | 2026-03-08 | 增强自动保存调试日志，添加保存前后文件内容的前后10字符对比信息 |
| 1.3 | 2026-03-07 | 添加autosave_manager模块日志规范，所有保存操作均输出DEBUG日志 |
| 1.2 | 2026-03-06 | 修改日志输出行为：终端始终显示所有级别日志，UI和文件根据配置决定 |
| 1.1 | 2026-03-05 | 添加开发者模式与DEBUG日志绑定的说明 |
| 1.0 | 2026-03-03 | 初始版本 |

## 开发者模式与日志级别

### 功能说明

应用程序支持开发者模式，该模式与日志系统紧密绑定。日志系统有三个输出渠道，各有不同的行为：

| 输出渠道 | 行为说明 |
|---------|---------|
| **终端** | 总是显示所有级别的日志（包括 DEBUG），无论开发者模式设置如何 |
| **日志文件** | 根据开发者模式设置决定日志级别 |
| **UI 日志面板** | 根据开发者模式设置决定是否显示 DEBUG 级别日志 |

- **开发者模式启用时**：
  - 终端：显示所有日志
  - 文件：记录 DEBUG 及以上级别
  - UI：显示 DEBUG 及以上级别
- **开发者模式禁用时**：
  - 终端：显示所有日志
  - 文件：仅记录 INFO 及以上级别
  - UI：仅显示 INFO 及以上级别

### 配置方式

开发者模式可通过以下方式切换：

1. 打开设置页面
2. 找到"开发者选项"分组
3. 切换"开发者模式"开关

### 启动时日志级别

程序启动时会读取配置文件中的 `developer_mode` 设置：

```python
config = load_config("config.json")
developer_mode = config.get("developer_mode", False)

logger = get_logger()
log_level = LogLevel.DEBUG if developer_mode else LogLevel.INFO
logger.initialize(log_file="app.log", level=log_level, max_records=1000)
```

### 配置加载日志

为避免启动时大量重复的配置加载日志，配置加载成功的日志已改为 DEBUG 级别，并显示调用模块：

```
[2026-03-05 22:02:34.280269] [DEBUG] [config_manager] 配置加载成功: config.json (调用模块: main)
```

## 日志输出渠道说明

### 终端输出

- **特点**：始终显示所有级别日志，不受配置影响
- **用途**：开发调试时的主要调试工具
- **位置**：运行程序的控制台/终端窗口

### 日志文件输出

- **特点**：根据配置的日志级别记录
- **用途**：持久化保存重要日志，便于问题追踪
- **位置**：项目根目录下的 `app.log`

### UI 日志面板输出

- **特点**：根据配置的日志级别显示
- **用途**：在应用界面内查看实时日志
- **位置**：Home 页面右侧的日志面板
