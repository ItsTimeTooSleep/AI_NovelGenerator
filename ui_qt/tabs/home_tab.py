# ui_qt/home_tab.py
import os

from PyQt5.QtCore import QEvent, QSize, Qt, QTimer
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    PlainTextEdit,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TextEdit,
    TransparentToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from core.config_manager import load_config
from ui_qt.utils.notification_manager import NotificationManager

from ..home import (
    AutoGenerateManager,
    AutosaveManager,
    ChapterLoader,
    ComposerFeatures,
    GenerationFlowManager,
    LayoutManager,
    LogPanelManager,
    ProgressManager,
    ProjectStateManager,
    ProjectStatusManager,
    StateController,
    StepManager,
    StreamingManager,
    UIBuilder,
)
from ..utils.animations import AnimationUtils
from ..utils.auto_generate import (
    AutoGenerateProgressPage,
)
from ..utils.generation_handlers import (
    ProjectDetailsDialog,
    clear_vectorstore_handler,
    do_consistency_check,
    import_knowledge_handler,
    save_project_params,
    show_plot_arcs_ui,
)
from ..utils.helpers import AdaptiveStackedWidget
from ..utils.styles import Styles


class HomeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeTab")

        self.current_project = None
        self.current_project_path = ""
        self._entered_full_layout = False
        self._entered_step4_actions = False

        self._chapter_load_timer = None
        self._loading_chapter_num = None
        self._is_loading_chapter = False

        self._notify = NotificationManager(self)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.headerWidget = QWidget(self)
        self.headerWidget.setMinimumHeight(70)
        self.headerWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.headerWidget.setStyleSheet("background-color: transparent;")
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(20, 15, 20, 15)

        self.bookTitleLabel = SubtitleLabel("未选择书籍", self.headerWidget)
        self.propertyBtn = PushButton(FIF.TAG, "属性", self.headerWidget)
        self.propertyBtn.clicked.connect(self.show_properties)

        self.headerLayout.addWidget(self.bookTitleLabel)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.propertyBtn)

        self.mainLayout.addWidget(self.headerWidget)

        self.splitter = QSplitter(Qt.Horizontal, self)

        self.leftPanel = QWidget()

        self.leftPanel.setObjectName("leftPanel")
        self.leftPanel.setStyleSheet("#leftPanel { background-color: transparent; }")
        self.leftLayout = QVBoxLayout(self.leftPanel)

        self.editorLabel = StrongBodyLabel("本章内容 (可编辑)", self.leftPanel)
        self.editor = TextEdit(self.leftPanel)
        self.editor.setPlaceholderText("此处显示生成的内容...")

        self.logOutput = TextEdit(self.leftPanel)
        self.logOutput.setReadOnly(True)

        self.leftLayout.addWidget(self.editorLabel)
        self.leftLayout.addWidget(self.editor, 2)
        self.leftLayout.addWidget(self.logOutput, 1)

        self.rightPanel = QScrollArea()
        self.rightPanel.setObjectName("rightPanelScroll")
        self.rightPanel.setStyleSheet(
            "QScrollArea#rightPanelScroll { background-color: transparent; border: none; }"
            + Styles.ScrollBar
        )
        self.rightPanel.viewport().setStyleSheet("background-color: transparent;")

        self.rightPanel.setWidgetResizable(True)
        self.rightWidget = QWidget()
        self.rightWidget.setObjectName("homeRightWidget")
        self.rightPanel.setWidget(self.rightWidget)
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(0)

        self.rightStack = AdaptiveStackedWidget(self.rightWidget)
        self.rightLayout.addWidget(self.rightStack, 1)

        self.simplifiedPage = QWidget(self.rightWidget)
        self.simplifiedPage.setObjectName("simplifiedPage")
        self.simplifiedPage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.simplifiedLayout = QVBoxLayout(self.simplifiedPage)
        self.simplifiedLayout.setContentsMargins(0, 0, 0, 0)
        self.simplifiedLayout.setSpacing(0)
        self.simplifiedLayout.setAlignment(Qt.AlignTop)

        self.centerContainer = QFrame(self.simplifiedPage)
        self.centerContainer.setObjectName("centerContainer")
        self.centerContainer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.centerLayout = QVBoxLayout(self.centerContainer)
        self.centerLayout.setContentsMargins(0, 0, 0, 0)
        self.centerLayout.setAlignment(Qt.AlignCenter)
        self.simplifiedLayout.addWidget(self.centerContainer, 1)
        self.rightStack.addWidget(self.simplifiedPage)

        self.fullPage = QWidget(self.rightWidget)
        self.fullScrollArea = QScrollArea(self.fullPage)
        self.fullScrollArea.setWidgetResizable(True)
        self.fullScrollArea.setObjectName("fullScrollArea")
        self.fullScrollArea.setStyleSheet(
            "QScrollArea#fullScrollArea { background-color: transparent; border: none; }"
            + Styles.ScrollBar
        )
        self.fullScrollArea.viewport().setStyleSheet("background-color: transparent;")

        self.fullContentWidget = QWidget()
        self.fullScrollArea.setWidget(self.fullContentWidget)
        self.fullLayout = QVBoxLayout(self.fullContentWidget)
        self.fullLayout.setContentsMargins(0, 0, 0, 0)

        self.paramsCard = CardWidget(self.fullContentWidget)
        self.paramsLayout = QVBoxLayout(self.paramsCard)

        self.initCard = CardWidget(self.fullContentWidget)
        self.initCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.initLayout = QVBoxLayout(self.initCard)

        self.actionsCard = CardWidget(self.fullContentWidget)
        self.actionsLayout = QVBoxLayout(self.actionsCard)

        self.fullLayout.setSpacing(16)
        self.fullLayout.addWidget(self.actionsCard)
        self.fullLayout.addWidget(self.paramsCard)
        self.fullLayout.addWidget(self.initCard)
        self.optionalCard = CardWidget(self.fullContentWidget)
        self.optionalLayout = QVBoxLayout(self.optionalCard)
        self.fullLayout.addWidget(self.optionalCard)
        self.fullLayout.setAlignment(Qt.AlignTop)

        self.fullPageLayout = QVBoxLayout(self.fullPage)
        self.fullPageLayout.setContentsMargins(0, 0, 0, 0)
        self.fullPageLayout.addWidget(self.fullScrollArea)

        self.rightStack.addWidget(self.fullPage)

        # 自动生成页面
        self.autoGeneratePage = AutoGenerateProgressPage(self.rightWidget)
        self.rightStack.addWidget(self.autoGeneratePage)
        self._auto_generate_worker = None

        self.rightPartContainer = QWidget(self)
        self.rightPartContainer.setObjectName("rightPartContainer")
        self.rightPartContainer.setStyleSheet(
            "QWidget#rightPartContainer { background-color: transparent; }"
        )

        self.rightPartMainLayout = QHBoxLayout(self.rightPartContainer)
        self.rightPartMainLayout.setContentsMargins(0, 0, 0, 0)
        self.rightPartMainLayout.setSpacing(0)

        self.rightPartInnerWidget = QWidget()
        self.rightPartInnerWidget.setStyleSheet("background-color: transparent;")
        self.rightPartInnerLayout = QHBoxLayout(self.rightPartInnerWidget)
        self.rightPartInnerLayout.setContentsMargins(0, 0, 0, 0)
        self.rightPartInnerLayout.setSpacing(0)

        self.rightPartSplitter = QSplitter(Qt.Horizontal, self.rightPartInnerWidget)
        self.rightPartSplitter.setContentsMargins(0, 0, 0, 0)
        self.rightPartSplitter.addWidget(self.rightPanel)
        self.logPanel = QFrame(self.rightPartInnerWidget)
        self.logPanel.setObjectName("logPanel")
        self.logPanel.setMinimumWidth(0)
        self.logPanel.setMaximumWidth(0)
        self.logPanel.setStyleSheet(
            "QFrame#logPanel { background-color: rgba(0,0,0,0.03); border-left: 1px solid rgba(0,0,0,0.08); }"
        )
        self.logPanelLayout = QVBoxLayout(self.logPanel)
        self.logPanelLayout.setContentsMargins(12, 12, 12, 12)
        self.logPanelLabel = StrongBodyLabel("输出日志", self.logPanel)
        self.logPanelLayout.addWidget(self.logPanelLabel)
        self.logPanel.hide()

        self.rightPartSplitter.addWidget(self.logPanel)

        self.rightPartInnerLayout.addWidget(self.rightPartSplitter)

        self.logToggleBtn = TransparentToolButton(
            FIF.RIGHT_ARROW, self.rightPartContainer
        )
        self.logToggleBtn.setFixedSize(28, 80)
        self.logToggleBtn.setIconSize(QSize(18, 18))
        self.logToggleBtn.setStyleSheet("""
            TransparentToolButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255,255,255,0.03),
                    stop:0.5 rgba(255,255,255,0.06),
                    stop:1 rgba(255,255,255,0.03));
                border: none;
                border-left: 1px solid rgba(0,0,0,0.06);
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                padding: 0px;
            }
            TransparentToolButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(162,155,254,0.08),
                    stop:0.5 rgba(162,155,254,0.12),
                    stop:1 rgba(162,155,254,0.08));
                border-left: 1px solid rgba(162,155,254,0.2);
            }
            TransparentToolButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(162,155,254,0.15),
                    stop:0.5 rgba(162,155,254,0.20),
                    stop:1 rgba(162,155,254,0.15));
            }
        """)
        self.logToggleBtn.setToolTip("显示/隐藏日志面板")
        # 注意：事件连接将在 _connect_events() 中进行，因为此时 log_panel_manager 还未初始化

        self.rightPartMainLayout.addWidget(self.rightPartInnerWidget, 1)
        self.rightPartMainLayout.addWidget(self.logToggleBtn)

        self._guide_mode = False
        self._log_panel_expanded = False
        # 使用安全的初始值而不是极大值
        self.rightPartSplitter.setSizes([800, 0])
        self.logToggleBtn.setIcon(FIF.LEFT_ARROW)
        self.logToggleBtn.setToolTip("显示日志面板")

        self.splitter.addWidget(self.leftPanel)
        self.splitter.addWidget(self.rightPartContainer)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.mainLayout.addWidget(self.splitter)

        self.config_file = "config.json"
        self.loaded_config = load_config(self.config_file) or {}
        self.streaming_enabled = self.loaded_config.get("streaming_enabled", True)
        self.streamTimer = QTimer(self)
        self.streamTimer.timeout.connect(self._update_stream_bridge)
        self._stream_target = None
        self._stream_text = ""
        self._stream_pos = 0
        self._streaming = False
        self._stream_stop_btn = None
        self._stream_chunk_size = 8
        self._stream_interval = 25
        self._step1_save_timer = QTimer(self)
        self._step1_save_timer.setSingleShot(True)
        self._step1_save_timer.timeout.connect(self._do_step1_autosave_bridge)
        self._last_step1_editor = None
        self._step2_save_timer = QTimer(self)
        self._step2_save_timer.setSingleShot(True)
        self._step2_save_timer.timeout.connect(self._do_step2_autosave_bridge)

        self._init_managers()
        self._connect_events()

        self.project_state_manager.check_project_files()
        # 确保跳过按钮的可见性正确更新
        QTimer.singleShot(
            200, self.project_state_manager.update_skip_buttons_visibility
        )
        QTimer.singleShot(100, self.animate_ui)

        # 初始化新功能模块
        self.composer_features = ComposerFeatures(self)
        self.composer_features.init_search_replace()
        self.composer_features.init_context_menu()
        self.composer_features.init_composer()
        self.composer_features.init_shortcuts()

    def _init_managers(self):
        self.streaming_manager = StreamingManager(self)
        self.autosave_manager = AutosaveManager(self)
        self.layout_manager = LayoutManager(self)
        self.progress_manager = ProgressManager(self)
        self.state_controller = StateController(self)
        self.step_manager = StepManager(self)
        self.ui_builder = UIBuilder(self)
        self.generation_flow = GenerationFlowManager(
            self,
            self.streaming_manager,
            self.autosave_manager,
            self.progress_manager,
            self.step_manager,
        )

        self.log_panel_manager = LogPanelManager(self)
        self.log_panel_manager.initialize()
        self.chapter_loader = ChapterLoader(self)
        self.project_state_manager = ProjectStateManager(self)
        self.project_status_manager = ProjectStatusManager(self)
        self.auto_generate_manager = AutoGenerateManager(self)

        self.ui_builder.initParams()
        self.ui_builder.initProjectActions()
        self.ui_builder.initChapterActions()
        self.ui_builder.initOptionalActions()
        self._bind_init_card_layout()

    def _bind_init_card_layout(self):
        if hasattr(self, "initStack"):
            self.initStack.currentChanged.connect(self._update_init_card_height)
            self.initStack.installEventFilter(self)
        if hasattr(self, "initCard"):
            self.initCard.installEventFilter(self)
        self._update_init_card_height()

    def _update_init_card_height(self):
        """
        更新 initCard 的高度以适应内容
        不再设置最大高度，让卡片可以自动拉伸显示所有内容
        """
        if not hasattr(self, "initLayout") or not hasattr(self, "initCard"):
            return
        self.initLayout.invalidate()
        size = self.initLayout.sizeHint()
        target_height = size.height()
        if target_height <= 0:
            return
        # 只设置最小高度，不设置最大高度，让卡片可以自动拉伸
        self.initCard.setMinimumHeight(target_height)
        self.initCard.setMaximumHeight(16777215)  # 设置为一个很大的值，相当于不限制

    def eventFilter(self, obj, event):
        if obj in (getattr(self, "initCard", None), getattr(self, "initStack", None)):
            if event.type() in (QEvent.LayoutRequest, QEvent.Resize):
                self._update_init_card_height()
        return super().eventFilter(obj, event)

    def _connect_events(self):
        """
        连接所有UI事件

        Args:
            无

        Returns:
            无

        Raises:
            无
        """
        # 日志面板切换按钮
        self.logToggleBtn.clicked.connect(self.log_panel_manager.toggle_panel)

        self.step1Btn.clicked.connect(self.generation_flow.on_step1)
        self.step2Btn.clicked.connect(self.generation_flow.on_step2)
        self.stopStep1Btn.clicked.connect(self.streaming_manager.stop_active_stream)
        if hasattr(self, "skipStep1Btn"):
            self.skipStep1Btn.clicked.connect(self._on_skip_step1)
        if hasattr(self, "skipStep2Btn"):
            self.skipStep2Btn.clicked.connect(self._on_skip_step2)
        self.stopStep2Btn.clicked.connect(self.streaming_manager.stop_active_stream)
        self.step2ToStep1Arrow.clicked.connect(self.step_manager.go_to_step1_from_step2)
        self.step1ToStep2Arrow.clicked.connect(self.step_manager.go_to_step2_from_step1)
        self.step1ReviewToStep2Arrow.clicked.connect(
            self.step_manager.go_to_step2_from_step1_review
        )
        self.continueToStep2Btn.clicked.connect(
            self.step_manager.go_to_step2_from_step1
        )
        self.viewInitStepsBtn.clicked.connect(self.step_manager.show_init_steps)
        self.step1TextEdit.textChanged.connect(
            lambda: self.autosave_manager._schedule_step1_autosave(self.step1TextEdit)
        )
        self.step1ReviewTextEdit.textChanged.connect(
            lambda: self.autosave_manager._schedule_step1_autosave(
                self.step1ReviewTextEdit
            )
        )
        self.step2TextEdit.textChanged.connect(
            self.autosave_manager._schedule_step2_autosave
        )
        if hasattr(self, "continueToReadyBtn"):
            self.continueToReadyBtn.clicked.connect(
                self.step_manager.go_to_ready_from_step2
            )
        self.continueToStep3Btn.clicked.connect(lambda: self._on_continue_to_step3())
        self.step3Btn.clicked.connect(self.generation_flow.on_step3)
        self.step4Btn.clicked.connect(self.generation_flow.on_step4)
        self.stopChapterStreamBtn.clicked.connect(
            self.streaming_manager.stop_active_stream
        )
        self.continueToStep4Btn.clicked.connect(self.step_manager.enter_step4_actions)
        self.backToStep3Btn.clicked.connect(self.step_manager.enter_step3_actions)

    def _on_continue_to_step3(self):
        """
        处理继续到Step 3的点击事件
        """
        import logging
        logging.info("[DEBUG] 开始执行 _on_continue_to_step3")
        logging.info(f"[DEBUG] 当前项目路径: {self.current_project_path}")
        logging.info(f"[DEBUG] 右侧面板状态: {self.rightPanel.isVisible()}")
        logging.info(f"[DEBUG] 右侧堆栈当前索引: {self.rightStack.currentIndex()}")
        logging.info(f"[DEBUG] 日志面板状态: {self.logPanel.isVisible()}")
        
        try:
            self.step_manager.enter_full_controls()
            logging.info("[DEBUG] enter_full_controls 执行成功")
        except Exception as e:
            logging.error(f"[DEBUG] enter_full_controls 执行失败: {e}")
            import traceback
            logging.error(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
        self.step1TokenBtn.clicked.connect(
            lambda: self.show_step_token_info("第一步 · 生成小说架构")
        )
        self.step2TokenBtn.clicked.connect(
            lambda: self.show_step_token_info("第二步 · 生成章节目录")
        )
        self.step4TokenBtn.clicked.connect(
            lambda: self.show_step_token_info("第四步 · 定稿章节")
        )
        self.step1BtnNoProject.clicked.connect(self._go_to_library)
        self.btnConsistency.clicked.connect(
            lambda: do_consistency_check(
                self.loaded_config,
                self.current_project_path,
                self.currChapterSpin.value(),
                self.log,
                self,
            )
        )
        self.btnImportKnowledge.clicked.connect(
            lambda: import_knowledge_handler(
                self.loaded_config, self.current_project_path, self.log, self
            )
        )
        self.btnClearVector.clicked.connect(
            lambda: clear_vectorstore_handler(self.current_project_path, self.log, self)
        )
        self.btnPlotArcs.clicked.connect(
            lambda: show_plot_arcs_ui(self.current_project_path, self)
        )
        self.currChapterSpin.valueChanged.connect(
            self.chapter_loader.on_chapter_spin_changed
        )
        # 编辑器内容变化时更新缓存
        self.editor.textChanged.connect(self.chapter_loader.on_editor_content_changed)
        # 自动生成按钮事件
        self.btnAutoGenerate.clicked.connect(
            self.auto_generate_manager.show_config_dialog
        )
        self.autoGeneratePage.stopButton.clicked.connect(
            self.auto_generate_manager.stop_generation
        )

        for idx, step_widget in enumerate(self.step1ProgressWidgets):
            step_widget.clicked.connect(
                lambda checked=False, w=step_widget: self.progress_manager.show_step_detail(
                    w
                )
            )
            step_widget.retry_clicked.connect(
                lambda step_idx=idx: self.progress_manager.retry_step1_step(step_idx)
            )

        if hasattr(self, "step2ProgressWidgets"):
            for idx, step_widget in enumerate(self.step2ProgressWidgets):
                step_widget.clicked.connect(
                    lambda checked=False, w=step_widget: self.progress_manager.show_step_detail(
                        w
                    )
                )
                step_widget.retry_clicked.connect(
                    lambda step_idx=idx: self.progress_manager.retry_step2_step(
                        step_idx
                    )
                )

    def animate_ui(self):
        if self.leftPanel.isVisible():
            AnimationUtils.fade_in(self.leftPanel, 600)
        if self.rightStack.currentIndex() == 1:
            AnimationUtils.animate_layout_items(self.fullLayout, 300)

    def log(self, text):
        self.log_panel_manager.log(text)

    def _reset_step1_progress_widgets(self):
        """
        重置Step1进度组件的状态
        用于切换项目时重置所有进度组件
        """
        if hasattr(self, "step1ProgressWidgets"):
            for step_widget in self.step1ProgressWidgets:
                step_widget.reset()
        if hasattr(self, "step1ProgressContainer"):
            self.step1ProgressContainer.hide()
            self.step1ProgressContainer.update_line_state(-1, [])
        # 确保continueToStep2Btn在重置时也隐藏
        if hasattr(self, "continueToStep2Btn"):
            self.continueToStep2Btn.hide()

    def _reset_step2_progress_widgets(self):
        """
        重置Step2进度组件的状态
        用于切换项目时重置所有进度组件
        """
        if hasattr(self, "step2ProgressWidgets"):
            for step_widget in self.step2ProgressWidgets:
                step_widget.reset()
        if hasattr(self, "step2ProgressContainer"):
            self.step2ProgressContainer.hide()
            self.step2ProgressContainer.update_line_state(-1, [])
        # 确保continueToReadyBtn在重置时也隐藏
        if hasattr(self, "continueToReadyBtn"):
            self.continueToReadyBtn.hide()

    def _reset_init_buttons(self):
        """
        重置初始步骤相关按钮的状态
        """
        if hasattr(self, "step1Btn"):
            self.step1Btn.setText("开始 Step 1")
            self.step1Btn.show()
        if hasattr(self, "stopStep1Btn"):
            self.stopStep1Btn.hide()
        if hasattr(self, "continueToStep2Btn"):
            self.continueToStep2Btn.hide()
        if hasattr(self, "step2Btn"):
            self.step2Btn.setText("开始 Step 2")
            self.step2Btn.show()
        if hasattr(self, "stopStep2Btn"):
            self.stopStep2Btn.hide()
        if hasattr(self, "continueToReadyBtn"):
            self.continueToReadyBtn.hide()

    def set_project(self, project_data):
        self.project_state_manager.set_project(project_data)

    def _update_stream_bridge(self):
        self.streaming_manager._update_stream()

    def _do_step1_autosave_bridge(self):
        self.autosave_manager._do_step1_autosave()

    def _do_step2_autosave_bridge(self):
        self.autosave_manager._do_step2_autosave()

    def _go_to_library(self):
        mw = self.window()
        if mw and hasattr(mw, "libraryTab"):
            mw.switchTo(mw.libraryTab)

    def show_properties(self):
        if not self.current_project:
            self._notify.warning("提示", "请先选择一个项目")
            return

        dialog = ProjectDetailsDialog(self.current_project, self.window())
        if dialog.exec():
            data = dialog.get_data()
            self.current_project.update(data)

            cover_path = data.get("cover_path")
            if cover_path and os.path.exists(cover_path):
                try:
                    import shutil

                    ext = os.path.splitext(cover_path)[1]
                    saved_cover_name = f"cover{ext}"
                    saved_cover_path = saved_cover_name
                    shutil.copy2(
                        cover_path,
                        os.path.join(self.current_project_path, saved_cover_name),
                    )
                    self.current_project["cover_image"] = saved_cover_path
                except Exception as e:
                    print(f"Failed to copy cover image: {e}")

            save_project_params(self)

            if "name" in data:
                self.bookTitleLabel.setText(data["name"])

            self._notify.success("成功", "项目属性已更新")

    def show_step_token_info(self, step_name: str):
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
            from ..utils.helpers import show_error_notification

            show_error_notification(
                "错误", f"打开Token信息失败: {e}", parent=self.window()
            )

    def check_project_files(self):
        """检查项目文件状态并更新UI显示（委托给 project_state_manager）"""
        self.project_state_manager.check_project_files()

    def init_search_replace(self):
        """初始化搜索替换功能（委托给 composer_features）"""

    def init_context_menu(self):
        """初始化选择上下文菜单（委托给 composer_features）"""

    def _connect_context_menu_signals(self, context_menu):
        """连接上下文菜单信号（委托给 composer_features）"""

    def init_composer(self):
        """初始化Composer AI功能（委托给 composer_features）"""

    def init_shortcuts(self):
        """初始化快捷键（委托给 composer_features）"""

    def get_current_active_editor(self):
        """获取当前活动的编辑器（委托给 composer_features）"""
        return self.composer_features.get_current_active_editor()

    def show_search_widget(self):
        """显示搜索替换窗口（委托给 composer_features）"""
        self.composer_features.show_search_widget()

    def on_selection_changed(self, editor_key):
        """文本选择变化时显示上下文菜单（委托给 composer_features）"""
        self.composer_features.on_selection_changed(editor_key)

    def show_context_menu(self, editor_key):
        """显示上下文菜单（委托给 composer_features）"""
        self.composer_features.show_context_menu(editor_key)

    def on_copy(self):
        """复制按钮点击（委托给 composer_features）"""
        self.composer_features.on_copy()

    def on_paste(self):
        """粘贴按钮点击（委托给 composer_features）"""
        self.composer_features.on_paste()

    def on_fix_grammar(self, text):
        """修复语法按钮点击（委托给 composer_features）"""
        self.composer_features.on_fix_grammar(text)

    def on_polish(self, text):
        """润色按钮点击（委托给 composer_features）"""
        self.composer_features.on_polish(text)

    def on_expand(self, text, expand_type):
        """扩展描写按钮点击（委托给 composer_features）"""
        self.composer_features.on_expand(text, expand_type)

    def on_ask_composer(self, text):
        """询问Composer按钮点击（委托给 composer_features）"""
        self.composer_features.on_ask_composer(text)

    def cleanup_composer(self):
        """清理composer相关组件（委托给 composer_features）"""
        self.composer_features.cleanup_composer()

    def on_ai_level_changed(self, new_level):
        """
        处理AI等级变化（委托给 composer_features）

        Args:
            new_level: 新的AI等级
        """
        self.composer_features.on_ai_level_changed(new_level)

    def process_ai_task(self, task_type, text, extra_param=""):
        """
        处理AI任务（委托给 composer_features）

        Args:
            task_type: 任务类型 (grammar/polish/expand/query)
            text: 选中文本
            extra_param: 额外参数（如扩展类型或用户查询）
        """
        self.composer_features.process_ai_task(task_type, text, extra_param)

    def process_ai_request(self, task_type, original_text, extra_param):
        """
        调用 LLM 处理 AI 任务（委托给 composer_features）

        Args:
            task_type: 任务类型
            original_text: 原始文本
            extra_param: 额外参数
        """
        self.composer_features.process_ai_request(task_type, original_text, extra_param)

    def show_diff_preview(self, original_text, modified_text):
        """
        显示差异预览（委托给 composer_features）

        Args:
            original_text: 原始文本
            modified_text: 修改后的文本
        """
        self.composer_features.show_diff_preview(original_text, modified_text)

    def apply_changes(self, modified_text):
        """
        应用修改（委托给 composer_features）

        Args:
            modified_text: 修改后的文本
        """
        self.composer_features.apply_changes(modified_text)

    def reject_changes(self):
        """拒绝修改（委托给 composer_features）"""
        self.composer_features.reject_changes()

    def show_auto_generate_config(self):
        """显示自动生成配置对话框（委托给 auto_generate_manager）"""
        self.auto_generate_manager.show_config_dialog()

    def _get_last_completed_chapter(self) -> int:
        """获取最后一个已完成的章节号（委托给 auto_generate_manager）"""
        return self.auto_generate_manager._get_last_completed_chapter()

    def start_auto_generate(self, start_chapter: int, chapter_count: int):
        """开始自动生成（委托给 auto_generate_manager）"""
        self.auto_generate_manager.start_generation(start_chapter, chapter_count)

    def stop_auto_generate(self):
        """停止自动生成（委托给 auto_generate_manager）"""
        self.auto_generate_manager.stop_generation()

    def _on_auto_gen_chapter_started(self, chapter_num: int):
        """章节开始生成时的回调（委托给 auto_generate_manager）"""
        self.auto_generate_manager._on_chapter_started(chapter_num)

    def _on_auto_gen_step_changed(self, step_name: str):
        """步骤变化时的回调（委托给 auto_generate_manager）"""
        self.auto_generate_manager._on_step_changed(step_name)

    def _on_auto_gen_chapter_completed(self, chapter_num: int):
        """章节完成时的回调（委托给 auto_generate_manager）"""
        self.auto_generate_manager._on_chapter_completed(chapter_num)

    def _on_auto_gen_error(self, error_msg: str):
        """错误发生时的回调（委托给 auto_generate_manager）"""
        self.auto_generate_manager._on_error(error_msg)

    def _on_auto_gen_finished(self, success: bool):
        """自动生成完成时的回调（委托给 auto_generate_manager）"""
        self.auto_generate_manager._on_finished(success)

    def _on_chapter_spin_changed(self):
        """章节选择器变化时的处理函数（委托给 chapter_loader）"""
        self.chapter_loader.on_chapter_spin_changed()

    def _show_loading_text(self, chap_num):
        """显示加载中的文案（委托给 chapter_loader）"""
        self.chapter_loader._show_loading_text(chap_num)

    def _load_chapter_content(self, chap_num):
        """加载章节内容（委托给 chapter_loader）"""
        self.chapter_loader._load_chapter_content(chap_num)

    def _on_editor_content_changed(self):
        """编辑器内容变化时的处理函数（委托给 chapter_loader）"""
        self.chapter_loader.on_editor_content_changed()

    def _return_to_main_page(self):
        """返回主页面"""
        self.project_state_manager.check_project_files()

    def _update_skip_buttons_visibility(self):
        """根据开发者模式更新跳过按钮的可见性（委托给 project_state_manager）"""
        self.project_state_manager.update_skip_buttons_visibility()

    def _on_skip_step1(self):
        """处理跳过 Step 1 的逻辑（委托给 project_state_manager）"""
        self.project_state_manager._on_skip_step1()

    def _on_skip_step2(self):
        """处理跳过 Step 2 的逻辑（委托给 project_state_manager）"""
        self.project_state_manager._on_skip_step2()
