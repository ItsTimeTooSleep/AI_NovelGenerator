# -*- coding: utf-8 -*-
"""
AI Novel Generator - 写作编辑模块
====================================

本模块实现了小说写作编辑界面，负责：
- 章节列表的显示与管理
- 章节内容的编辑
- 章节的上一章/下一章导航
- 章节内容的自动保存

主要组件：
- WritingTab: 写作编辑主界面
"""

from datetime import datetime
import glob
import os
import threading

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QShortcut,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    PlainTextEdit,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
)
from qfluentwidgets import FluentIcon as FIF

from core.config_manager import load_config
from core.utils import read_file, save_string_to_txt
from ui_qt.utils.editor_toolkit import EditorToolkit
from ui_qt.utils.notification_manager import NotificationManager, NotificationType

from ..utils.styles import Styles
from ..widgets.placeholder_widget import EmptyState, PlaceholderWidget


class WritingTab(QWidget):
    """
    写作编辑主界面

    采用左右分栏布局：
    - 左侧：章节列表
    - 右侧：章节内容编辑器
    """

    def __init__(self, parent=None):
        """
        初始化写作编辑界面

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("writingTab")

        self._chapter_load_timer = None
        self._loading_file_path = None

        self._notify = NotificationManager(self)

        self.scrollArea = ScrollArea(self)
        self.scrollArea.setObjectName("writingScrollArea")
        self.scrollArea.setStyleSheet(
            "QScrollArea#writingScrollArea { background-color: transparent; border: none; }"
        )
        self.scrollArea.viewport().setStyleSheet("background-color: transparent;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建滚动区域内的内容控件
        self.contentWidget = QWidget()
        self.scrollArea.setWidget(self.contentWidget)

        # 主布局
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.scrollArea)

        # 内容布局
        self.contentLayout = QHBoxLayout(self.contentWidget)
        self.splitter = QSplitter(Qt.Horizontal, self.contentWidget)

        # 左侧面板：章节列表
        self.leftPanel = QWidget()
        self.leftLayout = QVBoxLayout(self.leftPanel)

        self.headerList = StrongBodyLabel("章节列表", self.leftPanel)

        # 章节列表容器
        self.chapterListContainer = QWidget()
        self.chapterListLayout = QVBoxLayout(self.chapterListContainer)
        self.chapterListLayout.setContentsMargins(0, 0, 0, 0)

        self.chapterList = QListWidget(self.chapterListContainer)
        self.chapterList.setStyleSheet(Styles.QListWidget)

        # 章节列表占位符
        self.chaptersPlaceholder = None

        self.chapterListLayout.addWidget(self.chapterList)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新列表", self.leftPanel)

        self.leftLayout.addWidget(self.headerList)
        self.leftLayout.addWidget(self.chapterListContainer)
        self.leftLayout.addWidget(self.refreshBtn)

        # 右侧面板：章节编辑器
        self.rightPanel = QWidget()
        self.rightLayout = QVBoxLayout(self.rightPanel)

        # 章节标题栏
        self.headerEditorLayout = QHBoxLayout()
        self.headerEditor = StrongBodyLabel("章节内容", self.rightPanel)
        self.headerEditorLayout.addWidget(self.headerEditor)

        # 工具栏：上一章、下一章
        self.toolbar = QHBoxLayout()
        self.prevBtn = PushButton(FIF.LEFT_ARROW, "上一章", self.rightPanel)
        self.nextBtn = PushButton(FIF.RIGHT_ARROW, "下一章", self.rightPanel)
        self.toolbar.addWidget(self.prevBtn)
        self.toolbar.addStretch(1)
        self.toolbar.addWidget(self.nextBtn)

        # 编辑器
        self.editor = PlainTextEdit(self.rightPanel)
        self.editor.setStyleSheet(Styles.PlainTextEdit)
        self.editor.setReadOnly(True)

        # Token信息按钮
        from qfluentwidgets import TransparentToolButton

        self.chapterTokenBtn = TransparentToolButton(FIF.INFO, self.rightPanel)
        self.chapterTokenBtn.setFixedSize(28, 28)
        self.chapterTokenBtn.setIconSize(QSize(16, 16))
        self.chapterTokenBtn.setToolTip("查看本章Token消耗详情")
        self.chapterTokenBtn.clicked.connect(self.show_chapter_token_info)
        self.headerEditorLayout.addWidget(self.chapterTokenBtn)

        self.rightLayout.addLayout(self.headerEditorLayout)
        self.rightLayout.addLayout(self.toolbar)
        self.rightLayout.addWidget(self.editor)

        # 将左右面板添加到分割器
        self.splitter.addWidget(self.leftPanel)
        self.splitter.addWidget(self.rightPanel)

        # 设置分割器比例（左侧1，右侧3）
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        # 禁止折叠面板
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)

        self.contentLayout.addWidget(self.splitter)

        # 配置文件
        self.config_file = "config.json"
        self.loaded_config = load_config(self.config_file) or {}

        # 当前章节编号
        self.current_chapter_number = None
        self.current_chapter_file = None

        # 默认文本标记
        self.has_default_text = False

        # 自动保存定时器
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save)

        # 连接信号
        self.refreshBtn.clicked.connect(self.load_chapters)
        self.chapterList.itemClicked.connect(self.on_chapter_selected)
        self.prevBtn.clicked.connect(self.on_prev)
        self.nextBtn.clicked.connect(self.on_next)
        self.editor.textChanged.connect(self.on_text_changed)

        # 初始化编辑工具包
        self.init_editor_toolkit()

        # 加载章节列表
        self.load_chapters()

    def init_editor_toolkit(self):
        """初始化编辑工具包"""
        self.editor_toolkit = EditorToolkit(self, self.get_filepath())
        self.editor_toolkit.add_editor(
            "main", self.editor, self.on_editor_selection_changed
        )
        self.editor_toolkit.init_shortcuts()

        # 设置编辑工具包的回调
        self._setup_editor_toolkit_handlers()

    def _setup_editor_toolkit_handlers(self):
        """设置编辑工具包的回调函数"""
        context_menu_handlers = {
            "on_copy": self._on_copy,
            "on_paste": self._on_paste,
            "on_fix_grammar": self._on_fix_grammar,
            "on_polish": self._on_polish,
            "on_expand": self._on_expand,
            "on_ask_composer": self._on_ask_composer,
        }
        self.editor_toolkit.set_context_menu_handlers(context_menu_handlers)

        composer_handlers = {
            "on_apply_changes": self._apply_changes,
        }
        self.editor_toolkit.set_composer_handlers(composer_handlers)

    def on_editor_selection_changed(self, editor_key: str):
        """编辑器选择变化时的回调"""
        self.editor_toolkit.set_active_editor(editor_key)
        self.editor_toolkit.context_menu_manager.on_selection_changed(editor_key)

    def _on_copy(self):
        """复制按钮点击"""
        self.editor.copy()

    def _on_paste(self):
        """粘贴按钮点击"""
        self.editor.paste()

    def _on_fix_grammar(self, text):
        """修复语法按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task("grammar", text)

    def _on_polish(self, text):
        """润色按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task("polish", text)

    def _on_expand(self, text, expand_type):
        """扩展描写按钮点击"""
        self.editor_toolkit.composer_manager.process_ai_task(
            "expand", text, expand_type
        )

    def _on_ask_composer(self, text):
        """询问Composer按钮点击"""
        self.editor_toolkit.composer_manager.ask_composer(text)

    def _apply_changes(self, modified_text: str):
        """应用修改到编辑器"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(modified_text)
            cursor.endEditBlock()
            self._notify.success("", "修改已应用")

    def on_diff_accepted(self, modified_text: str):
        """
        差异被接受时的回调

        Args:
            modified_text: 修改后的文本
        """
        self._apply_changes(modified_text)

    def on_diff_rejected(self):
        """差异被拒绝时的回调"""
        self._notify.info("", "修改已取消")

    def on_text_changed(self):
        """文本变化时重置自动保存定时器"""
        if hasattr(self, "has_default_text") and self.has_default_text:
            self.has_default_text = False
        self.auto_save_timer.start(1500)

    def auto_save(self):
        """自动保存"""
        if (
            hasattr(self, "current_chapter_file")
            and self.current_chapter_file
            and os.path.exists(self.current_chapter_file)
        ):
            if hasattr(self, "has_default_text") and self.has_default_text:
                return
            content = self.editor.toPlainText()
            save_string_to_txt(content, self.current_chapter_file)
            self.show_save_toast()

    def log(self, text):
        """
        记录日志

        Args:
            text: 要记录的日志文本
        """
        print(text)

    def show_save_toast(self):
        """显示保存提示"""
        now = datetime.now().strftime("%H:%M:%S")
        self._notify.success("", f"{now} 已保存")

    def get_filepath(self):
        """
        获取当前项目路径

        Returns:
            str: 项目路径
        """
        if hasattr(self.window(), "current_project") and self.window().current_project:
            return self.window().current_project.get("path", "").strip()
        other_params = self.loaded_config.get("other_params", {})
        return other_params.get("filepath", "").strip()

    def load_chapters(self):
        """
        加载章节列表

        从项目的 chapters 目录读取所有 chapter_*.txt 文件，
        按章节号排序后显示在列表中。
        """
        self.chapterList.clear()

        # 移除旧的占位符
        if self.chaptersPlaceholder:
            self.chaptersPlaceholder.deleteLater()
            self.chaptersPlaceholder = None

        filepath = self.get_filepath()
        if not filepath:
            self.headerList.setText("章节列表")
            # 显示未选择项目占位符
            empty_state = EmptyState.no_project()
            self.chaptersPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.chapterListContainer,
            )
            self.chapterList.hide()
            self.chapterListLayout.addWidget(self.chaptersPlaceholder)
            return

        self.headerList.setText("章节列表")
        chapters_dir = os.path.join(filepath, "chapters")

        # 查找所有章节文件
        files = []
        if os.path.exists(chapters_dir):
            files = glob.glob(os.path.join(chapters_dir, "chapter_*.txt"))
            try:
                # 按章节号排序
                files.sort(
                    key=lambda x: int(os.path.basename(x).split("_")[1].split(".")[0])
                )
            except Exception:
                files.sort()

        # 显示章节列表或占位符
        if not files:
            empty_state = EmptyState.chapters()
            self.chaptersPlaceholder = PlaceholderWidget(
                empty_state["icon"],
                empty_state["title"],
                empty_state["description"],
                self.chapterListContainer,
            )
            self.chapterList.hide()
            self.chapterListLayout.addWidget(self.chaptersPlaceholder)
        else:
            self.chapterList.show()
            # 添加到列表
            for file in files:
                name = os.path.basename(file)
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, file)  # 存储文件路径
                self.chapterList.addItem(item)

    def on_chapter_selected(self, item):
        """
        章节选中事件

        当用户点击章节列表中的某一章时，加载该章节内容到编辑器。

        Args:
            item: 被选中的列表项
        """
        file_path = item.data(Qt.UserRole)
        if os.path.exists(file_path):
            # 如果有正在进行的加载定时器，先停止
            if self._chapter_load_timer and self._chapter_load_timer.isActive():
                self._chapter_load_timer.stop()

            # 提取章节编号
            import re

            filename = os.path.basename(file_path)
            chapter_match = re.search(r"chapter_(\d+)\.txt", filename)
            if chapter_match:
                self.current_chapter_number = int(chapter_match.group(1))
            else:
                self.current_chapter_number = None

            self.current_chapter_file = file_path
            self.headerEditor.setText(f"章节内容: {os.path.basename(file_path)}")

            # 启用编辑器
            self.editor.setReadOnly(False)

            # 先显示加载中的文案
            self.editor.setPlainText(f"正在加载 {os.path.basename(file_path)}...")
            self.has_default_text = False

            # 设置正在加载的文件路径
            self._loading_file_path = file_path

            # 创建新的防抖定时器（300ms延迟）
            self._chapter_load_timer = QTimer(self)
            self._chapter_load_timer.setSingleShot(True)
            self._chapter_load_timer.timeout.connect(
                lambda: self._load_chapter_content(file_path)
            )
            self._chapter_load_timer.start(300)

    def show_chapter_token_info(self):
        """显示当前章节的Token消耗信息"""
        if not self.current_chapter_number:
            self._notify.warning("提示", "请先选择一个章节")
            return

        try:
            from core.llm import get_global_tokens_manager

            from ..widgets.token_info_dialog import NovelTokenStatsDialog

            tokens_manager = get_global_tokens_manager()
            if tokens_manager:
                dialog = NovelTokenStatsDialog(tokens_manager, parent=self.window())
                dialog.exec()
            else:
                self._notify.warning("提示", "暂无Token消耗记录")
        except Exception as e:
            self._notify.error("错误", f"打开Token信息失败: {e}")

    def on_prev(self):
        """
        切换到上一章
        """
        row = self.chapterList.currentRow()
        if row > 0:
            self.chapterList.setCurrentRow(row - 1)
            self.on_chapter_selected(self.chapterList.item(row - 1))

    def on_next(self):
        """
        切换到下一章
        """
        row = self.chapterList.currentRow()
        if row < self.chapterList.count() - 1:
            self.chapterList.setCurrentRow(row + 1)
            self.on_chapter_selected(self.chapterList.item(row + 1))

    def hideEvent(self, event):
        """
        标签页隐藏时隐藏上下文菜单

        Args:
            event: 隐藏事件
        """
        # 清理编辑工具包
        if hasattr(self, "editor_toolkit"):
            if hasattr(self.editor_toolkit, "context_menu_manager"):
                for (
                    menu
                ) in self.editor_toolkit.context_menu_manager.context_menus.values():
                    if menu.isVisible():
                        menu.hide()
            if hasattr(self.editor_toolkit, "composer_manager"):
                self.editor_toolkit.composer_manager.cleanup_composer()
        super().hideEvent(event)

    def _load_chapter_content(self, file_path):
        """
        加载章节内容

        Args:
            file_path: 章节文件路径

        Returns:
            无

        Raises:
            无
        """
        # 检查是否还是要加载这个文件（可能用户已经切换到其他章节了）
        if self._loading_file_path != file_path:
            return

        if not os.path.exists(file_path):
            self.editor.clear()
            return

        try:
            content = read_file(file_path)

            # 如果内容为空或只有空白字符，显示默认文案
            if not content or not content.strip():
                self.editor.setPlainText("在这里开始编写您的章节内容...")
                self.has_default_text = True
            else:
                self.editor.setPlainText(content)
                self.has_default_text = False
        except Exception as e:
            self.editor.setPlainText(f"加载失败: {str(e)}")
            self.log(f"加载章节失败: {e}")
