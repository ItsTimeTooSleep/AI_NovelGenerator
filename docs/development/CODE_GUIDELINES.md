# AI小说生成器 - 代码管理规范

## 1. 命名约定

### 1.1 文件和目录命名
- 使用小写字母和下划线 (snake_case)
- 例如: `config_manager.py`, `novel_generator/`

### 1.2 类命名
- 使用大驼峰命名法 (PascalCase)
- 例如: `class HomeTab(QWidget):`

### 1.3 函数和方法命名
- 使用小写字母和下划线 (snake_case)
- 例如: `def load_config(config_file: str) -> dict:`

### 1.4 变量命名
- 使用小写字母和下划线 (snake_case)
- 例如: `current_project_path = ""`

### 1.5 常量命名
- 使用全大写字母和下划线 (UPPER_SNAKE_CASE)
- 例如: `GITHUB_REPO_URL = "https://github.com/Doctor-Shadow/AI_NovelGenerator"`

## 2. 文件组织结构

### 2.1 项目根目录
```
AI_NovelGenerator-main/
├── config_manager.py          # 配置管理
├── utils.py                   # 通用工具函数
├── version.py                 # 版本信息
├── tooltips.py                # 工具提示
├── embedding_adapters.py      # 嵌入模型适配器
├── llm_adapters.py            # 大语言模型适配器
├── tokens_manager.py          # Token管理
├── prompt_definitions.py      # 提示词定义
├── consistency_checker.py     # 一致性检查
├── chapter_directory_parser.py # 章节目录解析
├── main.py                    # 主程序入口
├── build_qt.py                # 构建脚本
├── novel_generator/           # 小说生成核心模块
├── ui_qt/                     # Qt UI模块
├── config/                    # 配置文件目录
├── novels/                    # 小说项目存储目录
├── .trae/                     # Trae IDE配置
├── .github/                   # GitHub配置
├── venv/                      # 虚拟环境 (不提交)
└── docs/                      # 文档
```

### 2.2 novel_generator/ 模块
- `architecture.py`: 小说架构生成
- `blueprint.py`: 章节蓝图生成
- `chapter.py`: 章节内容生成
- `composer.py`: Composer AI功能
- `finalization.py`: 章节定稿
- `knowledge.py`: 知识库管理
- `project_manager.py`: 项目管理
- `vectorstore_utils.py`: 向量存储工具
- `common.py`: 公共函数

### 2.3 ui_qt/ 模块
- `home_tab.py`: 主界面标签页
- `main_window.py`: 主窗口
- `settings_tab.py`: 设置标签页
- `home/`: 主界面子模块
- `settings/`: 设置界面子模块
- 其他标签页和组件

## 3. 模块间依赖关系

### 3.1 依赖原则
- 核心模块 (novel_generator/) 不应依赖 UI 模块
- UI 模块可以依赖核心模块
- 工具模块 (config_manager, utils等) 可被所有模块依赖
- 避免循环依赖

### 3.2 导入顺序 (isort配置)
1. 标准库导入
2. 第三方库导入
3. 本地模块导入
4. 每个部分之间空一行

## 4. 代码格式化工具链

### 4.1 工具配置
项目使用以下工具进行代码格式化和检查：

- **autoflake**: 清理未使用的导入和变量
- **isort**: 优化导入顺序
- **black**: 统一代码格式
- **flake8**: 静态代码检查

### 4.2 运行命令
```powershell
# 1. 清理未使用的导入
venv\Scripts\autoflake.exe --remove-all-unused-imports --remove-unused-variables --in-place --recursive --exclude venv,__pycache__,.git .

# 2. 优化导入顺序
venv\Scripts\isort.exe --skip venv --skip __pycache__ --skip .git .

# 3. 统一代码格式
venv\Scripts\black.exe --exclude '/(venv|__pycache__|\.git)/' .

# 4. 静态代码检查
venv\Scripts\flake8.exe --exclude venv,__pycache__,.git .
```

### 4.3 配置文件
- `.flake8`: flake8配置
- `.isort.cfg`: isort配置

## 5. 代码注释规范

### 5.1 函数注释
使用文档字符串描述函数的功能、参数、返回值和异常：

```python
def load_config(config_file: str) -> dict:
    """
    从指定的 config_file 加载配置，若不存在则创建一个默认配置文件。
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        dict: 加载的配置字典
        
    Raises:
        无，异常时返回空字典
    """
```

### 5.2 行内注释
- 使用 `#` 进行行内注释
- 注释应解释"为什么"而不是"是什么"
- 注释与代码之间空一格

## 6. Git提交规范

### 6.1 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 6.2 Type类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 7. 最佳实践

### 7.1 异常处理
- 避免使用裸的 `except:`
- 捕获具体的异常类型
- 提供有意义的错误信息

### 7.2 类型提示
- 为函数参数和返回值添加类型提示
- 使用 `typing` 模块中的类型

### 7.3 代码复用
- 提取重复代码为函数或类
- 优先使用现有的工具函数
- 避免复制粘贴代码

## 8. 测试

### 8.1 测试原则
- 核心功能应有单元测试
- UI功能可进行手动测试
- 重构后进行完整功能验证
