# -*- coding: utf-8 -*-
"""
UI 构建器模块 - 重构版

本模块负责构建 HomeTab 的 UI 组件，使用新的模块化架构。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
)
from qfluentwidgets import (
    IconWidget,
    IndeterminateProgressBar,
    PrimaryPushButton,
    PushButton,
    SpinBox,
    StrongBodyLabel,
    TextEdit,
)
from qfluentwidgets import FluentIcon as FIF

from ..utils.helpers import AdaptiveStackedWidget
from ..utils.styles import Styles, ThemeManager
from .step1_widget import Step1Widget
from .step2_widget import Step2Widget
from .step3_widget import Step3Widget
from .step4_widget import Step4Widget


class UIBuilder:
    """
    UI 构建器类

    负责构建 HomeTab 的所有 UI 组件，使用新的模块化架构。
    """

    def __init__(self, home_tab):
        """
        初始化 UIBuilder

        Args:
            home_tab: HomeTab 主窗口实例
        """
        self.home_tab = home_tab
        self.step1_widget = Step1Widget(home_tab)
        self.step2_widget = Step2Widget(home_tab)
        self.step3_widget = Step3Widget(home_tab)
        self.step4_widget = Step4Widget(home_tab)

    def initParams(self):
        """
        初始化参数卡片
        """
        self.home_tab.paramsHeader = StrongBodyLabel(
            "生成控制", self.home_tab.paramsCard
        )
        self.home_tab.paramsHeader.setWordWrap(True)
        self.home_tab.paramsLayout.addWidget(self.home_tab.paramsHeader)
        paramsHint = CaptionLabel(
            "选择要操作的章节，可选填以下内容以影响生成风格", self.home_tab.paramsCard
        )
        paramsHint.setWordWrap(True)
        paramsHint.setStyleSheet(Styles.HintText + " margin-bottom: 6px;")
        self.home_tab.paramsLayout.addWidget(paramsHint)

        self.home_tab.currChapterLabel = BodyLabel(
            "当前操作章节", self.home_tab.paramsCard
        )
        self.home_tab.currChapterLabel.setWordWrap(True)
        self.home_tab.currChapterSpin = SpinBox(self.home_tab.paramsCard)
        self.home_tab.currChapterSpin.setRange(1, 1000)
        self.home_tab.currChapterSpin.valueChanged.connect(
            self.home_tab.check_project_files
        )
        self.home_tab.paramsLayout.addWidget(self.home_tab.currChapterLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.currChapterSpin)

        self.home_tab.guidanceLabel = BodyLabel(
            "用户特别指导 (可选)", self.home_tab.paramsCard
        )
        self.home_tab.guidanceLabel.setWordWrap(True)
        self.home_tab.guidanceEdit = TextEdit(self.home_tab.paramsCard)
        self.home_tab.guidanceEdit.setMinimumHeight(60)
        self.home_tab.guidanceEdit.setMaximumHeight(120)
        self.home_tab.guidanceEdit.setPlaceholderText(
            "输入您希望AI特别注意的创作指导..."
        )
        self.home_tab.paramsLayout.addWidget(self.home_tab.guidanceLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.guidanceEdit)

        self.home_tab.charactersInvolvedLabel = BodyLabel(
            "本章涉及角色 (可选)", self.home_tab.paramsCard
        )
        self.home_tab.charactersInvolvedLabel.setWordWrap(True)
        self.home_tab.charactersInvolvedEdit = TextEdit(self.home_tab.paramsCard)
        self.home_tab.charactersInvolvedEdit.setMinimumHeight(40)
        self.home_tab.charactersInvolvedEdit.setMaximumHeight(80)
        self.home_tab.charactersInvolvedEdit.setPlaceholderText(
            "输入本章将出现的角色名称，多个角色用逗号分隔..."
        )
        self.home_tab.paramsLayout.addWidget(self.home_tab.charactersInvolvedLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.charactersInvolvedEdit)

        self.home_tab.keyItemsLabel = BodyLabel(
            "关键道具 (可选)", self.home_tab.paramsCard
        )
        self.home_tab.keyItemsLabel.setWordWrap(True)
        self.home_tab.keyItemsEdit = TextEdit(self.home_tab.paramsCard)
        self.home_tab.keyItemsEdit.setMinimumHeight(40)
        self.home_tab.keyItemsEdit.setMaximumHeight(80)
        self.home_tab.keyItemsEdit.setPlaceholderText(
            "输入本章将出现的关键道具，多个道具用逗号分隔..."
        )
        self.home_tab.paramsLayout.addWidget(self.home_tab.keyItemsLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.keyItemsEdit)

        self.home_tab.sceneLocationLabel = BodyLabel(
            "场景地点 (可选)", self.home_tab.paramsCard
        )
        self.home_tab.sceneLocationLabel.setWordWrap(True)
        self.home_tab.sceneLocationEdit = TextEdit(self.home_tab.paramsCard)
        self.home_tab.sceneLocationEdit.setMinimumHeight(40)
        self.home_tab.sceneLocationEdit.setMaximumHeight(80)
        self.home_tab.sceneLocationEdit.setPlaceholderText("输入本章故事发生的地点...")
        self.home_tab.paramsLayout.addWidget(self.home_tab.sceneLocationLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.sceneLocationEdit)

        self.home_tab.timeConstraintLabel = BodyLabel(
            "时间约束 (可选)", self.home_tab.paramsCard
        )
        self.home_tab.timeConstraintLabel.setWordWrap(True)
        self.home_tab.timeConstraintEdit = TextEdit(self.home_tab.paramsCard)
        self.home_tab.timeConstraintEdit.setMinimumHeight(40)
        self.home_tab.timeConstraintEdit.setMaximumHeight(80)
        self.home_tab.timeConstraintEdit.setPlaceholderText(
            '输入本章的时间约束，如"黄昏时分"、"三天内"等...'
        )
        self.home_tab.paramsLayout.addWidget(self.home_tab.timeConstraintLabel)
        self.home_tab.paramsLayout.addWidget(self.home_tab.timeConstraintEdit)

    def initProjectActions(self):
        """
        初始化项目操作卡片
        """
        flowTitle = StrongBodyLabel("创作流程", self.home_tab.initCard)
        flowTitle.setAlignment(Qt.AlignCenter)
        flowTitle.setStyleSheet("margin: 0;")
        flowCaption = CaptionLabel(
            "按顺序完成每一步，界面会自动引导您到下一步", self.home_tab.initCard
        )
        flowCaption.setAlignment(Qt.AlignCenter)
        flowCaption.setStyleSheet(Styles.HintText + " margin: 0;")
        self.home_tab.initLayout.setSpacing(0)
        self.home_tab.initLayout.addWidget(flowTitle)
        self.home_tab.initLayout.addSpacing(4)
        self.home_tab.initLayout.addWidget(flowCaption)
        self.home_tab.initLayout.addSpacing(32)
        self.home_tab.initStack = AdaptiveStackedWidget(self.home_tab.initCard)
        self.home_tab.initLayout.addWidget(self.home_tab.initStack)

        self.home_tab.frameNoProject = self.step1_widget.build_frame_no_project(
            self.home_tab.initCard
        )
        self.home_tab.initStack.addWidget(self.home_tab.frameNoProject)

        self.home_tab.frameStep1 = self.step1_widget.build_frame_step1(
            self.home_tab.initCard
        )
        self.home_tab.initStack.addWidget(self.home_tab.frameStep1)

        self.home_tab.frameStep2 = self.step2_widget.build_frame_step2(
            self.home_tab.initCard
        )
        self.home_tab.initStack.addWidget(self.home_tab.frameStep2)

        self.home_tab.frameStep1Review = self.step1_widget.build_frame_step1_review(
            self.home_tab.initCard
        )
        self.home_tab.initStack.addWidget(self.home_tab.frameStep1Review)

        self._build_frame_init_done()

    def _build_frame_init_done(self):
        """
        构建项目已完成界面
        """
        self.home_tab.frameInitDone = QFrame(self.home_tab.initCard)
        self.home_tab.frameInitDone.setObjectName("stepCardFrame")
        self.home_tab.frameInitDone.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        layoutDone = QVBoxLayout(self.home_tab.frameInitDone)
        layoutDone.setSpacing(4)
        layoutDone.setContentsMargins(0, 0, 0, 0)
        rowDone = QHBoxLayout()
        rowDone.addStretch(1)
        iconDone = IconWidget(FIF.ACCEPT, self.home_tab.frameInitDone)
        iconDone.setFixedSize(32, 32)
        rowDone.addWidget(iconDone)
        titleDone = StrongBodyLabel("项目已就绪", self.home_tab.frameInitDone)
        font = titleDone.font()
        pt = font.pointSize()
        if pt > 0:
            font.setPointSize(min(20, pt + 1))
            titleDone.setFont(font)
        titleDone.setAlignment(Qt.AlignCenter)
        rowDone.addWidget(titleDone)
        rowDone.addStretch(1)
        layoutDone.addLayout(rowDone)
        layoutDone.addSpacing(8)
        statusDone = BodyLabel(
            "架构与目录已生成，可以开始写章节。需要查看或调整时可点击下方按钮。",
            self.home_tab.frameInitDone,
        )
        statusDone.setWordWrap(True)
        statusDone.setAlignment(Qt.AlignCenter)
        statusDone.setStyleSheet(Styles.ChapterStatusSuccess + " margin: 0;")
        layoutDone.addWidget(statusDone)
        layoutDone.addSpacing(16)
        viewRow = QHBoxLayout()
        viewRow.addStretch(1)
        self.home_tab.viewInitStepsBtn = PushButton(
            "查看第一步 / 第二步", self.home_tab.frameInitDone
        )
        self.home_tab.viewInitStepsBtn.setFixedHeight(36)
        viewRow.addWidget(self.home_tab.viewInitStepsBtn)
        viewRow.addStretch(1)
        layoutDone.addLayout(viewRow)
        layoutDone.addSpacing(16)
        self.home_tab.continueToStep3Btn = PrimaryPushButton(
            "继续到第三步（完整控件）", self.home_tab.frameInitDone
        )
        self.home_tab.continueToStep3Btn.setFixedHeight(42)
        self.home_tab.continueToStep3Btn.setMinimumWidth(240)
        contRow = QHBoxLayout()
        contRow.addStretch(1)
        contRow.addWidget(self.home_tab.continueToStep3Btn)
        contRow.addStretch(1)
        layoutDone.addLayout(contRow)
        self.home_tab.initStack.addWidget(self.home_tab.frameInitDone)

    def initChapterActions(self):
        """
        初始化章节操作卡片
        """
        self.home_tab.actionsStack = QStackedWidget(self.home_tab.actionsCard)
        self.home_tab.actionsLayout.addWidget(self.home_tab.actionsStack)

        self._build_frame_actions_locked()

        self.home_tab.frameStep3Actions = self.step3_widget.build_frame_step3_actions(
            self.home_tab.actionsCard
        )
        self.home_tab.actionsStack.addWidget(self.home_tab.frameStep3Actions)

        self.home_tab.frameStep4Actions = self.step4_widget.build_frame_step4_actions(
            self.home_tab.actionsCard
        )
        self.home_tab.actionsStack.addWidget(self.home_tab.frameStep4Actions)

        self.home_tab.progressBar = IndeterminateProgressBar(self.home_tab.actionsCard)
        self.home_tab.progressBar.setVisible(False)
        self.home_tab.actionsLayout.addWidget(self.home_tab.progressBar)

    def _build_frame_actions_locked(self):
        """
        构建操作锁定界面
        """
        self.home_tab.frameActionsLocked = QFrame(self.home_tab.actionsCard)
        layoutLocked = QVBoxLayout(self.home_tab.frameActionsLocked)
        layoutLocked.setSpacing(12)
        iconLock = IconWidget(FIF.INFO, self.home_tab.frameActionsLocked)
        iconLock.setFixedSize(36, 36)
        layoutLocked.addWidget(iconLock, 0, Qt.AlignCenter)
        titleLock = StrongBodyLabel("章节生成", self.home_tab.frameActionsLocked)
        titleLock.setAlignment(Qt.AlignCenter)
        layoutLocked.addWidget(titleLock)
        msgLock = BodyLabel(
            "完成上方「第一步」和「第二步」后，即可在此生成各章草稿并定稿。",
            self.home_tab.frameActionsLocked,
        )
        msgLock.setWordWrap(True)
        msgLock.setAlignment(Qt.AlignCenter)
        msgLock.setStyleSheet(
            f"color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
        )
        layoutLocked.addWidget(msgLock)
        self.home_tab.actionsStack.addWidget(self.home_tab.frameActionsLocked)

    def initOptionalActions(self):
        """
        初始化可选功能卡片
        """
        optTitle = StrongBodyLabel("可选功能", self.home_tab.optionalCard)
        self.home_tab.optionalLayout.addWidget(optTitle)
        optHint = CaptionLabel(
            "知识库与向量库作用于当前项目路径；一致性审校针对当前章节。",
            self.home_tab.optionalCard,
        )
        optHint.setWordWrap(True)
        optHint.setStyleSheet(Styles.HintText + " margin-bottom: 12px;")
        self.home_tab.optionalLayout.addWidget(optHint)

        btnCol = QVBoxLayout()
        btnCol.setSpacing(8)

        self.home_tab.btnAutoGenerate = PushButton(
            FIF.ROBOT, "自动生成", self.home_tab.optionalCard
        )
        self.home_tab.btnAutoGenerate.setFixedHeight(40)

        self.home_tab.btnConsistency = PushButton(
            FIF.SYNC, "一致性审校", self.home_tab.optionalCard
        )
        self.home_tab.btnConsistency.setFixedHeight(40)

        self.home_tab.btnImportKnowledge = PushButton(
            FIF.ADD, "导入知识库", self.home_tab.optionalCard
        )
        self.home_tab.btnImportKnowledge.setFixedHeight(40)

        self.home_tab.btnClearVector = PushButton(
            FIF.DELETE, "清空向量库", self.home_tab.optionalCard
        )
        self.home_tab.btnClearVector.setFixedHeight(40)

        self.home_tab.btnPlotArcs = PushButton(
            FIF.MENU, "查看剧情要点", self.home_tab.optionalCard
        )
        self.home_tab.btnPlotArcs.setFixedHeight(40)

        btnCol.addWidget(self.home_tab.btnAutoGenerate)
        btnCol.addWidget(self.home_tab.btnConsistency)
        btnCol.addWidget(self.home_tab.btnImportKnowledge)
        btnCol.addWidget(self.home_tab.btnClearVector)
        btnCol.addWidget(self.home_tab.btnPlotArcs)
        btnCol.addStretch(1)
        self.home_tab.optionalLayout.addLayout(btnCol)
