# -*- coding: utf-8 -*-
"""
封面编辑器对话框组件

================================================================================
模块功能概述
================================================================================
本模块提供了一个专业的封面图片编辑对话框，支持：
1. 图片加载和预览
2. 拖拽调整图片在裁剪框内的位置
3. 固定尺寸裁剪区域（长方形）
4. 半透明覆盖效果，突出显示裁剪区域
5. 撤销/重做功能
6. 精美的UI设计和流畅的交互体验

================================================================================
设计决策
================================================================================
- 使用QPainter绘制图片和覆盖层，确保性能优化
- 采用状态栈实现撤销/重做功能
- 支持鼠标拖拽和键盘操作
- 使用qfluentwidgets提供现代化UI组件
- 裁剪区域固定为2:3的长宽比（标准书籍封面比例）

================================================================================
依赖模块
================================================================================
- PyQt5: Qt框架的Python绑定，提供GUI功能
- qfluentwidgets: Fluent Design风格的Qt控件库
- PIL (Pillow): 图像处理库
"""

import os
from typing import Optional

from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    MessageBoxBase,
    SubtitleLabel,
    ToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from ..utils.dialog_sizer import DialogSizer
from ..utils.styles import ThemeManager


class CoverEditorState:
    """封面编辑器状态类，用于实现撤销/重做功能"""

    def __init__(self, offset: QPointF, scale: float):
        """
        初始化状态对象

        参数:
            offset: 图片相对于裁剪框中心的偏移量
            scale: 图片缩放比例
        """
        self.offset = QPointF(offset)
        self.scale = scale


class CoverEditorCanvas(QWidget):
    """封面编辑画布组件"""

    def __init__(self, parent=None):
        """
        初始化封面编辑画布

        参数:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self.setMinimumSize(400, 500)
        self.setMouseTracking(True)

        self._pixmap: Optional[QPixmap] = None
        self._original_pixmap: Optional[QPixmap] = None
        self._offset = QPointF(0, 0)
        self._scale = 1.0
        self._is_dragging = False
        self._last_drag_pos = QPoint()

        self._crop_width = 200
        self._crop_height = 300
        self._min_scale = 0.1
        self._max_scale = 5.0

        self._state_stack: list[CoverEditorState] = []
        self._current_state_index = -1
        self._save_state()

    def set_image(self, image_path: str) -> bool:
        """
        设置要编辑的图片

        参数:
            image_path: 图片文件路径

        返回值:
            成功加载返回True，否则返回False
        """
        if not os.path.exists(image_path):
            return False

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False

        self._original_pixmap = pixmap
        self._pixmap = pixmap

        self._fit_image()
        self._state_stack = []
        self._current_state_index = -1
        self._save_state()
        self.update()
        return True

    def _fit_image(self):
        """自动调整图片大小以适应裁剪框"""
        if not self._pixmap:
            return

        pixmap_size = self._pixmap.size()
        crop_ratio = self._crop_width / self._crop_height
        pixmap_ratio = pixmap_size.width() / pixmap_size.height()

        if pixmap_ratio > crop_ratio:
            self._scale = self._crop_height / pixmap_size.height()
        else:
            self._scale = self._crop_width / pixmap_size.width()

        self._offset = QPointF(0, 0)

    def _save_state(self):
        """保存当前状态到状态栈"""
        state = CoverEditorState(self._offset, self._scale)

        if self._current_state_index < len(self._state_stack) - 1:
            self._state_stack = self._state_stack[: self._current_state_index + 1]

        self._state_stack.append(state)
        self._current_state_index = len(self._state_stack) - 1

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self._current_state_index > 0

    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return self._current_state_index < len(self._state_stack) - 1

    def undo(self):
        """撤销上一步操作"""
        if self.can_undo():
            self._current_state_index -= 1
            self._restore_state()

    def redo(self):
        """重做上一步撤销的操作"""
        if self.can_redo():
            self._current_state_index += 1
            self._restore_state()

    def _restore_state(self):
        """恢复指定状态"""
        if 0 <= self._current_state_index < len(self._state_stack):
            state = self._state_stack[self._current_state_index]
            self._offset = QPointF(state.offset)
            self._scale = state.scale
            self.update()

    def _get_crop_rect(self) -> QRectF:
        """获取裁剪区域在画布上的矩形"""
        canvas_center_x = self.width() / 2
        canvas_center_y = self.height() / 2

        x = canvas_center_x - self._crop_width / 2
        y = canvas_center_y - self._crop_height / 2

        return QRectF(x, y, self._crop_width, self._crop_height)

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        self._draw_background(painter)

        if self._pixmap:
            self._draw_image(painter)

        self._draw_overlay(painter)
        self._draw_crop_border(painter)

    def _draw_background(self, painter: QPainter):
        """绘制棋盘格背景"""
        tile_size = 20
        bg_secondary = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY)
        bg_primary = ThemeManager.get_color(ThemeManager.Colors.BG_PRIMARY)
        for i in range(0, self.width(), tile_size):
            for j in range(0, self.height(), tile_size):
                if (i // tile_size + j // tile_size) % 2 == 0:
                    color = QColor(bg_secondary)
                else:
                    color = QColor(bg_primary)
                painter.fillRect(i, j, tile_size, tile_size, color)

    def _draw_image(self, painter: QPainter):
        """绘制图片"""
        crop_rect = self._get_crop_rect()

        scaled_width = self._pixmap.width() * self._scale
        scaled_height = self._pixmap.height() * self._scale

        image_center_x = crop_rect.center().x() + self._offset.x()
        image_center_y = crop_rect.center().y() + self._offset.y()

        image_x = image_center_x - scaled_width / 2
        image_y = image_center_y - scaled_height / 2

        painter.drawPixmap(
            int(image_x),
            int(image_y),
            int(scaled_width),
            int(scaled_height),
            self._pixmap,
        )

    def _draw_overlay(self, painter: QPainter):
        """绘制半透明覆盖层，突出裁剪区域"""
        crop_rect = self._get_crop_rect()

        overlay_color = QColor(0, 0, 0, 150)

        top_rect = QRectF(0, 0, self.width(), crop_rect.top())
        bottom_rect = QRectF(
            0, crop_rect.bottom(), self.width(), self.height() - crop_rect.bottom()
        )
        left_rect = QRectF(0, crop_rect.top(), crop_rect.left(), crop_rect.height())
        right_rect = QRectF(
            crop_rect.right(),
            crop_rect.top(),
            self.width() - crop_rect.right(),
            crop_rect.height(),
        )

        painter.fillRect(top_rect, overlay_color)
        painter.fillRect(bottom_rect, overlay_color)
        painter.fillRect(left_rect, overlay_color)
        painter.fillRect(right_rect, overlay_color)

    def _draw_crop_border(self, painter: QPainter):
        """绘制裁剪区域边框"""
        crop_rect = self._get_crop_rect()

        border_color = QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_INVERTED))
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(crop_rect)

        corner_size = 15
        corner_pen = QPen(border_color, 3)
        painter.setPen(corner_pen)

        top_left = crop_rect.topLeft()
        top_right = crop_rect.topRight()
        bottom_left = crop_rect.bottomLeft()
        bottom_right = crop_rect.bottomRight()

        painter.drawLine(top_left, top_left + QPoint(corner_size, 0))
        painter.drawLine(top_left, top_left + QPoint(0, corner_size))

        painter.drawLine(top_right, top_right - QPoint(corner_size, 0))
        painter.drawLine(top_right, top_right + QPoint(0, corner_size))

        painter.drawLine(bottom_left, bottom_left + QPoint(corner_size, 0))
        painter.drawLine(bottom_left, bottom_left - QPoint(0, corner_size))

        painter.drawLine(bottom_right, bottom_right - QPoint(corner_size, 0))
        painter.drawLine(bottom_right, bottom_right - QPoint(0, corner_size))

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton and self._pixmap:
            self._is_dragging = True
            self._last_drag_pos = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._is_dragging and self._pixmap:
            delta = event.pos() - self._last_drag_pos
            self._offset += QPointF(delta)
            self._last_drag_pos = event.pos()
            self.update()
        elif self._pixmap:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.setCursor(QCursor(Qt.OpenHandCursor))
            self._save_state()

    def wheelEvent(self, event):
        """滚轮事件，用于缩放图片"""
        if not self._pixmap:
            return

        delta = event.angleDelta().y()
        scale_factor = 1.0 + delta / 1200.0

        new_scale = self._scale * scale_factor
        new_scale = max(self._min_scale, min(self._max_scale, new_scale))

        if new_scale != self._scale:
            self._scale = new_scale
            self.update()
            self._save_state()

    def reset(self):
        """重置图片位置和缩放"""
        if self._pixmap:
            self._fit_image()
            self._save_state()
            self.update()

    def get_cropped_pixmap(self) -> Optional[QPixmap]:
        """
        获取裁剪后的图片

        返回值:
            裁剪后的QPixmap对象，如果没有图片则返回None
        """
        if not self._pixmap:
            return None

        result = QPixmap(self._crop_width, self._crop_height)
        result.fill(QColor(ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY)))

        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        scaled_width = self._pixmap.width() * self._scale
        scaled_height = self._pixmap.height() * self._scale

        target_x = (self._crop_width - scaled_width) / 2 + self._offset.x()
        target_y = (self._crop_height - scaled_height) / 2 + self._offset.y()

        painter.drawPixmap(
            int(target_x),
            int(target_y),
            int(scaled_width),
            int(scaled_height),
            self._pixmap,
        )

        painter.end()

        if result.isNull():
            return None

        return result


class CoverEditorDialog(MessageBoxBase):
    """
    封面编辑器对话框
    支持尺寸自适应。
    """

    cover_selected = pyqtSignal(str)

    def __init__(self, initial_image_path: str = "", parent=None):
        """
        初始化封面编辑器对话框

        参数:
            initial_image_path: 初始图片路径
            parent: 父窗口对象
        """
        super().__init__(parent)
        self._initial_image_path = initial_image_path
        self._temp_cover_path: Optional[str] = None

        self._setup_ui()
        self._setup_connections()

        if initial_image_path and os.path.exists(initial_image_path):
            self._load_image(initial_image_path)

    def _setup_ui(self):
        """设置UI界面"""
        self.titleLabel = SubtitleLabel("封面编辑器", self)

        self._canvas = CoverEditorCanvas(self)
        self._canvas.setMinimumSize(400, 520)

        self._hint_label = CaptionLabel(
            "💡 提示：拖拽图片调整位置，滚轮缩放，角落标记为裁剪区域",
            self,
        )
        self._hint_label.setWordWrap(True)

        self._toolbar = QWidget(self)
        self._toolbar_layout = QHBoxLayout(self._toolbar)
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.setSpacing(8)

        self._browse_btn = ToolButton(FIF.PHOTO, self)
        self._browse_btn.setToolTip("选择图片")

        self._undo_btn = ToolButton(FIF.LEFT_ARROW, self)
        self._undo_btn.setToolTip("撤销")
        self._undo_btn.setEnabled(False)

        self._redo_btn = ToolButton(FIF.RIGHT_ARROW, self)
        self._redo_btn.setToolTip("重做")
        self._redo_btn.setEnabled(False)

        self._reset_btn = ToolButton(FIF.SYNC, self)
        self._reset_btn.setToolTip("重置")

        self._toolbar_layout.addWidget(self._browse_btn)
        self._toolbar_layout.addWidget(self._undo_btn)
        self._toolbar_layout.addWidget(self._redo_btn)
        self._toolbar_layout.addWidget(self._reset_btn)
        self._toolbar_layout.addStretch(1)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self._toolbar)
        self.viewLayout.addWidget(self._canvas)
        self.viewLayout.addWidget(self._hint_label)

        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")

        sizer = DialogSizer(
            width_ratio=0.40,
            height_ratio=0.65,
            min_width=450,
            min_height=550,
            max_width=600,
        )
        sizer.apply_to_widget(self.widget, self.parent())

    def _setup_connections(self):
        """设置信号连接"""
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        self._undo_btn.clicked.connect(self._on_undo_clicked)
        self._redo_btn.clicked.connect(self._on_redo_clicked)
        self._reset_btn.clicked.connect(self._on_reset_clicked)

        self.yesButton.clicked.connect(self._on_confirm_clicked)

    def _load_image(self, image_path: str):
        """加载图片到编辑器"""
        if self._canvas.set_image(image_path):
            self._update_buttons()

    def _on_browse_clicked(self):
        """浏览按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择封面图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if file_path:
            self._load_image(file_path)

    def _on_undo_clicked(self):
        """撤销按钮点击事件"""
        self._canvas.undo()
        self._update_buttons()

    def _on_redo_clicked(self):
        """重做按钮点击事件"""
        self._canvas.redo()
        self._update_buttons()

    def _on_reset_clicked(self):
        """重置按钮点击事件"""
        self._canvas.reset()
        self._update_buttons()

    def _update_buttons(self):
        """更新按钮状态"""
        self._undo_btn.setEnabled(self._canvas.can_undo())
        self._redo_btn.setEnabled(self._canvas.can_redo())

    def _on_confirm_clicked(self):
        """确认按钮点击事件"""
        cropped_pixmap = self._canvas.get_cropped_pixmap()
        if cropped_pixmap and not cropped_pixmap.isNull():
            import tempfile
            import uuid

            temp_dir = tempfile.gettempdir()
            temp_filename = f"cover_editor_{uuid.uuid4().hex}.png"
            temp_path = os.path.join(temp_dir, temp_filename)

            save_success = cropped_pixmap.save(temp_path, "PNG")
            if save_success and os.path.exists(temp_path):
                self._temp_cover_path = temp_path
            else:
                print(f"Failed to save cover to: {temp_path}")

    def get_result(self) -> Optional[str]:
        """
        获取编辑结果

        返回值:
            临时文件路径，如果用户取消或没有图片则返回None
        """
        return self._temp_cover_path
