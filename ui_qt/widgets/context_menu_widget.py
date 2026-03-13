# -*- coding: utf-8 -*-
"""
AI Novel Generator - 文本选择上下文菜单模块
=========================================

本模块实现了文本编辑器的选择上下文菜单功能：
- SelectionContextMenu: 文本选择悬浮菜单
- 支持基础操作（复制、粘贴）
- 支持文本优化（修复语法错误、润色）
- 支持内容扩展（心理、神态、动作、环境等）
- 支持AI交互（询问Composer）
"""

from PyQt5.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF

from ui_qt.utils.styles import ThemeManager, isDarkTheme


class MenuItemWidget(QWidget):
    """
    菜单项组件，包含图标和文本

    采用按钮式交互设计，整行可点击和悬停高亮
    """

    clicked = pyqtSignal()
    hovered = pyqtSignal(bool)

    def __init__(self, icon, text, has_submenu=False, parent=None):
        """
        初始化菜单项

        Args:
            icon: 菜单图标
            text: 菜单文本
            has_submenu: 是否有子菜单
            parent: 父控件
        """
        super().__init__(parent)
        self.has_submenu = has_submenu
        self.is_hovered = False
        self.setObjectName("menuItemWidget")
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(12)

        from qfluentwidgets import TransparentToolButton

        self.icon_btn = TransparentToolButton(icon, self)
        self.icon_btn.setFixedSize(28, 28)
        self.icon_btn.setIconSize(QSize(18, 18))
        self.icon_btn.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.icon_btn)

        self.text_label = QLabel(text)
        self.text_label.setObjectName("menuItemText")
        self.text_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        layout.addWidget(self.text_label)

        layout.addStretch()

        if self.has_submenu:
            self.arrow_label = QLabel("›")
            self.arrow_label.setObjectName("menuItemArrow")
            self.arrow_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            layout.addWidget(self.arrow_label)

        self.update_colors()
        self.update_style()

    def update_colors(self):
        """根据主题更新颜色"""
        self.update_style()

    def update_style(self):
        """更新样式（包括悬停状态和主题颜色）"""
        is_dark = isDarkTheme()

        if self.is_hovered:
            hover_bg = ThemeManager.get_color(
                ThemeManager.Colors.LIST_ITEM_HOVER, is_dark
            )
            self.setStyleSheet(f"background-color: {hover_bg}; border-radius: 6px;")
        else:
            self.setStyleSheet("background-color: transparent; border-radius: 6px;")

        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        self.text_label.setStyleSheet(
            f"color: {text_color}; font-size: 14px; font-weight: 500;"
        )
        if hasattr(self, "arrow_label"):
            self.arrow_label.setStyleSheet(
                f"color: {text_color}; font-size: 20px; font-weight: bold;"
            )

    def enterEvent(self, event):
        """鼠标进入时设置悬停样式"""
        self.is_hovered = True
        self.update_style()
        self.hovered.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清除悬停样式"""
        self.is_hovered = False
        self.update_style()
        self.hovered.emit(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下时触发点击信号"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SelectionContextMenu(QWidget):
    """
    文本选择悬浮菜单组件

    当用户选中文本时显示的上下文菜单，提供：
    - 基础操作：复制、粘贴
    - 文本优化：修复语法错误、润色
    - 内容扩展：心理、神态、动作、环境描写
    - AI交互：询问Composer
    """

    copy_clicked = pyqtSignal()
    paste_clicked = pyqtSignal()
    fix_grammar_clicked = pyqtSignal(str)
    polish_clicked = pyqtSignal(str)
    expand_clicked = pyqtSignal(str, str)
    ask_composer_clicked = pyqtSignal(str)

    def __init__(self, editor, parent=None):
        """
        初始化选择上下文菜单（预加载优化版）

        Args:
            editor: 关联的文本编辑器
            parent: 父控件
        """
        super().__init__(parent)
        self.editor = editor
        self.selected_text = ""
        self.expand_menu = None
        self.expand_menu_timer = QTimer(self)
        self.expand_menu_timer.setSingleShot(True)
        self.expand_menu_timer.timeout.connect(self.hide_expand_menu)
        self.expand_menu_visible = False
        self._expand_menu_created = False
        self._menu_items = []

        # 添加鼠标位置检查计时器（增加间隔以减少开销）
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)

        self.setObjectName("selectionContextMenu")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        self.setup_animations()

        # 预创建扩展菜单，避免首次显示时的延迟
        self.create_expand_menu()
        self._expand_menu_created = True

    def init_ui(self):
        """初始化用户界面"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 主容器卡片
        self.container = QFrame(self)
        self.container.setObjectName("contextMenuContainer")

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(4)
        self.container_layout.setContentsMargins(8, 8, 8, 8)

        # 创建菜单项
        self.copy_item = MenuItemWidget(FIF.COPY, "复制")
        self.copy_item.clicked.connect(self.on_copy)
        self.container_layout.addWidget(self.copy_item)
        self._menu_items.append(self.copy_item)

        self.paste_item = MenuItemWidget(FIF.PASTE, "粘贴")
        self.paste_item.clicked.connect(self.on_paste)
        self.container_layout.addWidget(self.paste_item)
        self._menu_items.append(self.paste_item)

        # 分隔线
        self.add_separator()

        self.fix_grammar_item = MenuItemWidget(FIF.EDIT, "修复语法")
        self.fix_grammar_item.clicked.connect(self.on_fix_grammar)
        self.container_layout.addWidget(self.fix_grammar_item)
        self._menu_items.append(self.fix_grammar_item)

        self.polish_item = MenuItemWidget(FIF.IOT, "润色")
        self.polish_item.clicked.connect(self.on_polish)
        self.container_layout.addWidget(self.polish_item)
        self._menu_items.append(self.polish_item)

        # 分隔线
        self.add_separator()

        self.expand_item = MenuItemWidget(FIF.ADD, "扩展描写", has_submenu=True)
        self.expand_item.hovered.connect(self.on_expand_hovered)
        self.container_layout.addWidget(self.expand_item)
        self._menu_items.append(self.expand_item)

        # 分隔线
        self.add_separator()

        self.ask_composer_item = MenuItemWidget(FIF.CHAT, "询问 Composer")
        self.ask_composer_item.clicked.connect(self.on_ask_composer)
        self.container_layout.addWidget(self.ask_composer_item)
        self._menu_items.append(self.ask_composer_item)

        self.main_layout.addWidget(self.container)
        self.update_colors()
        self.setFixedWidth(200)

    def add_separator(self):
        """添加分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        is_dark = isDarkTheme()
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {border_color};
                border: none;
                margin: 4px 16px;
            }}
        """)
        self.container_layout.addWidget(separator)

    def update_colors(self):
        """根据主题更新菜单颜色"""
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )

        self.container.setStyleSheet(f"""
            QFrame#contextMenuContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)

        for i in range(self.container_layout.count()):
            item = self.container_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, "update_style"):
                    widget.update_style()

    def create_expand_menu(self):
        """创建扩展描写子菜单"""
        self.expand_menu = QMenu(self)
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.LIST_ITEM_HOVER, is_dark)

        self.expand_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 12px 20px;
                border-radius: 6px;
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                margin: 2px 0px;
            }}
            QMenu::item:selected {{
                background-color: {hover_bg};
            }}
            QMenu::item:hover {{
                background-color: {hover_bg};
            }}
        """)

        # 连接子菜单关闭信号
        self.expand_menu.aboutToHide.connect(self.on_expand_menu_hide)

        # 添加扩展类型选项
        expand_types = [
            ("心理描写", "psychological"),
            ("神态描写", "expression"),
            ("动作描写", "action"),
            ("环境描写", "environment"),
            ("对话补充", "dialogue"),
        ]

        for name, type_id in expand_types:
            action = self.expand_menu.addAction(name)
            action.triggered.connect(lambda checked, t=type_id: self.on_expand(t))

    def on_expand_menu_hide(self):
        """子菜单关闭时重置可见性标志"""
        self.expand_menu_visible = False

    def on_expand_hovered(self):
        """当鼠标悬停在扩展描写项上时显示子菜单"""
        self.expand_menu_timer.stop()
        if not self._expand_menu_created:
            QTimer.singleShot(0, self._create_expand_menu_delayed)

        if self.expand_menu and not self.expand_menu_visible:
            pos = self.expand_item.mapToGlobal(QPoint(self.expand_item.width(), -4))
            self.expand_menu.popup(pos)
            self.expand_menu_visible = True

    def _create_expand_menu_delayed(self):
        """延迟创建扩展菜单，避免阻塞UI"""
        if not self._expand_menu_created:
            self.create_expand_menu()
            self._expand_menu_created = True

    def hide_expand_menu(self):
        """隐藏扩展描写子菜单"""
        if self.expand_menu and self.expand_menu.isVisible():
            self.expand_menu.hide()
        self.expand_menu_visible = False

    def enterEvent(self, event):
        """当鼠标进入主菜单时停止隐藏计时器"""
        self.expand_menu_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """当鼠标离开菜单时启动计时器隐藏子菜单"""
        # 启动计时器，但会被 check_mouse_position 检查
        self.expand_menu_timer.start(300)
        super().leaveEvent(event)

    def check_mouse_position(self):
        """
        定期检查鼠标位置，决定是否保持子菜单显示

        同时同步各菜单项的hover状态，修复快速移动鼠标时
        可能出现的多个按钮同时高亮的bug
        """
        global_pos = QCursor.pos()

        # 同步所有菜单项的hover状态
        self._sync_menu_items_hover(global_pos)

        if not self.expand_menu or not self.expand_menu.isVisible():
            return

        # 检查鼠标是否在子菜单区域内
        if self.expand_menu.geometry().contains(global_pos):
            self.expand_menu_timer.stop()
            return

        # 检查鼠标是否还在"扩展描写"项上
        expand_item_global_rect = self.expand_item.mapToGlobal(QPoint(0, 0))
        expand_item_rect = self.expand_item.rect().translated(
            expand_item_global_rect.x(), expand_item_global_rect.y()
        )
        if expand_item_rect.contains(global_pos):
            self.expand_menu_timer.stop()
            return

        # 鼠标不在扩展描写项和子菜单上，隐藏子菜单
        self.hide_expand_menu()

    def _sync_menu_items_hover(self, global_pos):
        """
        同步所有菜单项的hover状态

        Args:
            global_pos: 鼠标全局坐标

        解决问题：
            当鼠标快速移动或子菜单弹出时，Qt的enterEvent/leaveEvent
            可能不会正确触发，导致多个菜单项同时显示hover状态。
            此方法通过定期检查鼠标位置来强制同步状态。
        """
        for item in self._menu_items:
            if not item.isVisible():
                continue

            item_global_pos = item.mapToGlobal(QPoint(0, 0))
            item_rect = item.rect().translated(item_global_pos.x(), item_global_pos.y())

            should_hover = item_rect.contains(global_pos)

            if should_hover != item.is_hovered:
                item.is_hovered = should_hover
                item.update_style()

    def setup_animations(self):
        """设置动画效果"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(50)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def show_at_selection(self):
        """
        在选中文本附近显示菜单

        智能调整菜单位置，确保菜单不会超出屏幕边界：
        - 优先在选中文本下方显示
        - 如果下方空间不足，则在上方显示
        - 如果右侧空间不足，则向左调整
        - 如果左侧空间不足，则向右调整
        """
        cursor = self.editor.textCursor()
        self.selected_text = cursor.selectedText()

        if not self.selected_text:
            return

        try:
            self.animation.stop()
        except Exception:
            pass

        try:
            self.animation.finished.disconnect()
        except Exception:
            pass

        rect = self.editor.cursorRect(cursor)
        pos = self.editor.mapToGlobal(rect.center())

        self.setWindowOpacity(1.0)
        self.show()

        self.adjust_position_to_screen(pos)

    def adjust_position_to_screen(self, pos):
        """
        智能调整菜单位置，确保菜单不会超出屏幕边界

        参数:
            pos: 初始位置点（QPoint）

        返回值:
            无

        设计说明:
            - 优先在选中文本下方显示菜单
            - 如果下方空间不足，则在上方显示
            - 如果右侧空间不足，则向左调整
            - 如果左侧空间不足，则向右调整
            - 保持与屏幕边缘至少10像素的安全距离
        """
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QScreen

        menu_width = self.width()
        menu_height = self.height()

        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()

        if not screen:
            self.move(pos)
            return

        screen_geometry = screen.availableGeometry()
        screen_left = screen_geometry.left()
        screen_right = screen_geometry.right()
        screen_top = screen_geometry.top()
        screen_bottom = screen_geometry.bottom()

        margin = 10

        x = pos.x() - menu_width // 2
        y = pos.y() + 20

        if x + menu_width + margin > screen_right:
            x = screen_right - menu_width - margin
        if x < screen_left + margin:
            x = screen_left + margin

        if y + menu_height + margin > screen_bottom:
            y = pos.y() - menu_height - 10
            if y < screen_top + margin:
                y = screen_top + margin

        self.move(int(x), int(y))

    def on_copy(self):
        """复制按钮点击"""
        self.copy_clicked.emit()
        self.hide_with_animation()

    def on_paste(self):
        """粘贴按钮点击"""
        self.paste_clicked.emit()
        self.hide_with_animation()

    def on_fix_grammar(self):
        """修复语法按钮点击"""
        if self.selected_text:
            self.fix_grammar_clicked.emit(self.selected_text)
            self.hide_with_animation()

    def on_polish(self):
        """润色按钮点击"""
        if self.selected_text:
            self.polish_clicked.emit(self.selected_text)
            self.hide_with_animation()

    def on_expand(self, expand_type):
        """
        扩展描写按钮点击

        Args:
            expand_type: 扩展类型
        """
        if self.selected_text:
            self.expand_clicked.emit(self.selected_text, expand_type)
            self.hide_with_animation()

    def on_ask_composer(self):
        """询问Composer按钮点击"""
        if self.selected_text:
            self.ask_composer_clicked.emit(self.selected_text)
            self.hide_with_animation()

    def hide(self):
        """隐藏主菜单，同时确保子菜单也被隐藏"""
        self.expand_menu_timer.stop()
        if self.expand_menu:
            self.expand_menu.hide()
        self.expand_menu_visible = False
        super().hide()

    def hide_with_animation(self):
        """带动画的隐藏"""
        if self.expand_menu:
            self.expand_menu.hide()
        self.expand_menu_visible = False

        # 先断开之前的连接，避免多次触发
        try:
            self.animation.finished.disconnect()
        except Exception:
            pass

        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def keyPressEvent(self, event):
        """
        键盘事件处理

        Args:
            event: 键盘事件
        """
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        """
        失去焦点时隐藏

        Args:
            event: 焦点事件
        """
        # 延迟检查，避免瞬时焦点变化
        QTimer.singleShot(300, lambda: self.check_focus(event))

    def check_focus(self, event):
        """检查是否还需要保持焦点"""
        # 检查焦点是否在编辑器上（父控件）
        focus_widget = self.focusWidget()

        # 如果焦点在编辑器上，保持菜单显示
        if focus_widget == self.editor or self.editor.isAncestorOf(focus_widget):
            return

        # 如果焦点在菜单本身或其子控件上，保持显示
        if self.hasFocus() or self.isAncestorOf(focus_widget):
            return

        # 如果焦点在扩展菜单上，保持显示
        if self.expand_menu and (
            focus_widget == self.expand_menu
            or self.expand_menu.isAncestorOf(focus_widget)
        ):
            return

        # 否则隐藏菜单
        self.hide()
