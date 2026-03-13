# -*- coding: utf-8 -*-
"""
AI Novel Generator - 嵌入式Composer输入组件
=============================================

本模块实现了嵌入到编辑器中的Composer输入组件：
- InlineComposerInputWidget: 嵌入式AI查询输入组件
- 支持平滑展开/收起动画
- 带阴影效果增强视觉层次感
- 点击其他区域自动收起
- 动态扩展编辑器空间，不遮挡文本
"""

from PyQt5.QtCore import (
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    Qt,
    pyqtSignal,
    QTimer,
    QSize,
)
from PyQt5.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QColor, QTextCursor

from ..utils.styles import ThemeManager, isDarkTheme


class InlineComposerInputWidget(QWidget):
    """
    嵌入式Composer AI查询输入组件

    在编辑器选中文本上方动态展开的输入框，通过插入空白行实现真正的嵌入效果，
    不会遮挡其他文本内容。
    """

    query_submitted = pyqtSignal(str)
    ai_level_changed = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, selected_text="", ai_level="standard", parent=None, editor=None):
        """
        初始化嵌入式输入组件

        Args:
            selected_text: 选中的文本
            ai_level: AI等级 (mini/standard/pro)
            parent: 父控件（通常是编辑器的 viewport）
            editor: 关联的编辑器实例
        """
        super().__init__(parent)
        self.selected_text = selected_text
        self.ai_level = ai_level
        self.ai_levels = ["mini", "standard", "pro"]
        self.editor = editor  # 保存编辑器引用

        self.min_height = 44
        self.max_height = 120
        self._expanded_height = 72
        self._inserted_lines = 0  # 记录插入的空行数
        self._original_selection_start = 0
        self._original_selection_end = 0
        self._insert_position = -1  # 插入空行的起始位置（绝对字符位置）
        self._blank_start_position = -1  # 新空白区域的起始位置
        self._is_protecting = False  # 是否正在保护空行（防止递归）

        self._animation_duration = 150
        self._is_expanded = False
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._delayed_close)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setFocusPolicy(Qt.StrongFocus)

        self.init_ui()
        self.setup_shadow()
        self.setup_animations()

    def init_ui(self):
        """初始化用户界面"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_primary = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        text_placeholder = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )
        primary = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        primary_dark = ThemeManager.get_color(ThemeManager.Colors.PRIMARY_DARK, is_dark)
        primary_light = ThemeManager.get_color(
            ThemeManager.Colors.PRIMARY_LIGHT, is_dark
        )
        disabled_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_TERTIARY, is_dark
        )

        self.container = QFrame(self)
        self.container.setObjectName("inlineComposerContainer")
        self.container.setStyleSheet(f"""
            QFrame#inlineComposerContainer {{
                background-color: {bg_color};
                border: 2px solid {primary};
                border-radius: 12px;
            }}
        """)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 8, 12, 8)
        self.container_layout.setSpacing(6)

        self.hint_label = QLabel(
            f'按 "↑↓" 切换模式 (当前: {self.ai_level})，按 "ESC" 关闭'
        )
        self.hint_label.setStyleSheet(f"""
            QLabel {{
                color: {text_placeholder};
                font-size: 12px;
                font-family: Consolas, 'Microsoft YaHei', sans-serif;
                padding: 0px;
            }}
        """)
        self.container_layout.addWidget(self.hint_label)

        self.input_layout = QHBoxLayout()
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        self.input_layout.setSpacing(8)

        self.query_input = QTextEdit(self.container)
        self.query_input.setPlaceholderText("输入您的问题...")
        self.query_input.setAcceptRichText(False)
        self.query_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.query_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.query_input.setMinimumHeight(32)
        self.query_input.setMaximumHeight(80)
        self.query_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_primary};
                font-size: 14px;
                font-family: Consolas, 'Microsoft YaHei', monospace;
            }}
            QTextEdit::placeholder {{
                color: {text_placeholder};
            }}
        """)
        self.query_input.installEventFilter(self)
        self.input_layout.addWidget(self.query_input, 1)

        self.submit_btn = QPushButton("↑", self.container)
        self.submit_btn.setFixedSize(32, 32)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {primary_light};
            }}
            QPushButton:pressed {{
                background-color: {primary_dark};
            }}
            QPushButton:disabled {{
                background-color: {disabled_color};
            }}
        """)
        self.input_layout.addWidget(self.submit_btn)

        self.container_layout.addLayout(self.input_layout)
        self.main_layout.addWidget(self.container)

        self.submit_btn.clicked.connect(self.on_submit)
        self.query_input.textChanged.connect(self.on_text_changed)

        self.setFixedHeight(0)
        # 宽度将根据编辑器动态计算
        self._min_width_ratio = 0.5  # 最小宽度为编辑器的50%
        self._max_width_ratio = 0.85  # 最大宽度为编辑器的85%
        self._preferred_width_ratio = 0.7  # 首选宽度为编辑器的70%
        self.setMinimumWidth(300)  # 绝对最小宽度
        self.setMaximumWidth(800)  # 绝对最大宽度

    def setup_shadow(self):
        """设置阴影效果"""
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setColor(QColor(0, 0, 0, 60))
        self.shadow_effect.setOffset(0, 4)
        self.container.setGraphicsEffect(self.shadow_effect)

    def setup_animations(self):
        """设置展开/收起动画"""
        self.height_animation = QPropertyAnimation(self, b"maximumHeight")
        self.height_animation.setDuration(self._animation_duration)
        self.height_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(self._animation_duration)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)

    def show_at_position(self, global_pos: QPoint, editor_rect):
        """
        在指定位置显示输入框（使用全局坐标）

        Args:
            global_pos: 全局坐标位置（选中文本顶部）
            editor_rect: 编辑器的全局矩形区域
        """
        print(
            f"[DEBUG] show_at_position called: global_pos=({global_pos.x()}, {global_pos.y()})"
        )
        print(
            f"[DEBUG] editor_rect: left={editor_rect.left()}, top={editor_rect.top()}, right={editor_rect.right()}, bottom={editor_rect.bottom()}"
        )
        self._is_expanded = True

        self.query_input.clear()
        self.update_submit_button_state()

        target_height = self._expanded_height
        print(f"[DEBUG] target_height: {target_height}")

        self.height_animation.stop()
        self.height_animation.setStartValue(0)
        self.height_animation.setEndValue(target_height)

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)

        print(f"[DEBUG] Calling show(), raise_()...")
        self.show()
        self.raise_()

        widget_width = self.minimumWidth()
        x = global_pos.x() - widget_width // 2
        y = global_pos.y() - target_height - 8
        print(f"[DEBUG] Initial position: x={x}, y={y}, widget_width={widget_width}")

        if x < editor_rect.left():
            x = editor_rect.left() + 10
        if x + widget_width > editor_rect.right():
            x = editor_rect.right() - widget_width - 10
        if y < editor_rect.top():
            y = editor_rect.top() + 10

        print(f"[DEBUG] Final position: x={x}, y={y}")

        # 转换为相对于父控件的本地坐标
        if self.parent():
            local_pos = self.parent().mapFromGlobal(QPoint(x, y))
            print(
                f"[DEBUG] Local position relative to parent: ({local_pos.x()}, {local_pos.y()})"
            )
            self.move(local_pos)
        else:
            self.move(x, y)

        self.setFixedHeight(target_height)
        print(f"[DEBUG] Widget size: width={self.width()}, height={self.height()}")
        print(f"[DEBUG] Widget visible: {self.isVisible()}")
        print(
            f"[DEBUG] Widget geometry: x={self.x()}, y={self.y()}, w={self.width()}, h={self.height()}"
        )

        self.height_animation.start()
        self.opacity_animation.start()

        QTimer.singleShot(50, self.query_input.setFocus)

    def show_at_local_position(self, local_x: int, local_y: int):
        """
        在指定位置显示输入框（使用相对于父控件的本地坐标）

        输入框将作为编辑器 viewport 的子控件，跟随滚动

        Args:
            local_x: 本地 X 坐标
            local_y: 本地 Y 坐标
        """
        print(f"[DEBUG] show_at_local_position called: ({local_x}, {local_y})")
        self._is_expanded = True

        self.query_input.clear()
        self.update_submit_button_state()

        target_height = self._expanded_height
        print(f"[DEBUG] target_height: {target_height}")

        self.height_animation.stop()
        self.height_animation.setStartValue(0)
        self.height_animation.setEndValue(target_height)

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)

        print(f"[DEBUG] Showing widget at ({local_x}, {local_y})")
        self.move(local_x, local_y)
        self.show()
        self.raise_()
        self.setFixedHeight(target_height)

        print(f"[DEBUG] Widget visible: {self.isVisible()}")
        print(
            f"[DEBUG] Widget geometry: x={self.x()}, y={self.y()}, w={self.width()}, h={self.height()}"
        )

        self.height_animation.start()
        self.opacity_animation.start()

        QTimer.singleShot(50, self.query_input.setFocus)

    def show_embedded_at_selection(self, selection_start: int, selection_end: int):
        """
        在选中文本上方嵌入显示输入框

        通过在选中文本前插入空白行，实现真正的嵌入效果，不遮挡其他文本

        Args:
            selection_start: 选区开始位置
            selection_end: 选区结束位置
        """
        print(
            f"[DEBUG] show_embedded_at_selection: start={selection_start}, end={selection_end}"
        )

        if not self.editor:
            print("[DEBUG] ERROR: editor is None")
            return

        self._original_selection_start = selection_start
        self._original_selection_end = selection_end

        # 计算需要插入的空行数（输入框高度 / 行高）
        cursor = self.editor.textCursor()

        # 获取行高：通过比较两行的 Y 坐标差值
        cursor.movePosition(QTextCursor.Start)
        rect1 = self.editor.cursorRect(cursor)
        cursor.movePosition(QTextCursor.Down)
        rect2 = self.editor.cursorRect(cursor)

        line_height = rect2.y() - rect1.y()
        if line_height <= 0:
            # 如果无法获取行高，使用字体度量
            font_metrics = self.editor.fontMetrics()
            line_height = font_metrics.lineSpacing()
            if line_height <= 0:
                line_height = 20  # 默认行高

        # 计算需要的空行数（输入框高度 + 间距）
        needed_height = self._expanded_height + 16
        self._inserted_lines = max(
            4, (needed_height + line_height - 1) // line_height
        )  # 至少4行
        print(
            f"[DEBUG] line_height={line_height}, needed_height={needed_height}, inserted_lines={self._inserted_lines}"
        )

        # 在选中文本所在行**之前**插入空行
        # 关键：需要在选中文本所在行的上方创建空白区域
        insert_cursor = self.editor.textCursor()
        insert_cursor.setPosition(selection_start)

        # 移动到选中文本所在行的行首
        insert_cursor.movePosition(QTextCursor.StartOfLine)
        actual_insert_pos = insert_cursor.position()

        # 检查是否在文档开头
        if actual_insert_pos == 0:
            # 在文档开头，直接插入空行
            insert_position = 0
        else:
            # 不在文档开头，需要在当前行**之前**插入
            # 方法：在上一行的末尾插入换行符
            # 先移动到上一行
            insert_cursor.movePosition(QTextCursor.Up)
            insert_cursor.movePosition(QTextCursor.EndOfLine)
            insert_position = insert_cursor.position()

        # 记录插入位置
        self._insert_position = insert_position

        # 插入空行
        self._is_protecting = True
        insert_cursor.beginEditBlock()
        newlines = "\n" * self._inserted_lines
        insert_cursor.insertText(newlines)
        insert_cursor.endEditBlock()
        self._is_protecting = False

        print(
            f"[DEBUG] Inserted {self._inserted_lines} lines at position {insert_position}"
        )

        # 计算新空白区域的起始位置
        # 如果在上一行末尾插入，新空白区域从下一行开始
        if actual_insert_pos != 0 and insert_position != 0:
            self._blank_start_position = insert_position + 1
        else:
            self._blank_start_position = insert_position

        print(f"[DEBUG] _blank_start_position: {self._blank_start_position}")

        # 连接文本变化信号，监听用户是否删除空行
        self.editor.textChanged.connect(self._on_editor_text_changed)

        # 更新选区位置（因为插入了空行，选区需要后移）
        new_selection_start = selection_start + self._inserted_lines
        new_selection_end = selection_end + self._inserted_lines

        # 恢复选区
        restore_cursor = self.editor.textCursor()
        restore_cursor.setPosition(new_selection_start)
        restore_cursor.setPosition(new_selection_end, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(restore_cursor)

        # 获取插入空行后的位置（在 viewport 中的位置）
        # 找到新插入空白区域的起始位置
        line_cursor = self.editor.textCursor()
        line_cursor.setPosition(self._blank_start_position)

        # 获取该位置在 viewport 中的矩形
        line_rect = self.editor.cursorRect(line_cursor)

        # 获取空白区域结束位置（选中文本所在行）的矩形
        # 选区位置已经更新了（加上了插入的空行数）
        selection_cursor = self.editor.textCursor()
        selection_cursor.setPosition(new_selection_start)
        selection_rect = self.editor.cursorRect(selection_cursor)

        print(
            f"[DEBUG] line_rect (blank start): x={line_rect.x()}, y={line_rect.y()}, height={line_rect.height()}"
        )
        print(
            f"[DEBUG] selection_rect (blank end): x={selection_rect.x()}, y={selection_rect.y()}, height={selection_rect.height()}"
        )

        # 实际空白区域高度 = 选中文本行顶部 - 空白区域起始位置
        actual_blank_height = selection_rect.y() - line_rect.y()
        print(f"[DEBUG] actual_blank_height (calculated): {actual_blank_height}")
        print(
            f"[DEBUG] expected blank_height (lines * line_height): {self._inserted_lines * line_height}"
        )

        # 计算输入框位置和宽度
        viewport = self.editor.viewport()
        viewport_width = viewport.width()

        # 根据编辑器宽度动态计算输入框宽度
        widget_width = int(viewport_width * self._preferred_width_ratio)
        widget_width = max(int(viewport_width * self._min_width_ratio), widget_width)
        widget_width = min(int(viewport_width * self._max_width_ratio), widget_width)
        widget_width = max(self.minimumWidth(), min(widget_width, self.maximumWidth()))

        # 更新输入框宽度
        self.setFixedWidth(widget_width)

        # 水平居中
        local_x = (viewport_width - widget_width) // 2
        if local_x < 10:
            local_x = 10

        # 使用实际计算的空白区域高度（而不是估算值）
        # blank_area_height = self._inserted_lines * line_height

        # 垂直位置：在空白区域内居中
        # 输入框顶部 = 空白区域顶部 + (空白区域高度 - 输入框高度) / 2
        target_height = self._expanded_height
        vertical_offset = (actual_blank_height - target_height) / 2
        local_y = line_rect.y() + int(vertical_offset)

        # 确保输入框不会超出空白区域底部
        max_local_y = line_rect.y() + actual_blank_height - target_height - 2
        if local_y > max_local_y:
            local_y = max_local_y

        print(f"[DEBUG] viewport_width={viewport_width}, widget_width={widget_width}")
        print(
            f"[DEBUG] actual_blank_height={actual_blank_height}, target_height={target_height}, vertical_offset={vertical_offset}"
        )
        print(
            f"[DEBUG] line_rect.y()={line_rect.y()}, local_y={local_y}, max_local_y={max_local_y}"
        )
        print(f"[DEBUG] Final embedded position: ({local_x}, {local_y})")

        # 详细布局信息
        print(f"[DEBUG] ===== LAYOUT DEBUG =====")

        # 获取上方文字的位置（插入位置前一行）
        above_cursor = self.editor.textCursor()
        above_cursor.setPosition(self._insert_position)
        above_cursor.movePosition(QTextCursor.Up)
        above_rect = self.editor.cursorRect(above_cursor)
        print(f"[DEBUG] 上方文字底部 Y: {above_rect.y() + above_rect.height()}")

        print(f"[DEBUG] 空白区域顶部 Y: {line_rect.y()}")
        print(f"[DEBUG] 空白区域底部 Y: {line_rect.y() + actual_blank_height}")
        print(f"[DEBUG] 选中文本行顶部 Y: {selection_rect.y()}")
        print(
            f"[DEBUG] 选中文本行底部 Y: {selection_rect.y() + selection_rect.height()}"
        )
        print(f"[DEBUG] 输入框顶部 Y: {local_y}")
        print(f"[DEBUG] 输入框底部 Y: {local_y + target_height}")
        print(
            f"[DEBUG] 输入框与上方文字间距: {local_y - above_rect.y() - above_rect.height()}"
        )
        print(
            f"[DEBUG] 输入框与下方文字间距: {selection_rect.y() - (local_y + target_height)}"
        )
        print(f"[DEBUG] =========================")

        self._is_expanded = True
        self.query_input.clear()
        self.update_submit_button_state()

        target_height = self._expanded_height

        self.height_animation.stop()
        self.height_animation.setStartValue(0)
        self.height_animation.setEndValue(target_height)

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)

        self.move(local_x, local_y)
        self.show()
        self.raise_()
        self.setFixedHeight(target_height)

        self.height_animation.start()
        self.opacity_animation.start()

        # 安装事件过滤器，监听编辑器 resize 事件
        if self.editor:
            self.editor.installEventFilter(self)

        QTimer.singleShot(50, self.query_input.setFocus)

    def _on_editor_text_changed(self):
        """
        监听编辑器文本变化，检测用户是否删除了空行

        如果用户删除了空行，自动关闭输入框
        """
        if self._is_protecting or not self._is_expanded:
            return

        if self._insert_position < 0 or self._inserted_lines <= 0:
            return

        # 检查插入位置是否还有足够的空行
        if not self.editor:
            return

        try:
            cursor = self.editor.textCursor()
            cursor.setPosition(self._insert_position)

            # 检查从插入位置开始是否有足够的换行符
            remaining_newlines = 0
            for i in range(self._inserted_lines + 2):  # 多检查几行
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                selected_text = cursor.selectedText()
                if selected_text and selected_text[-1] == "\n":
                    remaining_newlines += 1
                else:
                    break
                cursor.clearSelection()
                cursor.setPosition(self._insert_position + i + 1)

            # 如果空行被删除，关闭输入框
            if remaining_newlines < self._inserted_lines:
                print(
                    f"[DEBUG] User deleted blank lines (expected {self._inserted_lines}, found {remaining_newlines}), closing..."
                )
                self._inserted_lines = remaining_newlines  # 更新剩余空行数
                if remaining_newlines == 0:
                    self._force_close()
        except Exception as e:
            print(f"[DEBUG] Error checking blank lines: {e}")

    def _force_close(self):
        """强制关闭输入框（不删除空行，因为已经被用户删除了）"""
        try:
            self.editor.textChanged.disconnect(self._on_editor_text_changed)
        except Exception:
            pass

        # 移除编辑器事件过滤器
        try:
            if self.editor:
                self.editor.removeEventFilter(self)
        except Exception:
            pass

        self._is_expanded = False
        self._inserted_lines = 0
        self._insert_position = -1
        self._blank_start_position = -1

        self.hide()
        self.closed.emit()

    def collapse(self):
        """平滑收起输入框，并删除插入的空行"""
        # 即使已经收起，也要确保删除空行
        if not self._is_expanded:
            # 仍然需要清理空行（如果有的话）
            if self._inserted_lines > 0 and self._insert_position >= 0:
                print(
                    f"[DEBUG] collapse: already collapsed, but cleaning up remaining lines"
                )
                self._remove_inserted_lines()
            return

        self._is_expanded = False

        # 断开文本变化信号
        try:
            self.editor.textChanged.disconnect(self._on_editor_text_changed)
        except Exception:
            pass

        # 移除编辑器事件过滤器
        try:
            if self.editor:
                self.editor.removeEventFilter(self)
        except Exception:
            pass

        # 删除插入的空行
        self._remove_inserted_lines()

        self.height_animation.stop()
        self.height_animation.setStartValue(self.height())
        self.height_animation.setEndValue(0)

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)

        self.height_animation.finished.connect(self._on_collapse_finished)
        self.height_animation.start()
        self.opacity_animation.start()

    def _remove_inserted_lines(self):
        """删除插入的空行，恢复原文档布局"""
        print(
            f"[DEBUG] _remove_inserted_lines called: editor={self.editor is not None}, _inserted_lines={self._inserted_lines}, _insert_position={self._insert_position}"
        )

        if not self.editor or self._inserted_lines <= 0 or self._insert_position < 0:
            print(f"[DEBUG] _remove_inserted_lines: early return - conditions not met")
            return

        print(
            f"[DEBUG] Removing {self._inserted_lines} inserted lines from position {self._insert_position}"
        )

        try:
            # 直接使用记录的插入位置，不再移动到行首
            # 因为插入位置已经是行首位置
            start_pos = self._insert_position
            print(f"[DEBUG] Using stored insert position: {start_pos}")

            doc = self.editor.document()
            doc_length = doc.characterCount()
            print(f"[DEBUG] Document length: {doc_length}")

            # 检查位置是否有效
            if start_pos >= doc_length:
                print(f"[DEBUG] start_pos >= doc_length, adjusting...")
                start_pos = max(0, doc_length - 1)

            # 找到第 _inserted_lines 个换行符后的位置
            chars_to_delete = 0
            for i in range(self._inserted_lines):
                pos = start_pos + i
                if pos >= doc_length:
                    break
                char = doc.characterAt(pos)
                print(f"[DEBUG] char at {pos}: {repr(char)}")
                if char == "\n" or char == "\u2029":  # \u2029 是段落分隔符
                    chars_to_delete += 1
                else:
                    break

            print(f"[DEBUG] chars_to_delete: {chars_to_delete}")

            if chars_to_delete > 0:
                cursor = self.editor.textCursor()
                cursor.setPosition(start_pos)
                cursor.setPosition(start_pos + chars_to_delete, QTextCursor.KeepAnchor)

                self._is_protecting = True
                cursor.removeSelectedText()
                self._is_protecting = False

                print(f"[DEBUG] Removed {chars_to_delete} newlines successfully")
            else:
                print(f"[DEBUG] No newlines to delete!")

            self._inserted_lines = 0
            self._insert_position = -1
            self._blank_start_position = -1

        except Exception as e:
            print(f"[DEBUG] Error removing lines: {e}")
            import traceback

            traceback.print_exc()

    def _on_collapse_finished(self):
        """收起动画完成"""
        try:
            self.height_animation.finished.disconnect(self._on_collapse_finished)
        except Exception:
            pass
        self.hide()
        self.closed.emit()

    def on_text_changed(self):
        """文本变化时调整高度"""
        doc = self.query_input.document()
        doc_height = doc.size().height()
        new_height = int(doc_height) + 50

        new_height = max(self._expanded_height, min(new_height, self.max_height))

        if new_height != self.height() and self._is_expanded:
            self.setFixedHeight(new_height)

        self.update_submit_button_state()

    def update_width_for_viewport(self):
        """
        根据编辑器 viewport 宽度动态调整输入框宽度

        当编辑器窗口大小变化时调用此方法
        """
        if not self._is_expanded or not self.editor:
            return

        viewport = self.editor.viewport()
        viewport_width = viewport.width()

        # 根据编辑器宽度动态计算输入框宽度
        widget_width = int(viewport_width * self._preferred_width_ratio)
        widget_width = max(int(viewport_width * self._min_width_ratio), widget_width)
        widget_width = min(int(viewport_width * self._max_width_ratio), widget_width)
        widget_width = max(self.minimumWidth(), min(widget_width, self.maximumWidth()))

        # 更新输入框宽度
        self.setFixedWidth(widget_width)

        # 重新计算水平位置（居中）
        local_x = (viewport_width - widget_width) // 2
        if local_x < 10:
            local_x = 10

        # 保持当前垂直位置，只更新水平位置
        self.move(local_x, self.y())

        print(
            f"[DEBUG] Updated width for viewport: viewport_width={viewport_width}, widget_width={widget_width}"
        )

    def update_submit_button_state(self):
        """更新提交按钮状态"""
        text = self.query_input.toPlainText().strip()
        self.submit_btn.setEnabled(bool(text))

    def eventFilter(self, obj, event):
        """
        事件过滤器，捕获键盘事件和编辑器 resize 事件

        Args:
            obj: 事件目标对象
            event: 事件对象

        Returns:
            bool: 是否拦截事件
        """
        # 处理编辑器 resize 事件
        if obj == self.editor and event.type() == QEvent.Resize:
            if self._is_expanded:
                self.update_width_for_viewport()
            return False

        # 处理输入框键盘事件
        if obj == self.query_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.collapse()
                return True
            elif event.key() == Qt.Key_Up:
                self.switch_ai_level(1)
                return True
            elif event.key() == Qt.Key_Down:
                self.switch_ai_level(-1)
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() != Qt.ShiftModifier:
                    self.on_submit()
                    return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """
        键盘事件处理

        Args:
            event: 键盘事件
        """
        if event.key() == Qt.Key_Escape:
            self.collapse()
        elif event.key() == Qt.Key_Up:
            self.switch_ai_level(1)
        elif event.key() == Qt.Key_Down:
            self.switch_ai_level(-1)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() != Qt.ShiftModifier:
                self.on_submit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def switch_ai_level(self, direction: int):
        """
        切换AI等级

        Args:
            direction: 切换方向，1表示向上，-1表示向下
        """
        try:
            current_index = self.ai_levels.index(self.ai_level)
            new_index = (current_index + direction) % len(self.ai_levels)
            self.ai_level = self.ai_levels[new_index]
            self.hint_label.setText(
                f'按 "↑↓" 切换模式 (当前: {self.ai_level})，按 "ESC" 关闭'
            )
            self.ai_level_changed.emit(self.ai_level)
        except ValueError:
            pass

    def on_submit(self):
        """提交查询"""
        query = self.query_input.toPlainText().strip()
        if query:
            self.query_submitted.emit(query)
            self.collapse()

    def focusOutEvent(self, event):
        """
        失去焦点事件处理

        Args:
            event: 焦点事件
        """
        focus_widget = self.parent().focusWidget() if self.parent() else None

        if focus_widget and (focus_widget == self or self.isAncestorOf(focus_widget)):
            return

        self._close_timer.start(100)

    def _delayed_close(self):
        """延迟关闭检查"""
        if not self._is_expanded:
            return

        focus_widget = None
        if self.parent():
            focus_widget = self.parent().focusWidget()

        if focus_widget and (focus_widget == self or self.isAncestorOf(focus_widget)):
            return

        self.collapse()

    def is_expanded(self) -> bool:
        """
        检查输入框是否展开

        Returns:
            bool: 是否展开
        """
        return self._is_expanded

    def set_selected_text(self, text: str):
        """
        设置选中的文本

        Args:
            text: 选中的文本
        """
        self.selected_text = text

    def set_ai_level(self, level: str):
        """
        设置AI等级

        Args:
            level: AI等级 (mini/standard/pro)
        """
        if level in self.ai_levels:
            self.ai_level = level
            self.hint_label.setText(
                f'按 "↑↓" 切换模式 (当前: {self.ai_level})，按 "ESC" 关闭'
            )
