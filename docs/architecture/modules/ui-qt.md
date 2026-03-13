# UI 模块

## 概述

本文档详细介绍 `ui_qt/` 目录下的 UI 模块，包括主窗口、标签页、工具类和组件。

## 目录结构

```
ui_qt/
├── core/                    # 核心工具
│   └── event_bus.py        # 事件总线
├── home/                    # 首页相关功能
│   ├── composer_features.py # Composer AI 功能
│   ├── project_state_manager.py
│   └── ...
├── settings/                # 设置相关
│   ├── dialogs/
│   └── sections/
├── tabs/                    # 标签页
│   ├── config_tab.py       # 配置页
│   ├── home_tab.py         # 首页
│   ├── library_tab.py      # 图书馆页
│   └── writing_tab.py      # 写作页
├── utils/                   # 工具类
│   ├── notification_manager.py  # 通知管理器
│   ├── animations.py
│   ├── styles.py
│   └── ...
├── widgets/                 # 自定义控件
│   └── ...
└── main_window.py          # 主窗口
```

## 通知管理器 (NotificationManager)

### 概述

`NotificationManager` 提供统一的通知系统，封装了 `qfluentwidgets` 的 `InfoBar` 调用，支持：

- 统一的通知样式和位置
- 错误消息点击复制功能
- 通知历史记录
- 线程安全的通知显示

### 使用方法

```python
from ui_qt.utils.notification_manager import NotificationManager

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._notify = NotificationManager(self)
    
    def on_save_success(self):
        self._notify.success("保存成功", "配置已保存")
    
    def on_error(self, error_msg):
        # 错误通知默认支持复制
        self._notify.error("错误", error_msg, copyable=True)
    
    def on_warning(self):
        self._notify.warning("警告", "磁盘空间不足")
    
    def on_info(self):
        self._notify.info("提示", "正在处理...")
```

### API 参考

#### 构造函数

```python
NotificationManager(
    parent: QWidget,
    position: InfoBarPosition = InfoBarPosition.TOP_RIGHT,
    default_duration: int = 3000
)
```

#### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `success(title, content, duration)` | title: 标题, content: 内容, duration: 时长(ms) | 显示成功通知 |
| `error(title, content, duration, copyable)` | ... | 显示错误通知，默认可复制 |
| `warning(title, content, duration)` | ... | 显示警告通知 |
| `info(title, content, duration)` | ... | 显示信息通知 |
| `persistent(type, title, content, copyable)` | ... | 显示持久通知（不自动关闭） |
| `show_from_thread(type, title, content, ...)` | ... | 从非主线程显示通知 |
| `get_history(limit)` | limit: 最大记录数 | 获取通知历史 |
| `close_all()` | - | 关闭所有活动通知 |

### 线程安全

在非主线程中显示通知时，使用 `show_from_thread` 方法：

```python
def worker_thread():
    # 执行耗时操作
    try:
        result = do_something()
        notify.show_from_thread(NotificationType.SUCCESS, "完成", "操作成功")
    except Exception as e:
        notify.show_from_thread(NotificationType.ERROR, "错误", str(e))
```

## 事件总线 (EventBus)

### 概述

`EventBus` 提供模块间的松耦合通信机制，使用发布/订阅模式。

### 使用方法

```python
from ui_qt.core import EventBus, EventType

# 订阅事件
def on_chapter_changed(event):
    print(f"Chapter changed: {event.data.get('chapter_num')}")

event_bus = EventBus.get_instance()
event_bus.subscribe(EventType.CHAPTER_CHANGED, on_chapter_changed)

# 发布事件
event_bus.publish(
    EventType.CHAPTER_CHANGED,
    source="ChapterLoader",
    chapter_num=5,
    has_content=True
)
```

### 事件类型

| 事件类型 | 说明 |
|---------|------|
| `PROJECT_LOADED` | 项目加载完成 |
| `PROJECT_UNLOADED` | 项目卸载 |
| `CHAPTER_CHANGED` | 章节变化 |
| `GENERATION_STARTED` | 生成开始 |
| `GENERATION_FINISHED` | 生成完成 |
| `GENERATION_ERROR` | 生成错误 |
| `LOG_MESSAGE` | 日志消息 |
| `UI_STATE_CHANGED` | UI 状态变化 |

---

## 项目状态管理器 (ProjectStatusManager)

### 概述

`ProjectStatusManager` 负责统一管理项目的所有状态信息，包括：
- Step 1/2 的完成状态和阶段性数据
- 章节的草稿/定稿状态
- 生成步骤的时间记录

采用统一的 `project_status.json` 文件存储，支持一致性检查。

---

## 状态控制器 (StateController)

### 概述

`StateController` 是新增的状态控制器，负责统一管理项目状态转换和UI更新。它采用配置驱动的方式，将状态定义与UI更新逻辑分离，简化了状态管理。

### 核心概念

#### 状态枚举

```python
from ui_qt.home import ProjectState, InitStackPage, ActionsStackPage, LayoutMode

# 项目状态
class ProjectState(Enum):
    NO_PROJECT = auto()           # 无项目
    STEP1_NOT_STARTED = auto()    # Step 1 未开始
    STEP1_IN_PROGRESS = auto()    # Step 1 进行中
    STEP1_COMPLETED = auto()      # Step 1 已完成
    STEP1_REVIEW = auto()         # Step 1 查看模式
    STEP2_NOT_STARTED = auto()    # Step 2 未开始
    STEP2_IN_PROGRESS = auto()    # Step 2 进行中
    PROJECT_READY = auto()        # 项目已就绪
    STEP3_ACTIVE = auto()         # Step 3 活动中
    STEP4_ACTIVE = auto()         # Step 4 活动中

# 初始化堆栈页面
class InitStackPage(Enum):
    NO_PROJECT = "frameNoProject"
    STEP1 = "frameStep1"
    STEP1_REVIEW = "frameStep1Review"
    STEP2 = "frameStep2"
    READY = "frameInitDone"

# 操作堆栈页面
class ActionsStackPage(Enum):
    LOCKED = "frameActionsLocked"
    STEP3 = "frameStep3Actions"
    STEP4 = "frameStep4Actions"

# 布局模式
class LayoutMode(Enum):
    SIMPLIFIED = "simplified"
    FULL = "full"
```

### 使用方法

```python
from ui_qt.home import StateController, ProjectState

# 初始化（在 HomeTab 中自动完成）
state_controller = StateController(home_tab)

# 切换状态
state_controller.transition_to(ProjectState.STEP1_COMPLETED)

# 切换状态并传递额外参数
state_controller.transition_to(ProjectState.STEP3_ACTIVE, chapter_num=5)

# 静默切换（不记录日志）
state_controller.transition_to(ProjectState.STEP2_NOT_STARTED, silent=True)

# 获取当前状态
current_state = state_controller.current_state

# 添加状态变化监听器
def on_state_changed(old_state, new_state):
    print(f"状态从 {old_state} 变为 {new_state}")

state_controller.add_state_change_listener(on_state_changed)

# 检查当前状态
is_full_mode = state_controller.is_in_full_mode()
is_step4 = state_controller.is_step4_active()
```

### 状态配置表

每个状态对应特定的UI配置：

| 状态 | initStack | actionsStack | 布局 | 关键组件 |
|------|-----------|--------------|------|---------|
| NO_PROJECT | frameNoProject | LOCKED | 简化 | 无 |
| STEP1_NOT_STARTED | frameStep1 | LOCKED | 简化 | step1Btn |
| STEP1_IN_PROGRESS | frameStep1 | LOCKED | 简化 | stopStep1Btn |
| STEP1_COMPLETED | frameStep1 | LOCKED | 简化 | continueToStep2Btn |
| STEP1_REVIEW | frameStep1Review | LOCKED | 简化 | 箭头 |
| STEP2_NOT_STARTED | frameStep2 | LOCKED | 简化 | step2Btn |
| STEP2_IN_PROGRESS | frameStep2 | LOCKED | 简化 | stopStep2Btn |
| PROJECT_READY | frameInitDone | LOCKED | 简化 | continueToStep3Btn |
| STEP3_ACTIVE | frameInitDone | STEP3 | 完整 | step3Btn |
| STEP4_ACTIVE | frameInitDone | STEP4 | 完整 | step4Btn |

### 设计优势

1. **配置驱动**: 所有UI配置通过数据类定义，便于维护
2. **单一职责**: 状态控制器只负责状态转换和UI更新
3. **解耦**: 业务逻辑模块不再直接操作UI组件
4. **可扩展**: 新增状态只需添加配置，无需修改核心逻辑
5. **可测试**: 状态转换逻辑集中，易于单元测试

### 与其他模块的关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         状态管理架构                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │ StepManager  │     │ ProjectState     │     │ GenerationFlow   │    │
│  │              │     │ Manager          │     │ Manager          │    │
│  │ 业务逻辑     │     │ 业务逻辑         │     │ 业务逻辑         │    │
│  └──────┬───────┘     └────────┬─────────┘     └────────┬─────────┘    │
│         │                      │                        │               │
│         └──────────────────────┼────────────────────────┘               │
│                                ▼                                        │
│                    ┌───────────────────────┐                            │
│                    │   StateController     │                            │
│                    │   状态切换 + UI更新   │                            │
│                    └───────────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 状态文件格式

文件位置: `{project_path}/project_status.json`

```json
{
    "version": 1,
    "step1": {
        "completed": false,
        "current_step": 3,
        "total_steps": 6,
        "steps_time": {
            "书名生成": 12.5,
            "核心种子生成": 45.2
        },
        "partial_data": {
            "generated_title": "...",
            "core_seed_result": "..."
        }
    },
    "step2": {
        "completed": false,
        "current_step": 0,
        "total_steps": 3,
        "steps_time": {},
        "partial_data": {}
    },
    "chapters": {
        "1": {
            "draft_generated": true,
            "draft_generated_at": "2026-03-09T10:30:00",
            "finalized": false,
            "finalized_at": null,
            "word_count": 3500
        }
    },
    "last_finalized_chapter": 0
}
```

### 一致性检查策略

状态优先级: **文件实际状态 > 状态文件记录**

检查规则:
1. Step 1 完成状态: 检查 `Novel_architecture.txt` 是否存在且有内容
2. Step 2 完成状态: 检查 `Novel_directory.txt` 是否存在且有内容
3. 章节草稿状态: 检查 `chapter_{num}.txt` 是否存在且有内容
4. 章节定稿状态: 检查 `global_summary.txt` 是否包含该章节信息

检查时机:
- 项目加载时
- 状态文件加载时

### 使用方法

```python
from ui_qt.home import ProjectStatusManager

# 初始化
status_manager = ProjectStatusManager(home_tab)
status_manager.set_project(project_path)

# Step 1/2 状态
is_step1_done = status_manager.is_step1_completed()
is_step2_done = status_manager.is_step2_completed()
partial_data = status_manager.get_step1_partial_data()

# 章节状态
is_draft = status_manager.is_draft_generated(1)
is_finalized = status_manager.is_finalized(1)

# 标记状态
status_manager.mark_draft_generated(1, word_count=3500)
status_manager.mark_finalized(1)
status_manager.mark_step1_completed()
status_manager.mark_step2_completed()

# 更新进度
status_manager.update_step1_progress(
    step_index=2,
    step_name="核心种子生成",
    step_time=45.2,
    step_data_key="core_seed_result",
    step_data_value="..."
)

# 获取最后定稿的章节
last_finalized = status_manager.get_last_finalized_chapter()

# 获取下一个需要处理的章节
next_chapter = status_manager.get_next_chapter_to_work_on()

# 手动执行一致性检查
corrections = status_manager.run_consistency_check()
```

### API 参考

#### Step 1/2 状态管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `is_step1_completed()` | - | bool | 检查 Step 1 是否已完成 |
| `is_step2_completed()` | - | bool | 检查 Step 2 是否已完成 |
| `get_step1_current_step()` | - | int | 获取 Step 1 当前步骤索引 |
| `get_step1_partial_data()` | - | Dict | 获取 Step 1 阶段性数据 |
| `get_step1_steps_time()` | - | Dict[str, float] | 获取 Step 1 各步骤耗时 |
| `update_step1_progress(...)` | step_index, step_name, step_time, step_data_key, step_data_value | bool | 更新 Step 1 进度 |
| `mark_step1_completed()` | - | bool | 标记 Step 1 已完成 |
| `reset_step1()` | - | bool | 重置 Step 1 状态 |
| `is_step2_completed()` | - | bool | 检查 Step 2 是否已完成 |
| `mark_step2_completed()` | - | bool | 标记 Step 2 已完成 |
| `reset_step2()` | - | bool | 重置 Step 2 状态 |

#### 章节状态管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `is_draft_generated(chapter_num)` | chapter_num: 章节号 | bool | 检查草稿是否已生成 |
| `is_finalized(chapter_num)` | chapter_num: 章节号 | bool | 检查是否已定稿 |
| `mark_draft_generated(chapter_num, word_count)` | 章节号, 字数 | bool | 标记草稿已生成 |
| `mark_finalized(chapter_num)` | chapter_num: 章节号 | bool | 标记已定稿 |
| `mark_draft_regenerating(chapter_num)` | chapter_num: 章节号 | bool | 标记正在重新生成（重置定稿状态） |
| `get_chapter_status(chapter_num)` | chapter_num: 章节号 | ChapterStatus | 获取章节状态对象 |
| `get_last_finalized_chapter()` | - | int | 获取最后定稿的章节号 |
| `get_next_chapter_to_work_on()` | - | int | 获取下一个需要处理的章节 |

### 设计优势

1. **统一管理**: 所有状态在一个文件中，减少文件碎片
2. **状态清晰**: 一眼看出项目和每章节的完整生命周期
3. **易于查询**: 不需要解析文件内容来判断状态
4. **支持统计**: 可记录步骤耗时、字数等元数据
5. **断点恢复**: 重启应用后可精确恢复到之前的状态
6. **解耦**: 状态管理与文件内容分离，更易维护
7. **一致性保证**: 自动检测并修正状态不一致问题

## 待完善内容

- [ ] main_window.py 详解
- [ ] 各标签页详解
- [ ] 组件和对话框详解

## 悬停提示组件 (HoverInfoIcon)

### 概述

`HoverInfoIcon` 提供悬停显示详细提示信息的组件，支持：
- 在标题旁显示问号图标
- 鼠标悬停时显示可滚动的提示框
- 支持HTML格式的富文本内容
- 支持鼠标拖拽滚动长文本

### 使用方法

```python
from ui_qt.widgets.hover_info_icon import HoverInfoIcon

# 创建悬停提示图标
info_icon = HoverInfoIcon(
    content="<p>这是提示内容</p>",
    icon_size=14,
    parent=self
)

# 动态更新提示内容
info_icon.setContent("<p>新的提示内容</p>")
```

### API 参考

#### 构造函数

```python
HoverInfoIcon(
    content: str = "",      # HTML格式的提示内容
    icon_size: int = 16,    # 图标大小
    parent=None             # 父控件
)
```

#### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `setContent(content)` | content: HTML格式内容 | 设置提示内容 |

## 带提示的设置卡片 (SettingCardWithTooltip)

### 概述

`SettingCardWithTooltip` 和 `OptionsSettingCardWithTooltip` 是带悬停提示的设置卡片组件，在标题旁显示问号图标。

### 使用方法

```python
from ui_qt.widgets.setting_card_with_tooltip import OptionsSettingCardWithTooltip

# 创建带提示的选项设置卡片
card = OptionsSettingCardWithTooltip(
    configItem=config_item,
    icon=FIF.ROBOT,
    title="AI 等级",
    content="选择 Composer AI 的智能等级",
    tooltip_content="<p>详细的等级说明...</p>",
    texts=["mini (精简)", "standard (标准)", "pro (专业)"],
    parent=self
)
```

## 差异预览管理器 (DiffPreviewManager)

### 概述

`DiffPreviewManager` 提供统一的差异预览功能，支持两种显示模式：

- **弹窗模式 (dialog)**: 在独立弹窗中显示差异，适合长文本和需要仔细审核的场景
- **行内模式 (inline)**: 在编辑器中直接显示差异，适合短文本和快速修改的场景

### 使用方法

```python
from ui_qt.widgets import DiffPreviewManager, get_diff_preview_mode_from_config

class MyEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.diff_preview_manager = None
    
    def show_ai_diff(self, original_text, modified_text, config):
        # 从配置获取预览模式
        mode = get_diff_preview_mode_from_config(config)
        
        # 创建差异预览管理器
        self.diff_preview_manager = DiffPreviewManager(
            editor=self.editor,
            parent=self,
            mode=mode
        )
        
        # 连接信号
        self.diff_preview_manager.changes_accepted.connect(self.apply_changes)
        self.diff_preview_manager.changes_rejected.connect(self.reject_changes)
        
        # 显示差异
        self.diff_preview_manager.show_diff(
            original_text, 
            modified_text,
            selection_start=0,
            selection_end=len(original_text)
        )
```

### API 参考

#### 构造函数

```python
DiffPreviewManager(
    editor: QWidget,
    parent: QWidget = None,
    mode: str = "dialog"
)
```

#### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `show_diff(original, modified, start, end)` | 原始文本, 修改后文本, 选区开始, 选区结束 | 显示差异预览 |
| `set_mode(mode)` | mode: "dialog" 或 "inline" | 设置预览模式 |
| `is_showing_diff()` | - | 检查是否正在显示差异 |
| `cleanup()` | - | 清理所有资源 |

#### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `changes_accepted` | modified_text: str | 用户接受修改 |
| `changes_rejected` | - | 用户拒绝修改 |

### 配置项

在 `config.json` 的 `composer_settings` 中设置：

```json
{
    "composer_settings": {
        "diff_preview_mode": "dialog"  // 或 "inline"
    }
}
```

---

## 嵌入式Composer输入组件 (InlineComposerInputWidget)

### 概述

`InlineComposerInputWidget` 提供嵌入到编辑器中的Composer输入组件，替代传统的弹窗式输入框。主要特点：

- 在选中文本上方动态展开输入框
- 平滑的展开/收起动画效果
- 柔和的阴影效果增强视觉层次感
- 点击其他区域自动收起
- 支持 AI 等级切换（mini/standard/pro）

### 使用方法

```python
from ui_qt.widgets.inline_composer_widget import InlineComposerInputWidget

class MyEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inline_composer = InlineComposerInputWidget(
            selected_text="",
            ai_level="standard",
            parent=self
        )
        self.inline_composer.query_submitted.connect(self.on_query_submitted)
        self.inline_composer.ai_level_changed.connect(self.on_ai_level_changed)
    
    def show_inline_composer(self, selected_text, global_pos, editor_rect):
        self.inline_composer.set_selected_text(selected_text)
        self.inline_composer.show_at_position(global_pos, editor_rect)
    
    def on_query_submitted(self, query):
        # 处理用户提交的查询
        pass
```

### API 参考

#### 构造函数

```python
InlineComposerInputWidget(
    selected_text: str = "",    # 选中的文本
    ai_level: str = "standard", # AI等级 (mini/standard/pro)
    parent=None                 # 父控件（通常是编辑器）
)
```

#### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `show_at_position(global_pos, editor_rect)` | 全局坐标位置, 编辑器矩形区域 | 在指定位置展开输入框 |
| `collapse()` | - | 平滑收起输入框 |
| `is_expanded()` | - | 检查输入框是否展开 |
| `set_selected_text(text)` | text: 选中文本 | 设置选中文本 |
| `set_ai_level(level)` | level: AI等级 | 设置AI等级 |

#### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `query_submitted` | query: str | 用户提交查询 |
| `ai_level_changed` | level: str | AI等级变化 |
| `closed` | - | 输入框关闭 |

### 阴影效果

组件默认配置了柔和的阴影效果：
- 模糊半径：20px
- 颜色：rgba(0, 0, 0, 60)
- 偏移：(0, 4)

---

**相关文档:**
- [系统总览](../overview.md)
- [核心模块](core.md)
- [小说生成器](novel-generator.md)

---

**返回 [文档导航](../../SUMMARY.md)**
