# 文档整合指南

本文档说明如何将项目根目录下的现有文档整合到新的文档体系中。

## 现有文档清单

项目根目录下的现有文档：

| 文件名 | 状态 | 建议处理方式 |
|--------|------|-------------|
| `README.md` | 保留 | 作为项目首页，添加指向 docs/ 的链接 |
| `READMEEN.md` | 保留 | 英文 README |
| `SYSTEM_ARCHITECTURE.md` | 可迁移 | 内容可整合到 `architecture/overview.md` 和 `architecture/data-flow.md` |
| `CODE_GUIDELINES.md` | 可迁移 | 内容可整合到 `development/coding-standards.md` |
| `README_UI_REFACTOR.md` | 归档 | 可移至 `.trae/documents/` 归档 |

## .trae/documents/ 下的文档

这些是项目开发过程中的计划文档，建议保留在原位置作为历史记录：

- `MIGRATION_GUIDE.md`
- `MODULAR_DESIGN.md`
- `QUICK_START.md`
- `ui_refactor_plan.md`
- 其他计划文档

## 整合步骤

### 1. 更新根目录 README.md

在根目录 README.md 顶部添加指向新文档体系的链接：

```markdown
## 📚 文档

完整文档请查看 [docs/](docs/) 目录：

- [快速上手](docs/getting-started/quick-start.md)
- [安装指南](docs/getting-started/installation.md)
- [文档导航](docs/SUMMARY.md)
```

### 2. 迁移 SYSTEM_ARCHITECTURE.md 内容

将 `SYSTEM_ARCHITECTURE.md` 中的内容拆分到：
- 系统总览部分 → `architecture/overview.md`
- 数据流向部分 → `architecture/data-flow.md`
- 模块说明部分 → `architecture/modules/` 下的对应文档

### 3. 迁移 CODE_GUIDELINES.md 内容

将代码规范相关内容整合到 `development/coding-standards.md`

### 4. 归档旧文档

将不再需要的旧文档移至 `.trae/documents/archive/` 目录。

## 注意事项

- 保留所有文档的 Git 历史
- 在迁移前做好备份
- 更新所有内部链接指向新位置
