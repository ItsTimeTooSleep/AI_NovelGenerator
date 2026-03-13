# ui_qt/generation_handlers.py
# -*- coding: utf-8 -*-
"""
业务逻辑层：集中处理所有生成相关业务逻辑
参考 ui/generation_handlers.py 的结构设计
"""

import inspect
import os
import tempfile
import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QWidget
from qfluentwidgets import (
    MessageBox,
    MessageBoxBase,
    SubtitleLabel,
    TextEdit,
)

from core.consistency_checker import check_consistency
from core.utils import read_file
from novel_generator import clear_vector_store, import_knowledge_file
from novel_generator.project_manager import ProjectManager
from ui_qt.utils.helpers import get_global_notify
from ui_qt.utils.notification_manager import NotificationType


class GenerationWorker(QThread):
    """
    异步生成工作线程

    Args:
        func: 要执行的生成函数
        streaming_enabled: 是否启用流式传输
        stream_callback: 流式回调函数（在主线程中调用）
        **kwargs: 传递给函数的参数
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, str, float)
    progress_with_data = pyqtSignal(str, str, float, dict)
    cancelled = pyqtSignal()
    stream_chunk = pyqtSignal(str)

    def __init__(
        self, func, streaming_enabled: bool = False, stream_callback=None, **kwargs
    ):
        super().__init__()
        self.func = func
        self.kwargs = kwargs
        self._is_cancelled = False
        self._streaming_enabled = streaming_enabled
        self._stream_callback = stream_callback

        if stream_callback:
            self.stream_chunk.connect(stream_callback)

    def cancel(self):
        """
        取消任务执行
        """
        self._is_cancelled = True

    def get_stream_callback(self):
        """
        获取流式回调函数，用于在生成函数中发送流式数据

        Returns:
            callable: 流式回调函数
        """

        def callback(chunk: str):
            if not self._is_cancelled:
                self.stream_chunk.emit(chunk)

        return callback

    def run(self):
        """执行生成任务"""
        try:
            if self._is_cancelled:
                self.cancelled.emit()
                return

            start_time = time.time()

            if self._streaming_enabled:
                self.kwargs["_stream_callback"] = self.get_stream_callback()

            result = self.func(**self.kwargs)

            if inspect.isgenerator(result):
                for item in result:
                    if self._is_cancelled:
                        self.cancelled.emit()
                        return
                    if isinstance(item, tuple):
                        current_time = time.time()
                        duration = current_time - start_time
                        start_time = current_time
                        if len(item) == 5:
                            (
                                step_index,
                                total_steps,
                                step_name,
                                status_msg,
                                extra_data,
                            ) = item
                            if extra_data:
                                self.progress_with_data.emit(
                                    step_name, status_msg, duration, extra_data
                                )
                            else:
                                self.progress.emit(step_name, status_msg, duration)
                        elif len(item) == 4:
                            self.progress.emit(item[2], item[3], duration)
                        elif len(item) == 3:
                            self.progress.emit(item[0], item[1], item[2])
                if not self._is_cancelled:
                    self.finished.emit(True)
            else:
                if self._is_cancelled:
                    self.cancelled.emit()
                    return
                self.finished.emit(result)
        except Exception as e:
            if self._is_cancelled:
                self.cancelled.emit()
                return
            import traceback

            traceback.print_exc()
            self.error.emit(str(e))


class PromptDialog(MessageBoxBase):
    """
    用于确认章节生成提示词的弹窗

    Args:
        parent: 父窗口
        title: 弹窗标题
        content: 提示词内容
    """

    def __init__(self, parent=None, title: str = "提示词确认", content: str = ""):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title, self)
        self.textEdit = TextEdit(self)
        self.textEdit.setPlainText(content)
        self.textEdit.setMinimumHeight(300)
        self.textEdit.setMinimumWidth(500)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("确认生成")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(600)

    def get_prompt(self) -> str:
        """
        获取用户编辑后的提示词

        Returns:
            str: 提示词内容
        """
        return self.textEdit.toPlainText()


class ProjectDetailsDialog(MessageBoxBase):
    """
    项目属性编辑弹窗

    Args:
        project_data: 项目数据字典
        parent: 父窗口
    """

    def __init__(self, project_data: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.project_data = project_data

        self.titleLabel = SubtitleLabel("项目详情", self)
        self.viewLayout.addWidget(self.titleLabel)

        from ..widgets.project_edit_form import ProjectEditForm

        self.form = ProjectEditForm(project_data, self)
        self.viewLayout.addWidget(self.form)

        self.yesButton.setText("保存修改")
        self.cancelButton.setText("关闭")

        self.widget.setMinimumWidth(500)

    def get_data(self) -> dict:
        """
        获取编辑后的项目数据

        Returns:
            dict: 项目数据字典
        """
        return self.form.get_data()


def check_api_key_configured(loaded_config, config_key_name, window):
    """
    检查 API Key 是否已配置

    Args:
        loaded_config: 已加载的配置字典
        config_key_name: 配置键名
        window: 窗口对象，用于显示通知

    Returns:
        bool: API Key 是否已配置
    """
    notify = get_global_notify()
    try:
        config = get_llm_config(loaded_config, config_key_name)
        api_key = config.get("api_key", "")
        if not api_key or api_key.strip() == "":
            if notify:
                notify.warning("提示", "请先在设置中配置 API Key")
            return False
        return True
    except Exception:
        if notify:
            notify.warning("提示", "请先在设置中配置 LLM 模型和 API Key")
        return False


def get_llm_config(loaded_config, config_key_name):
    """
    获取 LLM 配置

    Args:
        loaded_config: 已加载的配置字典
        config_key_name: 配置键名

    Returns:
        dict: LLM 配置

    Raises:
        ValueError: 未配置 LLM
    """
    choose_configs = loaded_config.get("choose_configs", {})
    config_name = choose_configs.get(config_key_name)
    if not config_name:
        llm_configs = loaded_config.get("llm_configs", {})
        if llm_configs:
            config_name = next(iter(llm_configs))
        else:
            raise ValueError("未配置LLM，请先去配置页添加模型")

    config = loaded_config["llm_configs"][config_name]
    return config


def check_project_loaded(current_project_path, window):
    """
    检查项目是否已加载

    Args:
        current_project_path: 当前项目路径
        window: 窗口对象

    Returns:
        bool: 项目是否已加载
    """
    notify = get_global_notify()
    if not current_project_path:
        if notify:
            notify.warning("警告", "请先在主页选择一个项目")
        return False
    return True


def save_project_params(home_tab):
    """
    保存项目参数

    Args:
        home_tab: HomeTab对象，包含所有需要保存的项目参数
    """
    if not home_tab.current_project:
        return

    current_project = home_tab.current_project
    current_project_path = home_tab.current_project_path

    guidance_text = ""
    if hasattr(home_tab, "guidanceEdit"):
        guidance_text = home_tab.guidanceEdit.toPlainText()

    characters_involved = ""
    if hasattr(home_tab, "charactersInvolvedEdit"):
        characters_involved = home_tab.charactersInvolvedEdit.toPlainText()

    key_items = ""
    if hasattr(home_tab, "keyItemsEdit"):
        key_items = home_tab.keyItemsEdit.toPlainText()

    scene_location = ""
    if hasattr(home_tab, "sceneLocationEdit"):
        scene_location = home_tab.sceneLocationEdit.toPlainText()

    time_constraint = ""
    if hasattr(home_tab, "timeConstraintEdit"):
        time_constraint = home_tab.timeConstraintEdit.toPlainText()

    curr_chapter = 1
    if hasattr(home_tab, "currChapterSpin"):
        curr_chapter = home_tab.currChapterSpin.value()

    entered_full_layout = getattr(home_tab, "_entered_full_layout", False)

    current_project["user_guidance"] = guidance_text
    current_project["characters_involved"] = characters_involved
    current_project["key_items"] = key_items
    current_project["scene_location"] = scene_location
    current_project["time_constraint"] = time_constraint
    current_project["current_chapter"] = curr_chapter
    current_project["entered_full_layout"] = entered_full_layout

    pm = ProjectManager()
    try:
        pm.save_project_config(current_project_path, current_project)
        if hasattr(home_tab, "log"):
            home_tab.log("配置已自动保存")
    except Exception as e:
        if hasattr(home_tab, "log"):
            home_tab.log(f"保存配置失败: {e}")


def do_consistency_check(
    loaded_config, current_project_path, curr_chapter, log_func, window
):
    """
    一致性审校

    Args:
        loaded_config: 已加载的配置
        current_project_path: 当前项目路径
        curr_chapter: 当前章节
        log_func: 日志函数
        window: 窗口对象
    """
    notify = get_global_notify()
    if not check_project_loaded(current_project_path, window):
        return

    if not check_api_key_configured(loaded_config, "consistency_review_llm", window):
        return

    try:
        config = get_llm_config(loaded_config, "consistency_review_llm")
    except Exception as e:
        if notify:
            notify.error("错误", str(e))
        return

    filepath = current_project_path
    chap_file = os.path.join(filepath, "chapters", f"chapter_{curr_chapter}.txt")
    if not os.path.exists(chap_file):
        if notify:
            notify.warning("提示", "当前章节文件不存在，无法审校。")
        return

    chapter_text = read_file(chap_file)
    if not chapter_text.strip():
        if notify:
            notify.warning("提示", "当前章节文件为空，无法审校。")
        return

    def task():
        try:
            log_func("开始一致性审校...")
            result = check_consistency(
                novel_setting="",
                character_state=read_file(
                    os.path.join(filepath, "character_state.txt")
                ),
                global_summary=read_file(os.path.join(filepath, "global_summary.txt")),
                chapter_text=chapter_text,
                api_key=config["api_key"],
                base_url=config["base_url"],
                model_name=config["model_name"],
                temperature=config["temperature"],
                interface_format=config["interface_format"],
                max_tokens=config["max_tokens"],
                timeout=config["timeout"],
                plot_arcs="",
            )
            log_func("审校结果：")
            log_func(result)
        except Exception as e:
            log_func(f"❌ 审校出错: {e}")
            if notify:
                notify.show_from_thread(NotificationType.ERROR, "错误", str(e))

    threading.Thread(target=task, daemon=True).start()


def import_knowledge_handler(loaded_config, current_project_path, log_func, window):
    """
    导入知识库

    Args:
        loaded_config: 已加载的配置
        current_project_path: 当前项目路径
        log_func: 日志函数
        window: 窗口对象
    """
    notify = get_global_notify()
    if not check_project_loaded(current_project_path, window):
        return

    selected_file, _ = QFileDialog.getOpenFileName(
        window, "选择要导入的知识库文件", "", "Text Files (*.txt);;All Files (*.*)"
    )
    if not selected_file:
        return

    emb_fmt = loaded_config.get("last_embedding_interface_format", "OpenAI")
    emb_conf = loaded_config.get("embedding_configs", {}).get(emb_fmt, {})
    if not emb_conf:
        if notify:
            notify.warning("提示", "请先在全局配置中配置 Embedding 模型。")
        return

    emb_api_key = emb_conf.get("api_key", "")
    if not emb_api_key or emb_api_key.strip() == "":
        if notify:
            notify.warning("提示", "请先在设置中配置 Embedding 模型的 API Key")
        return

    def task():
        try:
            encodings = ["utf-8", "gbk", "gb2312", "ansi"]
            content = None
            for enc in encodings:
                try:
                    with open(selected_file, "r", encoding=enc) as f:
                        content = f.read()
                        break
                except (UnicodeDecodeError, Exception):
                    continue
            if content is None:
                raise Exception("无法以任何已知编码读取文件")

            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".txt"
            ) as tmp:
                tmp.write(content)
                temp_path = tmp.name

            try:
                log_func(f"开始导入知识库文件: {selected_file}")
                import_knowledge_file(
                    embedding_api_key=emb_conf.get("api_key", ""),
                    embedding_url=emb_conf.get("base_url", ""),
                    embedding_interface_format=emb_conf.get(
                        "interface_format", "OpenAI"
                    ),
                    embedding_model_name=emb_conf.get("model_name", ""),
                    file_path=temp_path,
                    filepath=current_project_path,
                )
                log_func("✅ 知识库文件导入完成。")
                if notify:
                    notify.show_from_thread(
                        NotificationType.SUCCESS, "成功", "知识库导入完成"
                    )
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        except Exception as e:
            log_func(f"❌ 导入知识库出错: {e}")
            if notify:
                notify.show_from_thread(NotificationType.ERROR, "错误", str(e))

    threading.Thread(target=task, daemon=True).start()


def clear_vectorstore_handler(current_project_path, log_func, window):
    """
    清空向量库

    Args:
        current_project_path: 当前项目路径
        log_func: 日志函数
        window: 窗口对象
    """
    notify = get_global_notify()
    if not check_project_loaded(current_project_path, window):
        return

    first = MessageBox("警告", "确定要清空本地向量库吗？此操作不可恢复！", window)
    if first.exec():
        second = MessageBox(
            "二次确认", "你确定真的要删除所有向量数据吗？此操作不可恢复！", window
        )
        if second.exec():
            if clear_vector_store(current_project_path):
                log_func("已清空向量库。")
                if notify:
                    notify.success("成功", "向量库已清空")
            else:
                log_func(
                    f"未能清空向量库，请关闭程序后手动删除 {current_project_path} 下的 vectorstore 文件夹。"
                )
                if notify:
                    notify.warning("提示", "清空失败，请手动删除 vectorstore 文件夹")


def show_plot_arcs_ui(current_project_path, window):
    """
    显示剧情要点

    Args:
        current_project_path: 当前项目路径
        window: 窗口对象
    """
    notify = get_global_notify()
    if not check_project_loaded(current_project_path, window):
        return

    plot_arcs_file = os.path.join(current_project_path, "plot_arcs.txt")
    if not os.path.exists(plot_arcs_file):
        if notify:
            notify.info("剧情要点", "当前还未生成任何剧情要点或冲突记录。")
        return

    arcs_text = read_file(plot_arcs_file).strip()
    if not arcs_text:
        arcs_text = "当前没有记录的剧情要点或冲突。"

    dialog = MessageBoxBase(window)
    dialog.titleLabel = SubtitleLabel("剧情要点 / 未解决冲突", dialog)
    dialog.textDisplay = TextEdit(dialog)
    dialog.textDisplay.setPlainText(arcs_text)
    dialog.textDisplay.setReadOnly(True)
    dialog.textDisplay.setMinimumHeight(320)
    dialog.textDisplay.setMinimumWidth(500)
    dialog.viewLayout.addWidget(dialog.titleLabel)
    dialog.viewLayout.addWidget(dialog.textDisplay)
    dialog.yesButton.setText("关闭")
    dialog.cancelButton.setVisible(False)
    dialog.widget.setMinimumWidth(560)
    dialog.exec()


__all__ = [
    "GenerationWorker",
    "PromptDialog",
    "ProjectDetailsDialog",
    "get_llm_config",
    "check_api_key_configured",
    "check_project_loaded",
    "save_project_params",
    "do_consistency_check",
    "import_knowledge_handler",
    "clear_vectorstore_handler",
    "show_plot_arcs_ui",
]
