# 代码规范

本文档定义 AI_NovelGenerator 项目的代码规范和最佳实践。

## Python 代码规范

### 通用原则

1. **遵循 PEP 8**: 所有 Python 代码应符合 PEP 8 规范
2. **类型提示**: 所有函数应使用类型提示
3. **文档字符串**: 所有公共函数和类应有文档字符串

### 代码格式化

使用以下工具自动格式化代码：

```bash
# 格式化代码
black .

# 排序导入
isort .

# 代码检查
flake8 .
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/包 | 小写+下划线 | `config_manager.py` |
| 类 | 大驼峰 | `ConfigManager` |
| 函数/方法 | 小写+下划线 | `load_config()` |
| 常量 | 全大写+下划线 | `MAX_TOKENS = 4096` |
| 变量 | 小写+下划线 | `api_key` |

### 类型提示示例

```python
from typing import Dict, List, Optional

def load_config(file_path: str) -> Dict[str, str]:
    """
    加载配置文件。
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        FileNotFoundError: 文件不存在时
        json.JSONDecodeError: JSON 解析错误时
    """
    pass
```

### 文档字符串规范

使用 Google 风格的文档字符串：

```python
def generate_chapter(
    chapter_number: int,
    user_guidance: Optional[str] = None
) -> str:
    """
    生成指定章节的内容。
    
    这个函数会读取小说架构、目录和角色状态，
    构建提示词并调用 LLM 生成章节内容。
    
    Args:
        chapter_number: 章节号（从1开始）
        user_guidance: 用户特别指导，可选
        
    Returns:
        生成的章节内容字符串
        
    Examples:
        >>> content = generate_chapter(1, "重点描写主角醒来的场景")
        >>> print(content[:100])
        
    Notes:
        - 确保 Novel_architecture.txt 存在
        - 确保 config.json 已正确配置
    """
    pass
```

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 提交示例

```
feat(ui): 添加主题切换功能

- 支持 Auto/Light/Dark 三种主题
- 主题设置保存到 config.json
- 添加主题预览

Closes #123
```

## 模块设计原则

### 单一职责

每个模块/类应该只有一个改变的理由。

### 依赖注入

优先使用依赖注入而非硬编码依赖：

```python
# 不推荐
class ChapterGenerator:
    def __init__(self):
        self.llm_adapter = LLMAdapter()  # 硬编码

# 推荐
class ChapterGenerator:
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm_adapter = llm_adapter  # 依赖注入
```

### 错误处理

使用明确的异常类型，提供有意义的错误信息：

```python
class ConfigError(Exception):
    """配置相关错误"""
    pass

def load_config():
    if not os.path.exists("config.json"):
        raise ConfigError("配置文件不存在: config.json")
```

---

**相关文档:**
- [开发环境配置](setup.md)
- [测试指南](testing.md)
- [贡献指南](contributing.md)

---

**返回 [文档导航](../SUMMARY.md)**
