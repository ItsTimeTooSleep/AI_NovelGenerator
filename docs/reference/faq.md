# 常见问题解答

本页面收集了使用 AI_NovelGenerator 时常见的问题及解决方案。

## 安装相关

### Q: Python 版本有什么要求？

**A:** 需要 Python 3.9 或更高版本，推荐使用 3.10-3.12。

检查 Python 版本：
```bash
python.exe --version
```

### Q: pip install 速度太慢怎么办？

**A:** 使用国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

其他常用镜像源：
- 阿里云: https://mirrors.aliyun.com/pypi/simple/
- 中科大: https://pypi.mirrors.ustc.edu.cn/simple/
- 豆瓣: https://pypi.douban.com/simple/

### Q: PyQt5 安装失败怎么办？

**A:** 尝试指定版本安装：

```bash
pip install PyQt5==5.15.9
```

Windows 用户也可以尝试从 [Python Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt5) 下载预编译的 whl 文件安装。

---

## API 和模型相关

### Q: 支持哪些模型？

**A:** 支持所有 OpenAI 兼容格式的 API，包括：
- OpenAI (GPT-4, GPT-3.5, etc.)
- DeepSeek
- 通义千问
- 智谱 AI
- 本地 Ollama
- 其他 OpenAI 兼容接口

> 详细配置请参考 [配置项详解](config.md)

### Q: 如何使用本地 Ollama？

**A:** 步骤如下：

1. 安装 Ollama：从 https://ollama.ai 下载安装
2. 下载模型：
   ```bash
   ollama pull llama2
   ollama pull nomic-embed-text
   ```
3. 在配置中添加：
   ```json
   {
     "api_key": "ollama",
     "base_url": "http://localhost:11434/v1",
     "interface_format": "OpenAI",
     "model_name": "llama2"
   }
   ```

### Q: API 连接失败怎么办？

**A:** 请检查：
1. API Key 是否正确
2. Base URL 是否正确
3. 网络连接是否正常
4. 防火墙是否阻止请求
5. API 服务是否正常运行

可以在设置页面点击「测试连接」按钮验证配置。

### Q: 报错 "Expecting value: line 1 column 1 (char 0)"

**A:** 通常是 API 返回了非 JSON 响应（如 HTML 错误页面）。常见原因：
- API Key 错误或已过期
- Base URL 错误
- 模型名称错误
- 账户余额不足

---

## 生成相关

### Q: 生成速度太慢怎么办？

**A:** 可以尝试：
1. 减少 `max_tokens` 参数
2. 使用更快的模型
3. 检查网络连接
4. 减少 `embedding_retrieval_k` 的值

### Q: 生成的内容质量不高怎么办？

**A:** 可以尝试：
1. 调整 `temperature` 参数：
   - 降低（如 0.3-0.5）：更稳定、更保守
   - 提高（如 0.8-1.0）：更有创意
2. 使用更强大的模型
3. 完善小说架构和设定
4. 在生成时添加详细的「用户特别指导」

### Q: 章节之间连贯性不够怎么办？

**A:** 建议：
1. 确保每章都点击「定稿章节」，这会更新全局摘要和角色状态
2. 启用向量知识库（配置好 Embedding）
3. 在生成后续章节时，参考前面的章节内容
4. 使用「一致性检查」功能排查问题

### Q: 如何避免角色 OOC（Out of Character）？

**A:** 方法：
1. 在小说架构中详细设定角色性格和能力
2. 确保每章定稿，更新 character_state.txt
3. 在生成时填写「本章涉及角色」参数
4. 定期使用「一致性检查」功能

---

## 数据和文件相关

### Q: 项目文件保存在哪里？

**A:** 所有项目保存在：
```
novels/{项目名称}/
```

### Q: 如何备份项目？

**A:** 直接复制整个项目文件夹即可：
```
novels/{项目名称}/
```

建议定期备份整个 `novels/` 目录。

### Q: 向量数据库可以清空吗？

**A:** 可以。删除 `vectorstore/` 目录即可，但注意：
- 清空后需要重新为已定稿的章节生成 Embedding
- 可能影响后续章节的上下文连贯性

### Q: 可以在不同电脑间迁移项目吗？

**A:** 可以。步骤：
1. 复制 `novels/{项目名称}/` 文件夹到新电脑
2. 确保新电脑有相同版本的 AI_NovelGenerator
3. 打开应用，项目会自动出现在图书馆中

---

## 界面相关

### Q: 如何切换主题？

**A:** 在设置页面可以选择：
- Auto（跟随系统）
- Light（浅色）
- Dark（深色）

### Q: 编辑器支持哪些快捷键？

**A:** 支持：
- `Ctrl + Z`: 撤销
- `Ctrl + Y`: 重做
- `Ctrl + F`: 搜索
- `Ctrl + S`: 保存（部分页面）

### Q: 界面显示异常怎么办？

**A:** 尝试：
1. 重启应用
2. 检查 PyQt5 是否正确安装
3. 删除配置文件重新生成（注意备份 API Key）

---

## 其他问题

### Q: 有推荐的模型配置吗？

**A:** 性价比推荐：
- **LLM**: DeepSeek V3 / GPT-4o-mini
- **Embedding**: OpenAI text-embedding-ada-002 / Ollama nomic-embed-text

### Q: 如何贡献代码？

**A:** 请参考 [贡献指南](../development/contributing.md)

### Q: 发现 Bug 或有功能建议？

**A:** 欢迎在 [GitHub Issues](https://github.com/YILING0013/AI_NovelGenerator/issues) 中提出！

提交 Issue 时请提供：
- 清晰的问题描述
- 复现步骤
- 错误信息（如有）
- 环境信息（Python 版本、操作系统等）

---

## 仍有问题？

如果以上解答无法解决您的问题：
1. 查看是否有相关文档：[文档导航](../SUMMARY.md)
2. 搜索 [GitHub Issues](https://github.com/YILING0013/AI_NovelGenerator/issues)
3. 提交新的 Issue

---

**返回 [文档导航](../SUMMARY.md)**
