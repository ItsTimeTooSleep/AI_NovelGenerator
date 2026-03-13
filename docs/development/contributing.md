# 贡献指南

感谢您对 AI_NovelGenerator 项目的兴趣！我们欢迎各种形式的贡献。

## 行为准则

参与本项目请遵循：
- 尊重他人
- 保持建设性
- 接受不同意见

## 如何贡献

### 1. 报告问题

在提交新 Issue 之前，请先搜索现有 Issues 确认是否已有类似问题。

提交 Issue 时请包含：
- 清晰的标题和描述
- 复现步骤
- 预期行为和实际行为
- 环境信息（Python 版本、操作系统等）
- 错误日志或截图（如有）

### 2. 提交功能建议

功能建议应包含：
- 功能的使用场景
- 期望的实现方式
- 可能的替代方案

### 3. 贡献代码

#### 准备工作

1. Fork 项目仓库
2. 克隆您的 Fork：
   ```bash
   git clone https://github.com/[您的用户名]/AI_NovelGenerator.git
   cd AI_NovelGenerator
   ```
3. 创建虚拟环境（见 [开发环境配置](setup.md)）
4. 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### 开发流程

1. 编写代码
2. 确保代码符合规范（见 [代码规范](coding-standards.md)）
3. 添加或更新测试
4. 运行测试确保通过
5. 提交更改：
   ```bash
   git add .
   git commit -m "feat: 描述您的更改"
   ```

#### 提交 Pull Request

1. 推送到您的 Fork：
   ```bash
   git push origin feature/your-feature-name
   ```
2. 在 GitHub 上创建 Pull Request
3. 填写 PR 模板，确保：
   - 标题清晰描述更改
   - 描述包含更改的目的和实现方式
   - 关联相关 Issue（如有）
   - 列出测试用例

## 代码审查

所有 PR 都需要经过代码审查。审查者可能会：
- 要求代码风格调整
- 建议实现方式改进
- 要求添加测试
- 询问设计决策

请积极配合审查，这是提高代码质量的重要环节！

## 文档贡献

我们同样欢迎文档贡献！

文档贡献包括：
- 修正错别字或语法错误
- 改进文档清晰度
- 添加缺失的文档
- 翻译文档（如需）

## 新手友好的任务

如果您是第一次贡献，可以寻找标有 `good first issue` 或 `help wanted` 的 Issue。

## 获取帮助

如有任何问题，可以：
- 在相关 Issue 下留言
- 提交 Discussion 进行讨论

## 许可证

通过贡献代码，您同意您的贡献将在项目的许可证下发布。

---

**相关文档:**
- [开发环境配置](setup.md)
- [代码规范](coding-standards.md)
- [测试指南](testing.md)

---

**返回 [文档导航](../SUMMARY.md)**
