# -*- coding: utf-8 -*-
"""
Composer AI写作助手模块

================================================================================
模块功能概述
================================================================================
本模块实现了Composer AI写作助手的核心业务逻辑，为编辑器提供智能写作辅助功能。
支持语法修正、文本润色、内容扩写、问题查询等多种AI辅助功能。

================================================================================
核心类
================================================================================
- ComposerPromptBuilder: 提示词构建器，根据AI等级构建不同复杂度的提示词
- ComposerAIService: AI服务封装，处理AI请求和响应

================================================================================
AI等级说明
================================================================================
- mini: 基础模式，仅处理当前文本片段，响应速度快
- standard: 标准模式，包含章节上下文信息，平衡质量和速度
- pro: 专业模式，整合完整故事框架、蓝图及角色状态，质量最高

================================================================================
支持的任务类型
================================================================================
- grammar: 语法修正，修正文本中的语法错误
- polish: 文本润色，优化表达增强感染力
- expand: 内容扩写，根据指定类型扩展描写
- query: 问题查询，回答与选中文本相关的问题

================================================================================
设计决策
================================================================================
- 分层提示词设计，适应不同使用场景
- 上下文信息按需加载，控制Token消耗
- 支持自定义LLM适配器，兼容多种模型

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os


class ComposerPromptBuilder:
    """
    Composer提示词构建器

    根据不同的AI等级构建相应的提示词。
    """

    AI_LEVELS = {
        "mini": "基础提示词构建，仅处理当前文本片段",
        "standard": "增强提示词，包含上下文信息",
        "pro": "高级提示词，整合整个章节内容、故事框架、蓝图及角色状态",
    }

    def __init__(self, ai_level="standard", project_path=""):
        """
        初始化提示词构建器

        Args:
            ai_level: AI等级 (mini/standard/pro)
            project_path: 项目路径，用于读取上下文文件
        """
        self.ai_level = ai_level
        self.project_path = project_path

    def build_prompt(
        self, task_type, selected_text, user_query="", conversation_context="", **kwargs
    ):
        """
        构建提示词

        Args:
            task_type: 任务类型 (grammar/polish/expand/query)
            selected_text: 选中文本
            user_query: 用户查询（可选）
            conversation_context: 对话上下文（用于多轮对话）
            **kwargs: 其他参数

        Returns:
            str: 构建好的提示词
        """
        base_prompt = self._get_base_prompt(
            task_type, selected_text, user_query, conversation_context
        )
        context = self._get_context()

        if self.ai_level == "mini":
            return base_prompt
        elif self.ai_level == "standard":
            return base_prompt + "\n\n" + context.get("chapter", "")
        else:
            full_context = "\n\n".join(
                [
                    context.get("architecture", ""),
                    context.get("directory", ""),
                    context.get("character", ""),
                    context.get("global_summary", ""),
                    context.get("chapter", ""),
                ]
            )
            return base_prompt + "\n\n" + full_context

    def _get_base_prompt(
        self, task_type, selected_text, user_query, conversation_context=""
    ):
        """
        获取基础提示词

        Args:
            task_type: 任务类型
            selected_text: 选中文本
            user_query: 用户查询
            conversation_context: 对话上下文

        Returns:
            str: 基础提示词
        """
        prompts = {
            "grammar": self._build_grammar_prompt(selected_text),
            "polish": self._build_polish_prompt(selected_text),
            "expand": self._build_expand_prompt(selected_text, user_query),
            "query": self._build_query_prompt(
                selected_text, user_query, conversation_context
            ),
        }

        return prompts.get(task_type, "")

    def _build_grammar_prompt(self, selected_text):
        """
        构建语法修正提示词

        Args:
            selected_text: 选中文本

        Returns:
            str: 语法修正提示词
        """
        return f"""# 角色定位
你是一位资深的文学编辑，精通中文语法规范和文学创作技巧。你的任务是修正文本中的语法错误，同时保持原文的文学风格和表达意图。

# 修正范围
请检查并修正以下类型的语法问题：
1. **句法错误**：句子成分残缺、语序不当、句式杂糅等
2. **用词错误**：词语搭配不当、词性误用、近义词混淆等
3. **标点错误**：标点符号使用不规范或错误
4. **逻辑错误**：前后矛盾、因果倒置、主客颠倒等
5. **冗余问题**：成分赘余、语义重复等

# 修正原则
- 保持原文的风格基调和叙事视角
- 不改变原文的核心意思和情感表达
- 仅修正明确的语法错误，不过度修改
- 保留原文的文学性和个人写作特色

# 待修正文本
{selected_text}

# 输出格式要求
你必须严格按照以下格式输出修正后的文本，不要输出任何其他内容：
[SUGGESTION]修正后的文本[/SUGGESTION]"""

    def _build_polish_prompt(self, selected_text):
        """
        构建文本润色提示词

        Args:
            selected_text: 选中文本

        Returns:
            str: 文本润色提示词
        """
        return f"""# 角色定位
你是一位资深的文学润色专家，精通中文修辞艺术和叙事技巧。你的任务是优化文本表达，使其更加优美流畅、富有感染力。

# 润色方向
请从以下维度进行润色：

## 语言层面
1. **词汇优化**：选用更精准、更有表现力的词语
2. **句式调整**：长短句搭配、句式变化、节奏感
3. **修辞运用**：恰当使用比喻、拟人、排比等修辞手法

## 叙事层面
1. **画面感**：增强描写的视觉化效果和场景感
2. **情感张力**：强化情感表达的深度和力度
3. **节奏韵律**：优化叙事节奏，增强阅读流畅度

## 风格层面
1. **保持一致性**：与原文风格基调保持协调
2. **突出特色**：适度强化原文的写作特色
3. **避免过度**：润色要恰到好处，不过分雕琢

# 润色原则
- 保持原文的核心意思和情感基调
- 保持原文的叙事视角和人物性格
- 润色后的文本应自然流畅，不留雕琢痕迹
- 尊重作者的个人写作风格

# 待润色文本
{selected_text}

# 输出格式要求
你必须严格按照以下格式输出润色后的文本，不要输出任何其他内容：
[SUGGESTION]润色后的文本[/SUGGESTION]"""

    def _build_expand_prompt(self, selected_text, expand_type):
        """
        构建扩展描写提示词

        Args:
            selected_text: 选中文本
            expand_type: 扩展类型

        Returns:
            str: 扩展描写提示词
        """
        expand_guides = {
            "心理描写": {
                "description": "深入刻画人物内心世界",
                "techniques": [
                    "内心独白：展现人物的真实想法和情感波动",
                    "情感层次：呈现情感的递进、转折和复杂性",
                    "潜意识流露：通过闪回、联想揭示深层心理",
                    "矛盾冲突：展现内心的挣扎、犹豫和抉择",
                    "感官体验：将心理活动与身体感受相结合",
                ],
                "principles": [
                    "心理描写要与人物性格和当前处境相符",
                    "避免过度直白，善用暗示和象征",
                    "注意心理变化的逻辑性和连贯性",
                    "与外部行为和环境描写相呼应",
                ],
            },
            "神态描写": {
                "description": "细腻刻画人物面部表情和神态变化",
                "techniques": [
                    "眼神描写：目光的方向、焦点、情感色彩",
                    "微表情：瞬间的表情变化揭示内心活动",
                    "面部肌肉：眉头、嘴角、眼角等细节变化",
                    "神态与情绪：表情如何反映内心状态",
                    "习惯性神态：人物特有的表情习惯",
                ],
                "principles": [
                    "神态描写要服务于人物塑造和情节推进",
                    "避免千篇一律的表情描写",
                    "注意神态与对话、动作的协调配合",
                    "善用对比和变化展现人物状态",
                ],
            },
            "动作描写": {
                "description": "生动展现人物的行为动作",
                "techniques": [
                    "动作分解：将复杂动作分解为连续的细节",
                    "力量与节奏：表现动作的力度、速度和韵律",
                    "动作特征：体现人物的性格和习惯",
                    "环境互动：动作与周围事物的关系",
                    "无声语言：通过动作传达情感和意图",
                ],
                "principles": [
                    "动作要符合人物的身份、性格和当前状态",
                    "避免流水账式的动作罗列",
                    "动作描写要有选择性和目的性",
                    "与心理、神态描写相结合",
                ],
            },
            "环境描写": {
                "description": "营造场景氛围和空间感",
                "techniques": [
                    "感官细节：视觉、听觉、嗅觉、触觉的综合运用",
                    "空间层次：远近、高低、内外的空间布局",
                    "光影效果：光线、阴影、色彩的描写",
                    "氛围营造：环境如何烘托情绪和主题",
                    "动态变化：环境随时间或事件的改变",
                ],
                "principles": [
                    "环境描写要服务于叙事需要",
                    "避免脱离情节的孤立描写",
                    "注意环境与人物心境的呼应",
                    "详略得当，突出重点",
                ],
            },
            "对话补充": {
                "description": "丰富对话内容和表现力",
                "techniques": [
                    "语言风格：体现人物的身份、性格和背景",
                    "潜台词：言外之意和未尽之言",
                    "对话节奏：长短句交替、停顿和沉默",
                    "动作穿插：说话时的神态和动作",
                    "对话张力：冲突、试探、交锋",
                ],
                "principles": [
                    "对话要符合人物的性格和说话习惯",
                    "避免过于书面化或过于口语化",
                    "对话要有信息量和推动力",
                    "注意对话的自然流畅",
                ],
            },
        }

        guide = expand_guides.get(expand_type, expand_guides["心理描写"])

        techniques_text = "\n".join([f"  - {t}" for t in guide["techniques"]])
        principles_text = "\n".join([f"  - {p}" for p in guide["principles"]])

        return f"""# 角色定位
你是一位资深的小说作家，精通各类描写技巧。你的任务是进行专业的【{expand_type}】，{guide["description"]}。

# 写作技巧
{techniques_text}

# 写作原则
{principles_text}

# 扩展要求
1. 扩展内容要与原文风格保持一致
2. 扩展要自然融入原文，不显突兀
3. 扩展幅度适中，一般为原文的1.5-3倍长度
4. 注重描写的真实感和感染力

# 原文
{selected_text}

# 输出格式要求
你必须严格按照以下格式输出扩展后的文本，不要输出任何其他内容：
[SUGGESTION]扩展后的文本[/SUGGESTION]"""

    def _build_query_prompt(self, selected_text, user_query, conversation_context):
        """
        构建问题查询提示词

        Args:
            selected_text: 选中文本
            user_query: 用户查询
            conversation_context: 对话上下文

        Returns:
            str: 问题查询提示词
        """
        context_section = (
            f"\n# 对话历史\n{conversation_context}\n" if conversation_context else ""
        )

        return f"""# 角色定位
你是Composer，一位资深的小说创作顾问和文学编辑。你精通叙事学、人物塑造、情节设计、文体风格等文学创作的各个方面，能够为作家提供专业、深入、有建设性的指导。

# 专业领域
1. **叙事技巧**：视角选择、时间处理、叙事节奏、悬念设置等
2. **人物塑造**：性格刻画、人物弧光、关系设计、对话艺术等
3. **情节设计**：结构布局、冲突设置、高潮设计、伏笔照应等
4. **文体风格**：语言风格、修辞手法、氛围营造、意象运用等
5. **创作理论**：类型写作、读者心理、市场趋势等

# 回答原则
1. **专业性**：提供有理论支撑和实践价值的建议
2. **针对性**：紧扣用户的具体问题和文本内容
3. **建设性**：给出可操作的具体建议和改进方向
4. **启发性**：帮助用户打开思路，发现更多可能性
5. **尊重性**：尊重作者的创作意图和个人风格

# 选中文本上下文
{selected_text}
{context_section}
# 用户问题
{user_query}

请基于以上信息，给出专业、深入、有建设性的回答。你可以自由组织回答内容，必要时可以引用文学理论或经典作品作为例证。"""

    def _get_context(self):
        """
        获取上下文信息

        Returns:
            dict: 包含各种上下文信息的字典
        """
        context = {
            "architecture": "",
            "directory": "",
            "character": "",
            "global_summary": "",
            "chapter": "",
        }

        if not self.project_path:
            return context

        file_mappings = {
            "architecture": "Novel_architecture.txt",
            "directory": "Novel_directory.txt",
            "character": "character_state.txt",
            "global_summary": "global_summary.txt",
        }

        for key, filename in file_mappings.items():
            filepath = os.path.join(self.project_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read(2000)
                        if content:
                            context[key] = f"--- {filename} ---\n{content}"
                except Exception:
                    pass

        return context


class ComposerAIService:
    """
    Composer AI服务

    封装AI请求处理逻辑。
    """

    def __init__(self, llm_adapter=None, prompt_builder=None):
        """
        初始化AI服务

        Args:
            llm_adapter: LLM适配器实例
            prompt_builder: 提示词构建器实例
        """
        self.llm_adapter = llm_adapter
        self.prompt_builder = prompt_builder

    def process_task(self, task_type, selected_text, extra_param=""):
        """
        处理AI任务

        Args:
            task_type: 任务类型 (grammar/polish/expand/query)
            selected_text: 选中文本
            extra_param: 额外参数（如扩展类型或用户查询）

        Returns:
            str: AI处理结果

        Raises:
            Exception: 当处理失败时抛出异常
        """
        if not self.prompt_builder:
            raise ValueError("Prompt builder not initialized")

        if not self.llm_adapter:
            raise ValueError("LLM adapter not initialized")

        prompt = self.prompt_builder.build_prompt(
            task_type=task_type, selected_text=selected_text, user_query=extra_param
        )

        response = self.llm_adapter.invoke(prompt)
        return response
