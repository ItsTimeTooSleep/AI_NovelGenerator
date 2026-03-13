# ui_qt/library_tab.py
import os
import shutil

from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    EditableComboBox,
    FlowLayout,
    IconWidget,
    LineEdit,
    MessageBox,
    MessageBoxBase,
    PrimaryPushButton,
    PushButton,
    RoundMenu,
    ScrollArea,
    SpinBox,
    StrongBodyLabel,
    SubtitleLabel,
    TextEdit,
    ToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from novel_generator.project_manager import ProjectManager
from ui_qt.utils.notification_manager import NotificationManager

from ..utils.animations import AnimationUtils
from ..utils.dialog_sizer import DialogSizer, ScrollableContainer
from ..utils.styles import Styles, ThemeManager, get_book_cover_color
from ..widgets.cover_editor import CoverEditorDialog
from ..widgets.placeholder_widget import EmptyState, PlaceholderWidget


class CreateProjectDialog(MessageBoxBase):
    """
    新建图书对话框
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("新建图书", self)
        self.viewLayout.addWidget(self.titleLabel)

        self._container = ScrollableContainer(self)
        self._container.set_content_margins(0, 0, 0, 0)
        content_layout = self._container.content_layout()
        content_layout.setSpacing(12)

        self.formLayout = QFormLayout()

        self.nameEdit = LineEdit(self._container)
        self.nameEdit.setPlaceholderText("请输入书名（留空自动生成）")
        self.formLayout.addRow("书名:", self.nameEdit)

        self.authorEdit = LineEdit(self._container)
        self.authorEdit.setPlaceholderText("作者名")
        self.formLayout.addRow("作者:", self.authorEdit)

        self.genreCombo = EditableComboBox(self._container)
        self.genreCombo.addItems(
            ["玄幻", "都市", "仙侠", "科幻", "悬疑", "历史", "游戏", "奇幻"]
        )
        self.genreCombo.setCurrentIndex(-1)
        self.genreCombo.setPlaceholderText("请选择或输入类型")
        self.formLayout.addRow("类型:", self.genreCombo)

        self.topicEdit = TextEdit(self._container)
        self.topicEdit.setPlaceholderText("请输入小说主题...")
        self.topicEdit.setMaximumHeight(100)
        self.formLayout.addRow("主题:", self.topicEdit)

        self.coverLayout = QHBoxLayout()
        self.coverPathEdit = LineEdit(self._container)
        self.coverPathEdit.setPlaceholderText("选择封面图片 (可选)")
        self.coverPathEdit.setReadOnly(True)
        self.coverBtn = PushButton(FIF.PHOTO, "编辑", self._container)
        self.coverLayout.addWidget(self.coverPathEdit)
        self.coverLayout.addWidget(self.coverBtn)
        self.formLayout.addRow("封面:", self.coverLayout)

        self.chapterCountSpin = SpinBox(self._container)
        self.chapterCountSpin.setRange(10, 2000)
        self.chapterCountSpin.setValue(100)
        self.formLayout.addRow("预计章节数:", self.chapterCountSpin)

        self.wordCountSpin = SpinBox(self._container)
        self.wordCountSpin.setRange(1000, 20000)
        self.wordCountSpin.setValue(3000)
        self.wordCountSpin.setSingleStep(100)
        self.formLayout.addRow("单章字数:", self.wordCountSpin)

        content_layout.addLayout(self.formLayout)
        content_layout.addStretch()

        self.viewLayout.addWidget(self._container)

        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.35,
            height_ratio=0.55,
            min_width=380,
            min_height=350,
        )
        sizer.apply_to_widget(self.widget, parent)

        self.coverBtn.clicked.connect(self.browse_cover)

    def browse_cover(self):
        dialog = CoverEditorDialog(self.coverPathEdit.text(), self)
        if dialog.exec():
            result = dialog.get_result()
            if result:
                self.coverPathEdit.setText(result)

    def get_data(self):
        return {
            "name": self.nameEdit.text(),
            "author": self.authorEdit.text(),
            "genre": self.genreCombo.currentText(),
            "topic": self.topicEdit.toPlainText(),
            "cover_path": self.coverPathEdit.text(),
            "total_chapters_plan": self.chapterCountSpin.value(),
            "words_per_chapter_plan": self.wordCountSpin.value(),
        }


class EditProjectDialog(MessageBoxBase):
    """
    编辑图书信息对话框

    Args:
        project_data: 项目数据字典
        parent: 父窗口
    """

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data

        self.titleLabel = SubtitleLabel("编辑图书信息", self)
        self.viewLayout.addWidget(self.titleLabel)

        from ..widgets.project_edit_form import ProjectEditForm

        self.form = ProjectEditForm(project_data, self)
        self.viewLayout.addWidget(self.form)

        self.yesButton.setText("保存修改")
        self.cancelButton.setText("关闭")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.60,
            min_width=450,
            min_height=400,
        )
        sizer.apply_to_widget(self.widget, parent)

    def get_data(self):
        """
        获取编辑后的项目数据

        Returns:
            dict: 项目数据字典
        """
        return self.form.get_data()


class BookCover(QWidget):
    def __init__(self, title, genre, cover_path=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.genre = genre
        self.cover_path = cover_path
        self.setFixedSize(60, 80)

        from qfluentwidgets import isDarkTheme

        self.is_dark = isDarkTheme()
        self.bg_color = get_book_cover_color(title, is_dark=self.is_dark)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        brush = QBrush(self.bg_color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)

        if self.cover_path and os.path.exists(self.cover_path):
            try:
                pixmap = QPixmap(self.cover_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.size(),
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation,
                    )

                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.drawRoundedRect(self.rect(), 4, 4)
                    return
            except Exception:
                pass

        text_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_INVERTED, self.is_dark
        )
        painter.setPen(QColor(text_color))
        font = QFont("Microsoft YaHei", 20, QFont.Bold)
        painter.setFont(font)

        first_char = self.title[0] if self.title else "?"
        painter.drawText(self.rect(), Qt.AlignCenter, first_char)


class ProjectCard(CardWidget):
    projectClicked = pyqtSignal(str)
    projectEditRequested = pyqtSignal(dict)
    projectDeleteRequested = pyqtSignal(dict)

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.setMinimumSize(280, 160)
        self.setMaximumHeight(180)
        self.setCursor(Qt.PointingHandCursor)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.contentWidget = QWidget(self)
        self.contentLayout = QHBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(20, 18, 20, 18)
        self.contentLayout.setSpacing(16)

        cover_rel_path = project_data.get("cover_image", "")
        cover_abs_path = ""
        if cover_rel_path and "path" in project_data:
            cover_abs_path = os.path.join(project_data["path"], cover_rel_path)

        self.cover = BookCover(
            project_data.get("name", "未命名"),
            project_data.get("genre", "未分类"),
            cover_path=cover_abs_path,
            parent=self,
        )
        self.cover.setFixedSize(70, 95)

        self.infoWidget = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.infoWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(6)

        self.titleLabel = StrongBodyLabel(project_data.get("name", "未命名"), self)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setMaximumHeight(50)

        genre = project_data.get("genre", "未分类")
        author = project_data.get("author", "未知")
        self.infoLabel = BodyLabel(f"{genre} · {author}", self)
        self.infoLabel.setStyleSheet(Styles.HintText + " font-size: 12px;")

        self.progressLabel = BodyLabel(
            "进度: 第 {} 章".format(project_data.get("current_chapter", 1)), self
        )
        self.progressLabel.setStyleSheet(Styles.StatusLabelInfo + " font-size: 12px;")

        updated = project_data.get("updated_at", "")[:10]
        self.dateLabel = BodyLabel(f"更新: {updated}", self)
        self.dateLabel.setStyleSheet(Styles.SecondaryText + " font-size: 11px;")

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.infoLabel)
        self.vBoxLayout.addWidget(self.progressLabel)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.dateLabel)

        self.contentLayout.addWidget(self.cover)
        self.contentLayout.addWidget(self.infoWidget)

        self.mainLayout.addWidget(self.contentWidget)

        self.menuBtn = ToolButton(FIF.MORE, self)
        self.menuBtn.setFixedSize(28, 28)
        self.menuBtn.setCursor(Qt.PointingHandCursor)
        self.menuBtn.clicked.connect(self.show_menu)
        self.menuBtn.setParent(self)
        self.menuBtn.raise_()
        self.menuBtn.setStyleSheet(Styles.MenuButton)

        self.clicked.connect(self._on_clicked)

        from qfluentwidgets import isDarkTheme

        isDarkTheme()
        self.setStyleSheet(Styles.ProjectCardShadow)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow_color = QColor(
            ThemeManager.get_color(ThemeManager.Colors.SHADOW_PRIMARY)
        )
        shadow_color.setAlpha(25)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.menuBtn.move(self.width() - 36, 8)

    def _on_clicked(self):
        self.projectClicked.emit(self.project_data["path"])

    def show_menu(self):
        menu = RoundMenu(parent=self)

        edit_action = QAction(FIF.EDIT.icon(), "编辑", self)
        edit_action.triggered.connect(
            lambda: self.projectEditRequested.emit(self.project_data)
        )
        menu.addAction(edit_action)

        delete_action = QAction(FIF.DELETE.icon(), "删除", self)
        delete_action.triggered.connect(
            lambda: self.projectDeleteRequested.emit(self.project_data)
        )
        menu.addAction(delete_action)

        menu.exec_(self.menuBtn.mapToGlobal(QPoint(0, self.menuBtn.height())))


class LibraryTab(ScrollArea):
    project_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("libraryTab")

        self._notify = NotificationManager(self)

        self.view = QWidget()
        self.view.setObjectName("view")
        self.setStyleSheet("LibraryTab, #view { background-color: transparent; }")

        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(40, 40, 40, 40)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.headerWidget = QWidget()
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.iconWidget = IconWidget(FIF.BOOK_SHELF, self.view)
        self.iconWidget.setFixedSize(32, 32)

        self.titleContainer = QWidget()
        self.titleLayout = QVBoxLayout(self.titleContainer)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.setSpacing(0)

        self.titleLabel = SubtitleLabel("我的图书馆", self.view)
        self.subtitleLabel = BodyLabel("管理和创作您的小说世界", self.view)
        self.subtitleLabel.setStyleSheet(Styles.SecondaryText)

        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addWidget(self.subtitleLabel)

        self.createBtn = PrimaryPushButton(FIF.ADD, "新建图书", self.view)
        self.createBtn.clicked.connect(self.show_create_dialog)

        self.headerLayout.addWidget(self.iconWidget)
        self.headerLayout.addSpacing(10)
        self.headerLayout.addWidget(self.titleContainer)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.createBtn)

        self.vBoxLayout.addWidget(self.headerWidget)
        self.vBoxLayout.addSpacing(10)

        self.gridWidget = QWidget()
        self.flowLayout = FlowLayout(self.gridWidget, needAni=False)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setVerticalSpacing(20)
        self.flowLayout.setHorizontalSpacing(20)

        self.vBoxLayout.addWidget(self.gridWidget)

        self.placeholder = None

        try:
            from core.config_manager import load_config

            config = load_config("config.json")
            novels_dir = config.get(
                "novels_directory", os.path.join(os.getcwd(), "novels")
            )
            self.project_manager = ProjectManager(base_dir=novels_dir)
        except Exception as e:
            print(f"Failed to init ProjectManager: {e}")
            self.project_manager = None

        self.load_projects()

    def load_projects(self):
        if not self.project_manager:
            return

        try:
            while self.flowLayout.count():
                item = self.flowLayout.takeAt(0)
                if hasattr(item, "widget") and callable(getattr(item, "widget")):
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                elif isinstance(item, QWidget):
                    item.deleteLater()

            if self.placeholder:
                self.placeholder.deleteLater()
                self.placeholder = None

            projects = self.project_manager.list_projects()

            if not projects:
                empty_state = EmptyState.library()
                self.placeholder = PlaceholderWidget(
                    empty_state["icon"],
                    empty_state["title"],
                    empty_state["description"],
                    self.view,
                )
                self.placeholder.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding
                )
                self.vBoxLayout.addWidget(self.placeholder, 1)
                return

            projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            cards = []
            for i, p in enumerate(projects):
                card = ProjectCard(p, self.view)
                card.projectClicked.connect(self.on_project_clicked)
                card.projectEditRequested.connect(self.on_project_edit_requested)
                card.projectDeleteRequested.connect(self.on_project_delete_requested)

                # 设置初始透明度为0，但不隐藏卡片
                effect = QGraphicsOpacityEffect(card)
                effect.setOpacity(0)
                card.setGraphicsEffect(effect)

                self.flowLayout.addWidget(card)
                cards.append(card)

            # 依次延迟动画
            for i, card in enumerate(cards):
                QTimer.singleShot(i * 80, lambda c=card: self._animate_card_entry(c))

        except Exception as e:
            print(f"Error loading projects: {e}")
            if self.window():
                self._notify.error("加载失败", str(e))

    def _animate_card_entry(self, card):
        AnimationUtils.pop_in(card, duration=400)

    def show_create_dialog(self):
        dialog = CreateProjectDialog(self.window())
        if dialog.exec():
            data = dialog.get_data()
            try:
                _ = self.project_manager.create_project(
                    name=data["name"],
                    author=data["author"],
                    genre=data["genre"],
                    topic=data["topic"],
                    cover_path=data.get("cover_path"),
                    total_chapters_plan=data["total_chapters_plan"],
                    words_per_chapter_plan=data["words_per_chapter_plan"],
                )
                self.load_projects()
                project_name = data["name"] if data["name"] else "未命名小说"
                self._notify.success("成功", f"项目 '{project_name}' 创建成功")
            except Exception as e:
                self._notify.error("错误", str(e))

    def on_project_clicked(self, path):
        try:
            project_data = self.project_manager.load_project(path)
            self.project_selected.emit(project_data)
        except Exception as e:
            self._notify.error("错误", f"无法加载项目: {e}")

    def on_project_edit_requested(self, project_data):
        dialog = EditProjectDialog(project_data, self.window())
        if dialog.exec():
            data = dialog.get_data()
            project_data.update(data)

            cover_path = data.get("cover_path")
            if cover_path and os.path.exists(cover_path):
                try:
                    ext = os.path.splitext(cover_path)[1]
                    saved_cover_name = f"cover{ext}"
                    saved_cover_path = saved_cover_name
                    shutil.copy2(
                        cover_path, os.path.join(project_data["path"], saved_cover_name)
                    )
                    project_data["cover_image"] = saved_cover_path
                except Exception as e:
                    print(f"Failed to copy cover image: {e}")

            try:
                self.project_manager.save_project_config(
                    project_data["path"], project_data
                )
                self.load_projects()
                self._notify.success("成功", "图书信息已更新")
            except Exception as e:
                self._notify.error("错误", f"保存失败: {e}")

    def on_project_delete_requested(self, project_data):
        name = project_data.get("name", "未命名")
        path = project_data.get("path", "")

        first_dialog = MessageBox(
            "确认删除", f"确定要删除图书《{name}》吗？", self.window()
        )
        if not first_dialog.exec():
            return

        second_dialog = MessageBox(
            "二次确认",
            f"此操作将永久删除《{name}》及其所有内容，无法恢复！\n\n路径: {path}",
            self.window(),
        )
        if not second_dialog.exec():
            return

        try:
            import shutil

            if os.path.exists(path):
                shutil.rmtree(path)
                self.load_projects()
                self._notify.success("成功", f"《{name}》已删除")
            else:
                self._notify.warning("提示", "项目路径不存在")
        except Exception as e:
            self._notify.error("错误", f"删除失败: {e}")
