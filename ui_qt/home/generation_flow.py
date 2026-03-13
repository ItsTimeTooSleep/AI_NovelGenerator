# -*- coding: utf-8 -*-
"""
生成流程管理器模块

================================================================================
模块功能概述
================================================================================
本模块负责管理小说生成的完整流程，协调各个生成步骤的执行，
处理生成任务的启动、进度跟踪和完成回调。

================================================================================
核心类
================================================================================
- GenerationFlowManager: 生成流程管理器

================================================================================
核心功能
================================================================================
- start_worker: 启动后台生成任务
- start_step1_generation: 启动Step1（架构生成）
- start_step2_generation: 启动Step2（蓝图生成）
- start_step3_generation: 启动Step3（章节草稿）
- start_step4_finalization: 启动Step4（定稿处理）

================================================================================
生成流程
================================================================================
Step1: 小说架构生成
    └── 核心种子 → 角色动力学 → 世界观 → 情节架构
Step2: 章节蓝图生成
    └── 根据架构生成章节目录
Step3: 章节草稿生成
    └── 基于蓝图生成正文内容
Step4: 章节定稿处理
    └── 更新摘要 → 更新角色状态 → 向量入库

================================================================================
设计决策
================================================================================
- 使用QThread后台执行，避免阻塞UI
- 支持流式输出，实时显示生成进度
- 集成进度管理和自动保存
- 支持断点续传，中断后可继续
- 使用 StateController 统一管理状态切换

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import time

from core.utils import read_file
from novel_generator import (
    Chapter_blueprint_generate,
    Novel_architecture_generate,
    build_chapter_prompt,
    finalize_chapter,
    generate_chapter_draft,
)
from ui_qt.utils.helpers import get_global_notify
from ui_qt.utils.notification_manager import NotificationType

from ..utils.generation_handlers import (
    GenerationWorker,
    PromptDialog,
    check_api_key_configured,
    check_project_loaded,
    get_llm_config,
    save_project_params,
)
from .states import ProjectState


class GenerationFlowManager:
    def __init__(
        self,
        home_tab,
        streaming_manager,
        autosave_manager,
        progress_manager,
        step_manager,
    ):
        self.home_tab = home_tab
        self.streaming_manager = streaming_manager
        self.autosave_manager = autosave_manager
        self.progress_manager = progress_manager
        self.step_manager = step_manager
        self.prompt_kwargs = None
        self._streaming_enabled = False

    def _is_streaming_enabled(self) -> bool:
        """
        检查是否启用流式传输

        Returns:
            bool: 是否启用流式传输
        """
        self.home_tab.loaded_config = self.home_tab.loaded_config or {}
        return self.home_tab.loaded_config.get("streaming_enabled", True)

    def start_worker(
        self,
        func,
        finished_slot=None,
        progress_slot=None,
        progress_with_data_slot=None,
        use_streaming=False,
        **kwargs,
    ):
        """
        启动后台工作线程

        Args:
            func: 要执行的函数
            finished_slot: 完成回调
            progress_slot: 进度回调
            progress_with_data_slot: 带额外数据的进度回调
            use_streaming: 是否使用流式传输
            **kwargs: 传递给函数的参数
        """
        self.home_tab.progressBar.setVisible(True)
        self.home_tab.progressBar.start()

        streaming_enabled = use_streaming and self._is_streaming_enabled()
        self._streaming_enabled = streaming_enabled

        stream_callback = None
        if streaming_enabled:
            stream_callback = self.streaming_manager.start_real_stream(
                self.home_tab.editor, self.home_tab.stopChapterStreamBtn
            )

        self.home_tab.worker = GenerationWorker(
            func,
            streaming_enabled=streaming_enabled,
            stream_callback=stream_callback,
            **kwargs,
        )
        if finished_slot:
            self.home_tab.worker.finished.connect(finished_slot)
        else:
            self.home_tab.worker.finished.connect(self.on_worker_finished)

        if progress_slot:
            self.home_tab.worker.progress.connect(progress_slot)

        if progress_with_data_slot:
            self.home_tab.worker.progress_with_data.connect(progress_with_data_slot)

        self.home_tab.worker.error.connect(self.on_worker_error)
        self.home_tab.worker.cancelled.connect(self.on_worker_cancelled)
        self.home_tab.worker.start()

    def on_worker_finished(self, result):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        if self._streaming_enabled:
            self.streaming_manager.finish_real_stream()
        elif isinstance(result, str) and result.strip():
            self.streaming_manager._start_stream(
                self.home_tab.editor, result, self.home_tab.stopChapterStreamBtn
            )

        chap_num = self.home_tab.currChapterSpin.value()
        if hasattr(self.home_tab, "project_status_manager"):
            word_count = 0
            if isinstance(result, str) and result.strip():
                word_count = len(result.strip())
            self.home_tab.project_status_manager.mark_draft_generated(
                chap_num, word_count
            )

        self.home_tab.state_controller.transition_to(ProjectState.STEP3_ACTIVE)
        self.home_tab.check_project_files()

        self.home_tab.log("✅ 操作完成")

    def on_worker_cancelled(self):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        self.home_tab.log("⏹ 生成已被用户取消")
        notify = get_global_notify()
        if notify:
            notify.warning("提示", "生成已被取消")

        if hasattr(self.home_tab, "stopStep1Btn"):
            self.home_tab.stopStep1Btn.hide()
        if hasattr(self.home_tab, "stopStep2Btn"):
            self.home_tab.stopStep2Btn.hide()
        if hasattr(self.home_tab, "stopChapterStreamBtn"):
            self.home_tab.stopChapterStreamBtn.hide()

        if (
            hasattr(self.home_tab, "step1ProgressContainer")
            and self.home_tab.step1ProgressContainer.isVisible()
        ):
            self.home_tab.state_controller.transition_to(ProjectState.STEP1_NOT_STARTED)

        if (
            hasattr(self.home_tab, "step2ProgressContainer")
            and self.home_tab.step2ProgressContainer.isVisible()
        ):
            self.home_tab.state_controller.transition_to(ProjectState.STEP2_NOT_STARTED)

        if hasattr(self.home_tab, "step3Btn"):
            self.home_tab.step3Btn.setEnabled(True)

        self.home_tab.check_project_files()

    def on_worker_error(self, error):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        if self._streaming_enabled:
            self.streaming_manager.finish_real_stream()

        if hasattr(self.home_tab, "stopChapterStreamBtn"):
            self.home_tab.stopChapterStreamBtn.hide()

        if hasattr(self.home_tab, "step3Btn"):
            self.home_tab.step3Btn.setEnabled(True)
            self.home_tab.step3Btn.setText("Step 3. 重新生成草稿")

        if hasattr(self.home_tab, "step4Btn"):
            self.home_tab.step4Btn.setEnabled(True)
            self.home_tab.step4Btn.setText("Step 4. 定稿章节")

        if (
            hasattr(self.home_tab, "step2ProgressContainer")
            and self.home_tab.step2ProgressContainer.isVisible()
        ):
            self.home_tab.state_controller.transition_to(ProjectState.STEP2_NOT_STARTED)

        self.home_tab.check_project_files()

        self.home_tab.log(f"❌ 错误: {error}")
        notify = get_global_notify()
        if notify:
            notify.error("错误", error)

    def on_generation_progress(self, step_name, status_msg, duration):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [{step_name}] {status_msg}"

        if duration > 0.1:
            msg += f" (耗时: {duration:.1f}s)"
        self.home_tab.log(msg)

        if "完成" in status_msg or "Done" in status_msg:
            notify = get_global_notify()
            if notify:
                notify.success(step_name, f"已完成 (耗时 {duration:.1f}s)")

    def on_step1(self):
        if self.home_tab.step1Btn.text() == "继续到Step 2":
            self.step_manager.go_to_step2_from_step1()
            return

        if not check_project_loaded(
            self.home_tab.current_project_path, self.home_tab.window()
        ):
            return

        if not check_api_key_configured(
            self.home_tab.loaded_config, "architecture_llm", self.home_tab.window()
        ):
            return

        save_project_params(self.home_tab)

        if hasattr(self.home_tab, "project_status_manager"):
            self.home_tab.project_status_manager.reset_step1()
            self.home_tab.project_status_manager.reset_step2()

        try:
            config = get_llm_config(self.home_tab.loaded_config, "architecture_llm")
        except Exception as e:
            notify = get_global_notify()
            if notify:
                notify.error("错误", str(e))
            return

        from core.tokens_manager import set_token_context

        set_token_context(
            step_name="第一步 · 生成小说架构",
            chapter_number=None,
            metadata={"step": "1", "type": "architecture"},
        )

        kwargs = {
            "interface_format": config["interface_format"],
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "llm_model": config["model_name"],
            "title": self.home_tab.current_project.get("name", "未命名"),
            "topic": self.home_tab.current_project.get("topic", "")
            or self.home_tab.current_project.get("description", ""),
            "genre": self.home_tab.current_project.get("genre", "玄幻"),
            "number_of_chapters": int(
                self.home_tab.current_project.get("total_chapters_plan", 100)
            ),
            "word_number": int(
                self.home_tab.current_project.get("words_per_chapter_plan", 3000)
            ),
            "filepath": self.home_tab.current_project_path,
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "timeout": config["timeout"],
            "user_guidance": self.home_tab.guidanceEdit.toPlainText(),
        }

        self.home_tab.log("开始生成小说架构...")

        partial_arch_path = os.path.join(
            self.home_tab.current_project_path, "partial_architecture.json"
        )
        if not os.path.exists(partial_arch_path):
            self.home_tab.step1TextEdit.clear()
            self.home_tab.step1TextEdit.hide()
            for step_widget in self.home_tab.step1ProgressWidgets:
                step_widget.reset()
            self.home_tab.step1ProgressContainer.update_line_state(-1, [])

        self.home_tab.step1ProgressContainer.show()

        self.home_tab.state_controller.transition_to(ProjectState.STEP1_IN_PROGRESS)

        self.start_worker(
            Novel_architecture_generate,
            finished_slot=self.on_architecture_generated,
            progress_slot=self.progress_manager.on_step1_progress,
            progress_with_data_slot=self._on_step1_progress_with_data,
            **kwargs,
        )

    def _on_step1_progress_with_data(
        self, step_name: str, status_msg: str, duration: float, extra_data: dict
    ):
        """
        处理Step 1的进度更新（带额外数据）
        用于处理书名生成等需要传递额外信息的步骤

        Args:
            step_name: 步骤名称
            status_msg: 状态信息
            duration: 耗时
            extra_data: 额外数据字典
        """
        if extra_data and "generated_title" in extra_data:
            generated_title = extra_data["generated_title"]
            self.home_tab.log(f"✨ 生成书名: {generated_title}")
            if self.home_tab.current_project:
                self.home_tab.current_project["name"] = generated_title
                from novel_generator.project_manager import ProjectManager

                pm = ProjectManager()
                pm.save_project_config(
                    self.home_tab.current_project_path,
                    self.home_tab.current_project,
                )
                if hasattr(self.home_tab, "bookTitleLabel"):
                    self.home_tab.bookTitleLabel.setText(generated_title)
        self.progress_manager.on_step1_progress(step_name, status_msg, duration)

    def on_architecture_generated(self, _result):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        self.home_tab.stopStep1Btn.hide()

        self.home_tab.step1ProgressContainer.hide()

        if not self.home_tab.current_project_path:
            self.home_tab.log("未检测到当前项目路径，无法加载架构文件。")
            return

        arch_file = os.path.join(
            self.home_tab.current_project_path, "Novel_architecture.txt"
        )
        if not os.path.exists(arch_file):
            self.home_tab.step1TextEdit.show()
            self.home_tab.step1TextEdit.setPlainText(
                "未找到 Novel_architecture.txt，生成可能失败，请检查日志。"
            )
            self.home_tab.log("❌ 未找到 Novel_architecture.txt")
            self.home_tab.check_project_files()
            return

        try:
            text = read_file(arch_file)
        except Exception as e:
            self.home_tab.step1TextEdit.show()
            self.home_tab.step1TextEdit.setPlainText(f"读取小说架构文件失败：{e}")
            self.home_tab.log(f"❌ 读取小说架构失败: {e}")
            self.home_tab.check_project_files()
            return

        if not text.strip():
            self.home_tab.step1TextEdit.show()
            self.home_tab.step1TextEdit.setPlainText("小说架构文件为空，请重试生成。")
            self.home_tab.log("❌ 小说架构文件内容为空")
            self.home_tab.check_project_files()
            return

        if hasattr(self.home_tab, "project_status_manager"):
            self.home_tab.project_status_manager.mark_step1_completed()

        self.home_tab.step1TextEdit.show()
        self.home_tab.log("✅ 小说架构生成完成")

        def on_stream_complete():
            self.home_tab.state_controller.transition_to(ProjectState.STEP1_COMPLETED)
            self.home_tab.check_project_files()

        self.streaming_manager._start_stream(
            self.home_tab.step1TextEdit,
            text,
            self.home_tab.stopStep1Btn,
            on_complete=on_stream_complete,
        )

    def on_step2(self):
        if not check_project_loaded(
            self.home_tab.current_project_path, self.home_tab.window()
        ):
            return

        if not check_api_key_configured(
            self.home_tab.loaded_config, "chapter_outline_llm", self.home_tab.window()
        ):
            return

        save_project_params(self.home_tab)

        try:
            config = get_llm_config(self.home_tab.loaded_config, "chapter_outline_llm")
        except Exception as e:
            notify = get_global_notify()
            if notify:
                notify.error("错误", str(e))
            return

        from core.tokens_manager import set_token_context

        set_token_context(
            step_name="第二步 · 生成章节目录",
            chapter_number=None,
            metadata={"step": "2", "type": "directory"},
        )

        kwargs = {
            "interface_format": config["interface_format"],
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "llm_model": config["model_name"],
            "number_of_chapters": int(
                self.home_tab.current_project.get("total_chapters_plan", 100)
            ),
            "filepath": self.home_tab.current_project_path,
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "timeout": config["timeout"],
            "user_guidance": self.home_tab.guidanceEdit.toPlainText(),
        }

        self.home_tab.log("开始生成目录...")
        self.home_tab.step2TextEdit.clear()
        self.home_tab.step2TextEdit.hide()
        for step_widget in self.home_tab.step2ProgressWidgets:
            step_widget.reset()
        self.home_tab.step2ProgressContainer.update_line_state(-1, [])
        self.home_tab.step2ProgressContainer.show()

        self.home_tab.state_controller.transition_to(ProjectState.STEP2_IN_PROGRESS)

        self.start_worker(
            Chapter_blueprint_generate,
            finished_slot=self.on_directory_generated,
            progress_slot=self.progress_manager.on_step2_progress,
            **kwargs,
        )

    def on_directory_generated(self, _result):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        self.home_tab.stopStep2Btn.hide()
        self.home_tab.step2ProgressContainer.hide()

        if not self.home_tab.current_project_path:
            self.home_tab.log("未检测到当前项目路径，无法加载目录文件。")
            return

        dir_file = os.path.join(
            self.home_tab.current_project_path, "Novel_directory.txt"
        )
        if not os.path.exists(dir_file):
            self.home_tab.step2TextEdit.show()
            self.home_tab.step2TextEdit.setPlainText(
                "未找到 Novel_directory.txt，生成可能失败，请检查日志。"
            )
            self.home_tab.stopStep2Btn.hide()
            self.home_tab.log("❌ 未找到 Novel_directory.txt")
            self.home_tab.check_project_files()
            return

        try:
            text = read_file(dir_file)
        except Exception as e:
            self.home_tab.step2TextEdit.show()
            self.home_tab.step2TextEdit.setPlainText(f"读取章节目录文件失败：{e}")
            self.home_tab.stopStep2Btn.hide()
            self.home_tab.log(f"❌ 读取章节目录失败: {e}")
            self.home_tab.check_project_files()
            return

        if not text.strip():
            self.home_tab.step2TextEdit.show()
            self.home_tab.step2TextEdit.setPlainText("章节目录文件为空，请重试生成。")
            self.home_tab.stopStep2Btn.hide()
            self.home_tab.log("❌ 章节目录文件内容为空")
            self.home_tab.check_project_files()
            return

        if hasattr(self.home_tab, "project_status_manager"):
            self.home_tab.project_status_manager.mark_step2_completed()

        self.home_tab.step2TextEdit.show()
        self.home_tab.log("✅ 章节目录生成完成")

        def on_stream_complete():
            self.home_tab.state_controller.transition_to(ProjectState.PROJECT_READY)
            self.home_tab.check_project_files()

        self.streaming_manager._start_stream(
            self.home_tab.step2TextEdit,
            text,
            self.home_tab.stopStep2Btn,
            on_complete=on_stream_complete,
        )

    def on_step3(self):
        if not check_project_loaded(
            self.home_tab.current_project_path, self.home_tab.window()
        ):
            return

        if not check_api_key_configured(
            self.home_tab.loaded_config, "prompt_draft_llm", self.home_tab.window()
        ):
            return

        save_project_params(self.home_tab)

        try:
            config = get_llm_config(self.home_tab.loaded_config, "prompt_draft_llm")
        except Exception as e:
            notify = get_global_notify()
            if notify:
                notify.error("错误", str(e))
            return

        from core.tokens_manager import set_token_context

        chap_num = self.home_tab.currChapterSpin.value()
        set_token_context(
            step_name="第三步 · 生成草稿",
            chapter_number=chap_num,
            metadata={"step": "3", "type": "draft", "chapter": chap_num},
        )

        if hasattr(self.home_tab, "project_status_manager"):
            self.home_tab.project_status_manager.mark_draft_regenerating(chap_num)

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

        self.prompt_kwargs = {
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "filepath": self.home_tab.current_project_path,
            "novel_number": chap_num,
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

        self.home_tab.step3Btn.setEnabled(False)
        self.home_tab.step3Btn.setText("正在生成...")
        self.home_tab.continueToStep4Btn.hide()

        self.home_tab.log("正在构建提示词...")
        self.start_worker(
            build_chapter_prompt,
            finished_slot=self.on_prompt_built,
            **self.prompt_kwargs,
        )

    def on_prompt_built(self, prompt_text):
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        dialog = PromptDialog(self.home_tab.window(), "确认提示词", prompt_text)
        if dialog.exec():
            final_prompt = dialog.get_prompt()
            self.home_tab.log("开始生成章节草稿...")

            gen_kwargs = self.prompt_kwargs.copy()
            gen_kwargs["custom_prompt_text"] = final_prompt

            self.start_worker(
                generate_chapter_draft,
                use_streaming=True,
                **gen_kwargs,
            )
        else:
            self.home_tab.log("❌ 取消生成")
            self.home_tab.step3Btn.setEnabled(True)
            self.home_tab.check_project_files()

    def on_step4(self):
        if not check_project_loaded(
            self.home_tab.current_project_path, self.home_tab.window()
        ):
            return

        if not check_api_key_configured(
            self.home_tab.loaded_config, "final_chapter_llm", self.home_tab.window()
        ):
            return

        save_project_params(self.home_tab)

        try:
            config = get_llm_config(self.home_tab.loaded_config, "final_chapter_llm")
        except Exception as e:
            notify = get_global_notify()
            if notify:
                notify.error("错误", str(e))
            return

        from core.tokens_manager import set_token_context

        chap_num = self.home_tab.currChapterSpin.value()
        set_token_context(
            step_name="第四步 · 定稿章节",
            chapter_number=chap_num,
            metadata={"step": "4", "type": "finalize", "chapter": chap_num},
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
            "novel_number": chap_num,
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

        self.home_tab.log(f"开始定稿第{chap_num}章...")
        self.home_tab.step4Btn.setEnabled(False)
        self.home_tab.step4Btn.setText("正在定稿...")
        self.start_worker(
            finalize_chapter, finished_slot=self.on_step4_finished, **kwargs
        )

    def on_step4_finished(self, _result):
        """
        Step FOUR完成后的回调函数
        该函数负责：
        1. 停止进度条
        2. 更新UI状态
        3. 标记章节已定稿
        4. 自动切换到下一章
        5. 回到Step 3界面
        """
        self.home_tab.progressBar.stop()
        self.home_tab.progressBar.setVisible(False)

        self.home_tab.step4Btn.setEnabled(True)
        self.home_tab.step4Btn.setText("Step 4. 定稿章节")

        current_chap = self.home_tab.currChapterSpin.value()

        if hasattr(self.home_tab, "project_status_manager"):
            self.home_tab.project_status_manager.mark_finalized(current_chap)

        next_chap = current_chap + 1

        self.home_tab.currChapterSpin.setValue(next_chap)

        self.step_manager.enter_step3_actions()

        self.home_tab.check_project_files()

        self.home_tab.log(f"✅ 第{current_chap}章定稿完成，已切换到第{next_chap}章")
