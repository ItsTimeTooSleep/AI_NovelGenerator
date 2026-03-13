# -*- coding: utf-8 -*-
"""
自动生成功能模块
==================

提供小说章节自动批量生成功能：
- 配置对话框：设置生成章节数
- 进度页面：显示生成进度
- 工作线程：自动循环执行步骤3-4
"""

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    IconWidget,
    MessageBoxBase,
    ProgressBar,
    PushButton,
    ScrollArea,
    SpinBox,
    StrongBodyLabel,
    SubtitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

from core.tokens_manager import set_token_context
from novel_generator import (
    build_chapter_prompt,
    finalize_chapter,
    generate_chapter_draft,
)

from .dialog_sizer import DialogSizer
from .generation_handlers import get_llm_config, save_project_params


class AutoGenerateConfigDialog(MessageBoxBase):
    """
    自动生成配置对话框
    支持尺寸自适应。

    Args:
        current_chapter: 当前已完成的章节数
        total_plan: 计划总章节数
        parent: 父窗口
    """

    def __init__(self, current_chapter: int, total_plan: int, parent=None):
        super().__init__(parent)
        self.current_chapter = current_chapter
        self.total_plan = total_plan

        self.titleLabel = SubtitleLabel("自动生成配置", self)
        self.viewLayout.addWidget(self.titleLabel)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(16)

        self.startInfo = CardWidget(self)
        self.startInfo.setContentsMargins(16, 16, 16, 16)
        startLayout = QVBoxLayout(self.startInfo)
        startLayout.setSpacing(8)

        startTitle = StrongBodyLabel("📖 生成起始位置", self.startInfo)
        startLayout.addWidget(startTitle)

        self.startChapterLabel = BodyLabel(
            f"从第 {current_chapter + 1} 章开始生成", self.startInfo
        )
        self.startChapterLabel.setWordWrap(True)
        startLayout.addWidget(self.startChapterLabel)

        self.layout.addWidget(self.startInfo)

        self.chaptersCard = CardWidget(self)
        self.chaptersCard.setContentsMargins(16, 16, 16, 16)
        chaptersLayout = QVBoxLayout(self.chaptersCard)
        chaptersLayout.setSpacing(12)

        chaptersTitle = StrongBodyLabel("📊 生成章节数量", self.chaptersCard)
        chaptersLayout.addWidget(chaptersTitle)

        self.generateAllCheck = QCheckBox("生成全部剩余章节", self.chaptersCard)
        self.generateAllCheck.setChecked(True)
        self.generateAllCheck.stateChanged.connect(self.on_generate_all_changed)
        chaptersLayout.addWidget(self.generateAllCheck)

        self.customLayout = QHBoxLayout()
        self.customLayout.setSpacing(12)

        self.customLabel = BodyLabel("自定义生成数量：", self.chaptersCard)
        self.customLayout.addWidget(self.customLabel)

        self.chapterCountSpin = SpinBox(self.chaptersCard)
        remaining = max(1, total_plan - current_chapter)
        self.chapterCountSpin.setRange(1, remaining)
        self.chapterCountSpin.setValue(remaining)
        self.chapterCountSpin.setEnabled(False)
        self.customLayout.addWidget(self.chapterCountSpin)

        chaptersLayout.addLayout(self.customLayout)

        self.remainingLabel = CaptionLabel(
            f"剩余未生成章节数：{remaining} 章", self.chaptersCard
        )
        self.remainingLabel.setWordWrap(True)
        chaptersLayout.addWidget(self.remainingLabel)

        self.layout.addWidget(self.chaptersCard)

        self.hintCard = CardWidget(self)
        self.hintCard.setContentsMargins(16, 16, 16, 16)
        hintLayout = QVBoxLayout(self.hintCard)

        hintTitle = StrongBodyLabel("💡 说明", self.hintCard)
        hintLayout.addWidget(hintTitle)

        hintText = BodyLabel(
            "自动生成将循环执行以下流程：\n"
            "1. Step 3 - 生成章节草稿\n"
            "2. Step 4 - 定稿章节\n"
            "3. 自动切换到下一章，重复上述步骤",
            self.hintCard,
        )
        hintText.setWordWrap(True)
        hintLayout.addWidget(hintText)

        self.layout.addWidget(self.hintCard)

        self.viewLayout.addWidget(self.container)

        self.yesButton.setText("开始生成")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.50,
            min_width=450,
            min_height=350,
        )
        sizer.apply_to_widget(self.widget, parent)

    def on_generate_all_changed(self, state):
        """
        全部生成选项变化时的处理

        Args:
            state: 复选框状态
        """
        is_all = state == Qt.Checked
        self.chapterCountSpin.setEnabled(not is_all)
        if is_all:
            remaining = max(1, self.total_plan - self.current_chapter)
            self.chapterCountSpin.setValue(remaining)

    def get_config(self) -> dict:
        """
        获取配置信息

        Returns:
            dict: 包含start_chapter和chapter_count的字典
        """
        return {
            "start_chapter": self.current_chapter + 1,
            "chapter_count": self.chapterCountSpin.value(),
        }


class AutoGenerateProgressPage(QWidget):
    """
    自动生成进度页面

    Args:
        parent: 父窗口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autoGenerateProgressPage")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # 标题区域
        self.titleRow = QHBoxLayout()
        self.titleRow.setSpacing(12)

        self.iconWidget = IconWidget(FIF.ROBOT, self)
        self.iconWidget.setFixedSize(40, 40)
        self.titleRow.addWidget(self.iconWidget)

        self.titleLabel = SubtitleLabel("自动生成中...", self)
        self.titleRow.addWidget(self.titleLabel)
        self.titleRow.addStretch(1)

        self.layout.addLayout(self.titleRow)

        # 当前状态卡片
        self.statusCard = CardWidget(self)
        self.statusCard.setContentsMargins(20, 20, 20, 20)
        self.statusLayout = QVBoxLayout(self.statusCard)
        self.statusLayout.setSpacing(12)

        self.currentChapterLabel = StrongBodyLabel(
            "正在生成第 0 章 / 共 0 章", self.statusCard
        )
        self.statusLayout.addWidget(self.currentChapterLabel)

        self.stepLabel = BodyLabel("准备开始...", self.statusCard)
        self.stepLabel.setWordWrap(True)
        self.statusLayout.addWidget(self.stepLabel)

        self.layout.addWidget(self.statusCard)

        # 整体进度条
        self.overallProgressCard = CardWidget(self)
        self.overallProgressCard.setContentsMargins(20, 20, 20, 20)
        self.overallProgressLayout = QVBoxLayout(self.overallProgressCard)
        self.overallProgressLayout.setSpacing(8)

        self.overallProgressLabel = BodyLabel("整体进度：0%", self.overallProgressCard)
        self.overallProgressLayout.addWidget(self.overallProgressLabel)

        self.overallProgressBar = ProgressBar(self.overallProgressCard)
        self.overallProgressBar.setMinimum(0)
        self.overallProgressBar.setMaximum(100)
        self.overallProgressBar.setValue(0)
        self.overallProgressLayout.addWidget(self.overallProgressBar)

        self.layout.addWidget(self.overallProgressCard)

        # 当前步骤进度条
        self.currentStepCard = CardWidget(self)
        self.currentStepCard.setContentsMargins(20, 20, 20, 20)
        self.currentStepLayout = QVBoxLayout(self.currentStepCard)
        self.currentStepLayout.setSpacing(8)

        self.currentStepProgressLabel = BodyLabel("当前步骤进度", self.currentStepCard)
        self.currentStepLayout.addWidget(self.currentStepProgressLabel)

        self.currentStepProgressBar = ProgressBar(self.currentStepCard)
        self.currentStepProgressBar.setMinimum(0)
        self.currentStepProgressBar.setMaximum(0)
        self.currentStepLayout.addWidget(self.currentStepProgressBar)

        self.layout.addWidget(self.currentStepCard)

        # 已完成章节列表
        self.completedCard = CardWidget(self)
        self.completedCard.setContentsMargins(20, 20, 20, 20)
        self.completedLayout = QVBoxLayout(self.completedCard)
        self.completedLayout.setSpacing(8)

        self.completedTitle = StrongBodyLabel("已完成章节", self.completedCard)
        self.completedLayout.addWidget(self.completedTitle)

        self.completedScroll = ScrollArea(self.completedCard)
        self.completedScroll.setWidgetResizable(True)
        self.completedScroll.setMinimumHeight(120)

        self.completedListWidget = QWidget()
        self.completedListLayout = QVBoxLayout(self.completedListWidget)
        self.completedListLayout.setSpacing(4)
        self.completedListLayout.addStretch(1)

        self.completedScroll.setWidget(self.completedListWidget)
        self.completedLayout.addWidget(self.completedScroll)

        self.layout.addWidget(self.completedCard)

        # 按钮区域
        self.buttonRow = QHBoxLayout()
        self.buttonRow.addStretch(1)

        self.stopButton = PushButton(FIF.CANCEL, "停止生成", self)
        self.stopButton.setMinimumWidth(150)
        self.buttonRow.addWidget(self.stopButton)

        self.buttonRow.addStretch(1)
        self.layout.addLayout(self.buttonRow)

        self.layout.addStretch(1)

        # 内部状态
        self.completed_chapters = []
        self.total_chapters = 0
        self.current_chapter = 0

    def reset(self, total_chapters: int, start_chapter: int):
        """
        重置进度显示

        Args:
            total_chapters: 总章节数
            start_chapter: 起始章节
        """
        self.total_chapters = total_chapters
        self.current_chapter = start_chapter
        self.completed_chapters = []

        # 清空已完成列表
        while self.completedListLayout.count() > 1:
            item = self.completedListLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.titleLabel.setText("自动生成中...")
        self.currentChapterLabel.setText(
            f"正在生成第 {start_chapter} 章 / 共 {total_chapters} 章"
        )
        self.stepLabel.setText("准备开始...")
        self.overallProgressBar.setValue(0)
        self.overallProgressLabel.setText("整体进度：0%")
        self.currentStepProgressBar.setMaximum(0)

    def update_chapter(self, chapter_num: int):
        """
        更新当前章节

        Args:
            chapter_num: 章节号
        """
        self.current_chapter = chapter_num
        self.currentChapterLabel.setText(
            f"正在生成第 {chapter_num} 章 / 共 {self.total_chapters} 章"
        )

    def update_step(self, step_name: str):
        """
        更新当前步骤

        Args:
            step_name: 步骤名称
        """
        self.stepLabel.setText(f"当前步骤：{step_name}")
        self.currentStepProgressBar.setMaximum(0)

    def update_overall_progress(self, current: int, total: int):
        """
        更新整体进度

        Args:
            current: 当前完成数
            total: 总数
        """
        progress = int((current / total) * 100) if total > 0 else 0
        self.overallProgressBar.setValue(progress)
        self.overallProgressLabel.setText(f"整体进度：{progress}% ({current}/{total})")

    def add_completed_chapter(self, chapter_num: int):
        """
        添加已完成的章节

        Args:
            chapter_num: 章节号
        """
        self.completed_chapters.append(chapter_num)

        chapter_label = BodyLabel(
            f"✅ 第 {chapter_num} 章 已完成", self.completedListWidget
        )
        self.completedListLayout.insertWidget(
            self.completedListLayout.count() - 1, chapter_label
        )

        self.update_overall_progress(len(self.completed_chapters), self.total_chapters)

    def set_finished(self, success: bool):
        """
        设置生成完成状态

        Args:
            success: 是否成功
        """
        if success:
            self.titleLabel.setText("自动生成完成！")
            self.stepLabel.setText("所有章节已生成完毕")
        else:
            self.titleLabel.setText("自动生成已停止")
            self.stepLabel.setText("生成过程已中断")

        self.stopButton.setEnabled(False)
        self.currentStepProgressBar.setMaximum(100)
        self.currentStepProgressBar.setValue(100)


class AutoGenerateWorker(QThread):
    """
    自动生成工作线程

    Args:
        home_tab: HomeTab实例
        start_chapter: 起始章节
        chapter_count: 生成章节数
    """

    chapter_started = pyqtSignal(int)
    step_changed = pyqtSignal(str)
    chapter_completed = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, home_tab, start_chapter: int, chapter_count: int):
        super().__init__()
        self.home_tab = home_tab
        self.start_chapter = start_chapter
        self.chapter_count = chapter_count
        self._is_cancelled = False

    def cancel(self):
        """取消生成"""
        self._is_cancelled = True

    def run(self):
        """执行自动生成流程"""
        try:
            for i in range(self.chapter_count):
                if self._is_cancelled:
                    self.finished.emit(False)
                    return

                chapter_num = self.start_chapter + i
                self.chapter_started.emit(chapter_num)

                # Step 3: 生成草稿
                if not self._generate_draft(chapter_num):
                    self.finished.emit(False)
                    return

                if self._is_cancelled:
                    self.finished.emit(False)
                    return

                # Step 4: 定稿章节
                if not self._finalize_chapter(chapter_num):
                    self.finished.emit(False)
                    return

                self.chapter_completed.emit(chapter_num)

                # 更新当前章节
                self.home_tab.currChapterSpin.setValue(chapter_num + 1)
                save_project_params(self.home_tab)

            self.finished.emit(True)

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.error_occurred.emit(str(e))
            self.finished.emit(False)

    def _generate_draft(self, chapter_num: int) -> bool:
        """
        执行Step 3 - 生成草稿

        Args:
            chapter_num: 章节号

        Returns:
            bool: 是否成功
        """
        self.step_changed.emit("Step 3 - 构建提示词")

        try:
            config = get_llm_config(self.home_tab.loaded_config, "prompt_draft_llm")
        except Exception as e:
            self.error_occurred.emit(f"获取LLM配置失败: {e}")
            return False

        set_token_context(
            step_name="第三步 · 生成草稿",
            chapter_number=chapter_num,
            metadata={"step": "3", "type": "draft", "chapter": chapter_num},
        )

        choose_configs = self.home_tab.loaded_config.get("choose_configs", {})
        emb_config_name = choose_configs.get("embedding_model", "")

        if emb_config_name == "无" or not emb_config_name:
            emb_conf = {
                "interface_format": "",
                "api_key": "",
                "base_url": "",
                "model_name": "",
                "retrieval_k": 4,
            }
        else:
            emb_conf = self.home_tab.loaded_config.get("embedding_configs", {}).get(
                emb_config_name, {}
            )

        user_guidance = (
            self.home_tab.guidanceEdit.toPlainText()
            if hasattr(self.home_tab, "guidanceEdit")
            else ""
        )
        characters_involved = (
            self.home_tab.charactersInvolvedEdit.toPlainText()
            if hasattr(self.home_tab, "charactersInvolvedEdit")
            else ""
        )
        key_items = (
            self.home_tab.keyItemsEdit.toPlainText()
            if hasattr(self.home_tab, "keyItemsEdit")
            else ""
        )
        scene_location = (
            self.home_tab.sceneLocationEdit.toPlainText()
            if hasattr(self.home_tab, "sceneLocationEdit")
            else ""
        )
        time_constraint = (
            self.home_tab.timeConstraintEdit.toPlainText()
            if hasattr(self.home_tab, "timeConstraintEdit")
            else ""
        )

        prompt_kwargs = {
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "filepath": self.home_tab.current_project_path,
            "novel_number": chapter_num,
            "word_number": int(
                self.home_tab.current_project.get("words_per_chapter_plan", 3000)
            ),
            "temperature": config["temperature"],
            "user_guidance": user_guidance,
            "characters_involved": characters_involved,
            "key_items": key_items,
            "scene_location": scene_location,
            "time_constraint": time_constraint,
            "embedding_api_key": emb_conf.get("api_key", ""),
            "embedding_url": emb_conf.get("base_url", ""),
            "embedding_interface_format": emb_conf.get("interface_format", ""),
            "embedding_model_name": emb_conf.get("model_name", ""),
            "embedding_retrieval_k": int(emb_conf.get("retrieval_k", 4)),
            "interface_format": config["interface_format"],
            "max_tokens": config["max_tokens"],
            "timeout": config["timeout"],
        }

        if self._is_cancelled:
            return False

        self.step_changed.emit("Step 3 - 生成草稿")
        try:
            prompt_text = build_chapter_prompt(**prompt_kwargs)

            if self._is_cancelled:
                return False

            gen_kwargs = prompt_kwargs.copy()
            gen_kwargs["custom_prompt_text"] = prompt_text

            generate_chapter_draft(**gen_kwargs)
            return True

        except Exception as e:
            self.error_occurred.emit(f"生成草稿失败: {e}")
            return False

    def _finalize_chapter(self, chapter_num: int) -> bool:
        """
        执行Step 4 - 定稿章节

        Args:
            chapter_num: 章节号

        Returns:
            bool: 是否成功
        """
        self.step_changed.emit("Step 4 - 定稿章节")

        try:
            config = get_llm_config(self.home_tab.loaded_config, "final_chapter_llm")
        except Exception as e:
            self.error_occurred.emit(f"获取LLM配置失败: {e}")
            return False

        set_token_context(
            step_name="第四步 · 定稿章节",
            chapter_number=chapter_num,
            metadata={"step": "4", "type": "finalize", "chapter": chapter_num},
        )

        choose_configs = self.home_tab.loaded_config.get("choose_configs", {})
        emb_config_name = choose_configs.get("embedding_model", "")

        if emb_config_name == "无" or not emb_config_name:
            emb_conf = {
                "interface_format": "",
                "api_key": "",
                "base_url": "",
                "model_name": "",
                "retrieval_k": 4,
            }
        else:
            emb_conf = self.home_tab.loaded_config.get("embedding_configs", {}).get(
                emb_config_name, {}
            )

        kwargs = {
            "novel_number": chapter_num,
            "word_number": int(
                self.home_tab.current_project.get("words_per_chapter_plan", 3000)
            ),
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "temperature": config["temperature"],
            "filepath": self.home_tab.current_project_path,
            "embedding_api_key": emb_conf.get("api_key", ""),
            "embedding_url": emb_conf.get("base_url", ""),
            "embedding_interface_format": emb_conf.get("interface_format", ""),
            "embedding_model_name": emb_conf.get("model_name", ""),
            "interface_format": config["interface_format"],
            "max_tokens": config["max_tokens"],
            "timeout": config["timeout"],
        }

        try:
            finalize_chapter(**kwargs)
            return True
        except Exception as e:
            self.error_occurred.emit(f"定稿章节失败: {e}")
            return False
