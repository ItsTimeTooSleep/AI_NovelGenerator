# -*- coding: utf-8 -*-
"""
AI Novel Generator - 动画工具模块
==================================

本模块提供常用的 UI 动画效果工具类：
- 淡入动画
- 滑入动画
- 扫描高光动画
- 布局项依次动画

主要组件：
- AnimationUtils: 动画工具类，包含静态方法
- StepProgressContainer: 步骤进度容器（包含左侧连续线）
- StepProgressWidget: 单个步骤进度组件
"""

import math

from PyQt5.QtCore import (
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QGraphicsOpacityEffect,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import (
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)

from .styles import Styles, ThemeManager


def create_simple_arrow_icon(direction="up", size=14):
    """
    创建简化的单头箭头图标

    Args:
        direction: 箭头方向 ('up' 或 'down')
        size: 图标大小

    Returns:
        QIcon: 简化的箭头图标
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY))
    painter.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(color)

    # 绘制只有一个头的简化箭头
    center = size // 2
    padding = 2
    arrow_size = size - padding * 2

    if direction == "up":
        # 向上箭头（类似 Chevron，但更简单）
        points = [
            QPoint(center, padding),
            QPoint(padding + arrow_size, size - padding),
            QPoint(padding, size - padding),
        ]
    else:  # down
        # 向下箭头
        points = [
            QPoint(center, size - padding),
            QPoint(padding + arrow_size, padding),
            QPoint(padding, padding),
        ]

    painter.drawPolygon(points)
    painter.end()

    return QIcon(pixmap)


class PulseLabel(QWidget):
    """
    带脉冲动画效果的标签组件

    显示文本标签，并在激活状态下显示从左往右流动的脉冲光效动画。
    光效仅作用于文字本身，使用QPainterPath剪裁实现。
    """

    def __init__(self, text: str = "", parent=None):
        """
        初始化脉冲标签

        Args:
            text: 标签文本
            parent: 父控件
        """
        super().__init__(parent)
        self._text = text
        self._light_pos = 0.0
        self._is_pulsing = False
        self._text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY)
        self._pulse_color = ThemeManager.get_color(ThemeManager.Colors.STEP_ACTIVE)

        self._pulse_animation = QPropertyAnimation(self, b"lightPos", self)
        self._pulse_animation.setStartValue(-0.3)
        self._pulse_animation.setEndValue(1.3)
        self._pulse_animation.setDuration(2000)
        self._pulse_animation.setLoopCount(-1)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(24)

    def text(self) -> str:
        """
        获取标签文本

        Returns:
            str: 标签文本
        """
        return self._text

    def setText(self, text: str):
        """
        设置标签文本

        Args:
            text: 要设置的文本
        """
        self._text = text
        self.update()
        self.updateGeometry()

    def setTextColor(self, color: str):
        """
        设置文本颜色

        Args:
            color: 颜色值（十六进制字符串）
        """
        self._text_color = color
        self.update()

    def setPulseColor(self, color: str):
        """
        设置脉冲颜色

        Args:
            color: 颜色值（十六进制字符串）
        """
        self._pulse_color = color
        self.update()

    def getLightPos(self) -> float:
        """
        获取光条位置

        Returns:
            float: 光条位置
        """
        return self._light_pos

    def setLightPos(self, pos: float):
        """
        设置光条位置

        Args:
            pos: 光条位置
        """
        self._light_pos = pos
        self.update()

    lightPos = pyqtProperty(float, getLightPos, setLightPos)

    def startPulse(self):
        """
        开始脉冲动画

        参数:
            无

        返回值:
            无
        """
        if not self._is_pulsing:
            self._is_pulsing = True
            self._pulse_animation.start()

    def stopPulse(self):
        """
        停止脉冲动画

        参数:
            无

        返回值:
            无
        """
        if self._is_pulsing:
            self._is_pulsing = False
            self._pulse_animation.stop()
            self._light_pos = -0.3
            self.update()

    def isPulsing(self) -> bool:
        """
        检查是否正在脉冲

        Returns:
            bool: 是否正在脉冲
        """
        return self._is_pulsing

    def sizeHint(self):
        """
        获取推荐尺寸

        Returns:
            QSize: 推荐尺寸
        """
        from PyQt5.QtGui import QFontMetrics, QFont

        font = QFont()
        font.setPixelSize(15)
        font.setWeight(QFont.DemiBold)
        fm = QFontMetrics(font)
        return QSize(fm.horizontalAdvance(self._text) + 20, max(fm.height() + 4, 24))

    def paintEvent(self, event):
        """
        绘制事件

        Args:
            event: 绘制事件
        """
        from PyQt5.QtGui import QFont, QFontMetrics, QPainterPath, QBrush

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        if not self._text:
            return

        font = QFont()
        font.setPixelSize(15)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)

        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._text)
        text_height = fm.height()

        text_rect = self.rect()

        y_offset = (self.height() - text_height) // 2 + fm.ascent()

        text_color = QColor(self._text_color)
        painter.setPen(text_color)
        painter.drawText(0, y_offset, self._text)

        if self._is_pulsing:
            path = QPainterPath()
            path.addText(0, y_offset, font, self._text)
            painter.setClipPath(path)

            w = text_width + 20
            h = self.height()
            bar_width = w * 0.3
            x = -bar_width + self._light_pos * (w + bar_width)

            pulse_color = QColor(self._pulse_color)
            gradient = QLinearGradient(x, 0, x + bar_width, 0)

            transparent_color = QColor(pulse_color)
            transparent_color.setAlpha(0)
            gradient.setColorAt(0, transparent_color)

            bright_color = QColor(pulse_color)
            bright_color.setAlpha(200)
            gradient.setColorAt(0.3, bright_color)
            gradient.setColorAt(0.7, bright_color)
            gradient.setColorAt(1, transparent_color)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(x, 0, bar_width, h))


class AnimationUtils:
    """
    动画工具类

    提供静态方法来实现常用的 UI 动画效果。
    """

    @staticmethod
    def fade_in(
        widget: QWidget, duration: int = 500, remove_effect_on_finish: bool = True
    ):
        """
        淡入动画

        将控件从完全透明渐变到完全不透明。

        Args:
            widget: 要应用动画的控件
            duration: 动画时长（毫秒），默认 500ms
            remove_effect_on_finish: 动画结束后是否移除效果，默认 True

        Returns:
            QPropertyAnimation: 动画对象，可以用于进一步控制
        """
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        animation = QPropertyAnimation(opacity_effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        if remove_effect_on_finish:

            def on_finished():
                widget.setGraphicsEffect(None)

            animation.finished.connect(on_finished)

        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation

    @staticmethod
    def slide_in_left(widget: QWidget, duration: int = 450, offset: int = 30):
        """
        从左侧滑入并淡入

        Args:
            widget: 要应用动画的控件
            duration: 动画时长（毫秒），默认 450ms
            offset: 左侧偏移的像素数，默认 30px

        Returns:
            QParallelAnimationGroup: 动画组对象
        """
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        fade_anim = QPropertyAnimation(opacity_effect, b"opacity", widget)
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        original_pos = widget.pos()
        widget.move(original_pos.x() - offset, original_pos.y())

        pos_anim = QPropertyAnimation(widget, b"pos", widget)
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(QPoint(original_pos.x() - offset, original_pos.y()))
        pos_anim.setEndValue(original_pos)
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)

        group = QParallelAnimationGroup(widget)
        group.addAnimation(fade_anim)
        group.addAnimation(pos_anim)

        def on_finished():
            # 检查 widget 是否有 opacity_effect 属性，如果有，将其设置为 None
            if hasattr(widget, "opacity_effect"):
                widget.opacity_effect = None
            widget.setGraphicsEffect(None)

        group.finished.connect(on_finished)

        group.start(QParallelAnimationGroup.DeleteWhenStopped)
        return group

    @staticmethod
    def pop_in(
        widget: QWidget,
        duration: int = 400,
        scale_from: float = 0.9,
        y_offset: int = 15,
    ):
        """
        组合弹出动画：缩放 + 淡入 + 上移

        Args:
            widget: 要应用动画的控件
            duration: 动画时长（毫秒），默认 400ms
            scale_from: 初始缩放比例，默认 0.9
            y_offset: 初始Y轴偏移（向下为正），默认 15px

        Returns:
            QParallelAnimationGroup: 动画组对象
        """
        widget.show()

        original_pos = widget.pos()
        original_size = widget.size()

        scale_anim_helper = _ScaleAnimationHelper(widget, scale_from)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        fade_anim = QPropertyAnimation(opacity_effect, b"opacity", widget)
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        start_pos = QPoint(original_pos.x(), original_pos.y() + y_offset)
        widget.move(start_pos)

        pos_anim = QPropertyAnimation(widget, b"pos", widget)
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(original_pos)
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)

        scale_anim = QPropertyAnimation(scale_anim_helper, b"scale", widget)
        scale_anim.setDuration(duration)
        scale_anim.setStartValue(scale_from)
        scale_anim.setEndValue(1.0)
        scale_anim.setEasingCurve(QEasingCurve.OutBack)

        group = QParallelAnimationGroup(widget)
        group.addAnimation(fade_anim)
        group.addAnimation(pos_anim)
        group.addAnimation(scale_anim)

        def on_finished():
            widget.setGraphicsEffect(None)
            widget.move(original_pos)
            scale_anim_helper.cleanup()

        group.finished.connect(on_finished)

        group.start(QParallelAnimationGroup.DeleteWhenStopped)
        return group

    @staticmethod
    def create_scanning_highlight(widget, color=None, duration=2000):
        """
        创建扫描高光动画效果

        创建一个从左到右移动的条状高光动画。

        Args:
            widget: 要应用扫描高光的控件
            color: 高光颜色（默认使用主题PRIMARY颜色）
            duration: 扫描周期（毫秒），默认 2000ms

        Returns:
            QPropertyAnimation: 动画对象，可以用于控制动画
        """
        if color is None:
            color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)
        highlight_widget = ScanningHighlightWidget(widget, color)
        highlight_widget.setAttribute(Qt.WA_TransparentForMouseEvents)

        animation = QPropertyAnimation(highlight_widget, b"highlightPosition", widget)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.setLoopCount(-1)

        highlight_widget.animation = animation
        highlight_widget.show()

        return highlight_widget


class _ScaleAnimationHelper(QObject):
    """
    缩放动画辅助类

    通过自定义绘制实现缩放效果
    """

    def __init__(self, widget: QWidget, initial_scale: float = 0.9):
        super().__init__(widget)
        self._widget = widget
        self._scale = initial_scale
        self._original_paint_event = widget.paintEvent
        self._original_pos = widget.pos()
        self._original_size = widget.size()

        widget.paintEvent = self._scaled_paint_event
        widget.update()

    def get_scale(self):
        return self._scale

    def set_scale(self, scale: float):
        self._scale = scale
        self._widget.update()

    def _scaled_paint_event(self, event):
        painter = QPainter(self._widget)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        center = self._widget.rect().center()
        painter.translate(center)
        painter.scale(self._scale, self._scale)
        painter.translate(-center)

        painter.end()

        self._original_paint_event(event)

    def cleanup(self):
        self._widget.paintEvent = self._original_paint_event
        self._widget.update()

    scale = pyqtProperty(float, get_scale, set_scale)


class ScanningHighlightWidget(QWidget):
    """
    扫描高光组件

    显示一个从左到右移动的条状高光。
    """

    def __init__(self, parent=None, color=None):
        super().__init__(parent)
        self._highlight_position = 0.0
        if color is None:
            color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)
        self.color = QColor(color)
        self.animation = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        if parent:
            parent.installEventFilter(self)
            self.resize(parent.size())

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == event.Resize:
            self.resize(self.parent().size())
        return super().eventFilter(obj, event)

    def highlightPosition(self):
        return self._highlight_position

    def setHighlightPosition(self, pos):
        self._highlight_position = pos
        self.update()

    highlightPosition = pyqtProperty(float, highlightPosition, setHighlightPosition)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        highlight_width = int(width * 0.3)
        start_x = int(
            (width + highlight_width) * self._highlight_position - highlight_width
        )

        # 创建渐变
        gradient = QLinearGradient(start_x, 0, start_x + highlight_width, 0)
        color = self.color
        color.setAlpha(0)
        gradient.setColorAt(0, color)
        color.setAlpha(80)
        gradient.setColorAt(0.5, color)
        color.setAlpha(0)
        gradient.setColorAt(1, color)

        painter.fillRect(start_x, 0, highlight_width, height, gradient)


class StepProgressContainer(QWidget):
    """
    步骤进度容器

    包含左侧连续线和所有步骤组件。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        # 左侧连续线容器
        self.line_container = QWidget(self)
        self.line_container.setFixedWidth(48)
        self.line_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        line_layout = QVBoxLayout(self.line_container)
        line_layout.setContentsMargins(0, 0, 0, 0)
        line_layout.setSpacing(0)

        # 左侧连续线
        self.continuous_line = ContinuousLineWidget(self.line_container)
        self.continuous_line.set_container(self)
        line_layout.addWidget(self.continuous_line)

        layout.addWidget(self.line_container)

        # 步骤列表容器
        self.steps_container = QWidget(self)
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(8, 8, 8, 8)
        self.steps_layout.setSpacing(12)

        # Install event filter to track layout changes
        self.steps_container.installEventFilter(self)

        layout.addWidget(self.steps_container, 1)

        self.step_widgets = []
        self.connector_widgets = []

    def eventFilter(self, obj, event):
        """Event filter to track layout changes"""
        if obj == self.steps_container and event.type() in (
            event.Resize,
            event.LayoutRequest,
        ):
            self.continuous_line.update()
        return super().eventFilter(obj, event)

    def add_step(self, step_widget):
        """添加步骤"""
        self.step_widgets.append(step_widget)
        self.steps_layout.addWidget(step_widget)
        # Update the line after layout has had time to calculate positions
        QTimer.singleShot(100, self.continuous_line.update)

    def get_step(self, index):
        """获取步骤"""
        if 0 <= index < len(self.step_widgets):
            return self.step_widgets[index]
        return None

    def update_line_state(
        self, active_index, completed_indices, cancelled_indices=None
    ):
        """更新连接线状态"""
        self.continuous_line.update_states(
            active_index, completed_indices, cancelled_indices
        )


class ContinuousLineWidget(QWidget):
    """
    左侧连续线组件

    显示贯穿所有步骤左侧的连续线。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMinimumWidth(48)
        self.container = None
        self.active_index = -1
        self.completed_indices = set()
        self.cancelled_indices = set()

        self._pulse_frame = 0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._advance_pulse_frame)
        self._pulse_timer.start(16)

    def _advance_pulse_frame(self):
        """
        推进脉冲动画帧

        参数:
            无

        返回值:
            无
        """
        if self.active_index >= 0:
            self._pulse_frame = (self._pulse_frame + 1) % 120
            self.update()

    def set_container(self, container):
        """设置步骤容器引用"""
        self.container = container

    def update_states(self, active_index, completed_indices, cancelled_indices=None):
        """更新状态"""
        self.active_index = active_index
        self.completed_indices = set(completed_indices)
        self.cancelled_indices = set(cancelled_indices) if cancelled_indices else set()
        if active_index < 0:
            self._pulse_frame = 0
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            width = self.width()
            self.height()
            center_x = width // 2
            circle_radius = 12

            if not self.container or not hasattr(self.container, "step_widgets"):
                return

            step_widgets = self.container.step_widgets
            if not step_widgets:
                return

            # 只收集可见的步骤（只使用自定义的is_visible属性）
            visible_steps = []
            for i, step_widget in enumerate(step_widgets):
                if step_widget.is_visible:
                    visible_steps.append(i)

            if not visible_steps:
                return

            # 创建位置映射：原始索引 -> y坐标（使用实际步骤组件的位置）
            pos_map = {}
            for orig_idx in visible_steps:
                step_widget = step_widgets[orig_idx]
                # 获取步骤组件在全局坐标系中的位置
                step_global_pos = step_widget.mapToGlobal(step_widget.rect().center())
                # 转换为相对于连续线组件的坐标
                line_local_pos = self.mapFromGlobal(step_global_pos)
                pos_map[orig_idx] = line_local_pos.y()

            # 先绘制连线（在图标下方）
            for i in range(len(visible_steps) - 1):
                orig_idx1 = visible_steps[i]
                orig_idx2 = visible_steps[i + 1]

                # 确保两个步骤是连续的
                if orig_idx2 != orig_idx1 + 1:
                    continue

                y1 = pos_map[orig_idx1]
                y2 = pos_map[orig_idx2]

                should_draw = False
                color = QColor(ThemeManager.get_color(ThemeManager.Colors.STEP_IDLE))

                if orig_idx1 in self.completed_indices:
                    should_draw = True
                    color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_COMPLETED)
                    )
                elif (
                    orig_idx1 in self.cancelled_indices
                    or orig_idx2 in self.cancelled_indices
                ):
                    should_draw = True
                    color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_ERROR)
                    )
                elif orig_idx1 == self.active_index or orig_idx2 == self.active_index:
                    should_draw = True
                    color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_ACTIVE)
                    )

                if not should_draw:
                    continue

                pen = QPen(color, 2)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)

                # 线从圆的边缘开始，到下一个圆的边缘结束
                line_start_y = y1 + circle_radius
                line_end_y = y2 - circle_radius

                if line_start_y < line_end_y:
                    painter.drawLine(center_x, line_start_y, center_x, line_end_y)

            # 再绘制状态图标（在连线上方）
            for orig_idx in visible_steps:
                icon_y = pos_map[orig_idx]

                if orig_idx in self.completed_indices:
                    completed_color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_COMPLETED)
                    )
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(completed_color)
                    painter.drawEllipse(
                        center_x - circle_radius,
                        icon_y - circle_radius,
                        circle_radius * 2,
                        circle_radius * 2,
                    )

                    painter.setPen(
                        QPen(
                            QColor("white"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                        )
                    )
                    painter.setBrush(Qt.NoBrush)
                    painter.drawLine(center_x - 6, icon_y, center_x - 1, icon_y + 5)
                    painter.drawLine(center_x - 1, icon_y + 5, center_x + 8, icon_y - 4)

                elif orig_idx in self.cancelled_indices:
                    error_color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_ERROR)
                    )
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(error_color)
                    painter.drawEllipse(
                        center_x - circle_radius,
                        icon_y - circle_radius,
                        circle_radius * 2,
                        circle_radius * 2,
                    )

                    painter.setPen(
                        QPen(
                            QColor("white"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                        )
                    )
                    painter.setBrush(Qt.NoBrush)
                    painter.drawLine(center_x - 5, icon_y - 5, center_x + 5, icon_y + 5)
                    painter.drawLine(center_x + 5, icon_y - 5, center_x - 5, icon_y + 5)

                elif orig_idx == self.active_index:
                    active_color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_ACTIVE)
                    )
                    painter.setPen(QPen(active_color, 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(
                        center_x - circle_radius,
                        icon_y - circle_radius,
                        circle_radius * 2,
                        circle_radius * 2,
                    )

                    pulse_progress = self._pulse_frame / 120.0
                    triangle_wave = 1 - 2 * abs(pulse_progress - 0.5)
                    pulse_scale = triangle_wave
                    inner_base_radius = 6
                    inner_radius = int(inner_base_radius * (0.6 + 0.4 * pulse_scale))

                    glow_alpha = int(100 + 80 * pulse_scale)
                    glow_color = QColor(active_color)
                    glow_color.setAlpha(glow_alpha)

                    outer_glow_radius = inner_base_radius + int(4 * pulse_scale)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(glow_color)
                    painter.drawEllipse(
                        center_x - outer_glow_radius,
                        icon_y - outer_glow_radius,
                        outer_glow_radius * 2,
                        outer_glow_radius * 2,
                    )

                    painter.setBrush(active_color)
                    painter.drawEllipse(
                        center_x - inner_radius,
                        icon_y - inner_radius,
                        inner_radius * 2,
                        inner_radius * 2,
                    )

                else:
                    idle_color = QColor(
                        ThemeManager.get_color(ThemeManager.Colors.STEP_IDLE)
                    )
                    painter.setPen(QPen(idle_color, 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(
                        center_x - circle_radius,
                        icon_y - circle_radius,
                        circle_radius * 2,
                        circle_radius * 2,
                    )
        except Exception as e:
            print(f"绘制错误: {e}")


class StepProgressWidget(QFrame):
    """
    单个步骤进度组件

    显示单个步骤的名称、状态和输出。
    """

    clicked = pyqtSignal()
    retry_clicked = pyqtSignal(int)  # 发送步骤索引

    def __init__(self, step_name: str, step_index: int, parent=None):
        super().__init__(parent)
        self.step_name = step_name
        self.step_index = step_index
        self.is_active = False
        self.is_completed = False
        self.is_cancelled = False
        self.is_visible = False
        self._elapsed_time = 0.0
        self.ai_output = ""
        self.detail_logs = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.highlight_widget = None
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.init_ui()

    @property
    def elapsed_time(self):
        """
        获取已耗时

        Returns:
            float: 已耗时（秒）
        """
        return self._elapsed_time

    @elapsed_time.setter
    def elapsed_time(self, value):
        """
        设置已耗时，并更新显示

        Args:
            value: 要设置的耗时（秒）
        """
        self._elapsed_time = value
        self.timer_label.setText(f"{self._elapsed_time:.1f}s")

    def init_ui(self):
        """初始化 UI"""
        from qfluentwidgets import FluentIcon as FIF
        from qfluentwidgets import TransparentToolButton

        self.setObjectName("stepProgressWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 头部容器
        self.header_widget = QFrame(self)
        self.header_widget.setObjectName("stepHeader")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(12)

        # 步骤信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = PulseLabel(self.step_name, self)
        self.name_label.setObjectName("stepNameLabel")
        self.name_label.setTextColor(
            ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY)
        )
        info_layout.addWidget(self.name_label)

        header_layout.addLayout(info_layout, 1)

        self.timer_label = QLabel("0.0s")
        self.timer_label.setObjectName("stepTimerLabel")
        self.timer_label.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
        )
        self.timer_label.hide()
        header_layout.addWidget(self.timer_label)

        # 重试按钮
        self.retry_btn = TransparentToolButton(FIF.SYNC, self.header_widget)
        self.retry_btn.setFixedSize(28, 28)
        self.retry_btn.setIconSize(QSize(14, 14))
        self.retry_btn.setToolTip("重试此步骤")
        self.retry_btn.hide()
        self.retry_btn.clicked.connect(lambda: self.retry_clicked.emit(self.step_index))
        header_layout.addWidget(self.retry_btn)

        # 展开/折叠按钮
        self.toggle_btn = TransparentToolButton(
            create_simple_arrow_icon("up", 14), self.header_widget
        )
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setIconSize(QSize(14, 14))
        self.toggle_btn.setToolTip("展开/收起AI输出内容")
        self.toggle_btn.hide()
        self.toggle_btn.clicked.connect(self._toggle_output)
        header_layout.addWidget(self.toggle_btn)

        main_layout.addWidget(self.header_widget)

        # 输出区域
        self.output_container = QFrame(self)
        self.output_container.setObjectName("stepOutputContainer")
        self.output_container.setMaximumHeight(0)
        self.output_container.hide()

        output_layout = QVBoxLayout(self.output_container)
        output_layout.setContentsMargins(12, 0, 12, 12)
        output_layout.setSpacing(4)

        # 创建滚动区域
        scroll_area = QScrollArea(self.output_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("stepOutputScrollArea")
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            {Styles.ScrollBar}
        """)

        # 创建内容容器
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_content_layout = QVBoxLayout(scroll_content)
        scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        scroll_content_layout.setSpacing(0)

        self.output_label = QLabel(scroll_content)
        self.output_label.setObjectName("stepOutputLabel")
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet(
            f"font-size: 13px; color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
        )
        scroll_content_layout.addWidget(self.output_label)
        scroll_content_layout.addStretch(1)

        scroll_area.setWidget(scroll_content)
        output_layout.addWidget(scroll_area)

        main_layout.addWidget(self.output_container)

        self._update_styles()
        self.expand_animation = None

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_ai_output(self, output_text: str):
        """设置AI输出内容"""
        self.ai_output = output_text
        self._update_output()

    def add_log(self, log_text: str):
        """添加详情日志"""
        self.detail_logs.append(log_text)

    def get_logs(self):
        """获取详情日志"""
        return self.detail_logs

    def set_active(self, active: bool):
        """
        设置步骤是否激活

        Args:
            active: 是否激活

        Returns:
            无
        """
        self.is_active = active
        active_color = ThemeManager.get_color(ThemeManager.Colors.STEP_ACTIVE)
        if active:
            self.name_label.setTextColor(active_color)
            self.name_label.setPulseColor(active_color)
            self.name_label.startPulse()
            if not self.is_completed:
                self._elapsed_time = 0.0
                self.timer_label.setText("0.0s")
            self.timer_label.setStyleSheet(
                f"font-size: 13px; font-weight: 500; color: {active_color};"
            )
            self.timer_label.show()

            if self.timer.isActive():
                self.timer.stop()
            if not self.is_completed:
                self.timer.start(100)

            if not self.highlight_widget:
                self.highlight_widget = AnimationUtils.create_scanning_highlight(
                    self.header_widget, active_color
                )

            if self.ai_output:
                self.toggle_btn.show()

            self._update_styles()
        else:
            self.name_label.stopPulse()
            self.name_label.setTextColor(
                ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY)
            )
            if self.is_completed:
                completed_color = ThemeManager.get_color(
                    ThemeManager.Colors.STEP_COMPLETED
                )
                self.timer_label.setStyleSheet(
                    f"font-size: 13px; font-weight: 500; color: {completed_color};"
                )
            else:
                self.timer_label.setStyleSheet(
                    f"font-size: 13px; font-weight: 500; color: {ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)};"
                )
            self.timer.stop()

            if self.highlight_widget:
                if self.highlight_widget.animation:
                    self.highlight_widget.animation.stop()
                self.highlight_widget.hide()
                self.highlight_widget.deleteLater()
                self.highlight_widget = None

    def set_completed(self, completed: bool, auto_expand: bool = False):
        """
        设置步骤是否完成

        Args:
            completed: 是否完成
            auto_expand: 是否自动展开输出区域，默认为 False

        Returns:
            无
        """
        self.is_completed = completed
        completed_color = ThemeManager.get_color(ThemeManager.Colors.STEP_COMPLETED)
        if completed:
            self.set_active(False)
            self.name_label.setTextColor(completed_color)
            self.timer_label.setStyleSheet(
                f"font-size: 13px; font-weight: 500; color: {completed_color};"
            )
            self.timer_label.show()

            if self.ai_output:
                self.toggle_btn.show()
                if auto_expand:
                    self._expand_output()

            self._update_styles()
        else:
            self._update_styles()

    def set_cancelled(self, cancelled: bool):
        """
        设置步骤是否被取消

        Args:
            cancelled: 是否被取消

        Returns:
            无
        """
        self.is_cancelled = cancelled
        error_color = ThemeManager.get_color(ThemeManager.Colors.STEP_ERROR)
        if cancelled:
            self.set_active(False)
            self.name_label.setTextColor(error_color)
            self.timer_label.setStyleSheet(
                f"font-size: 13px; font-weight: 500; color: {error_color};"
            )
            self.timer_label.show()
            self.retry_btn.show()
            self._update_styles()
        else:
            self.retry_btn.hide()
            self._update_styles()

    def set_visible(self, visible: bool, animate: bool = True):
        """设置是否可见"""
        if visible == self.is_visible:
            return

        # 确保 opacity_effect 存在
        if not hasattr(self, "opacity_effect") or not self.opacity_effect:
            from PyQt5.QtWidgets import QGraphicsOpacityEffect

            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)

        self.is_visible = visible
        if visible:
            if animate:
                try:
                    self.opacity_effect.setOpacity(0.0)
                    QTimer.singleShot(50, lambda: AnimationUtils.slide_in_left(self))
                    # Also fade in
                    anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
                    anim.setDuration(450)
                    anim.setStartValue(0.0)
                    anim.setEndValue(1.0)
                    anim.setEasingCurve(QEasingCurve.OutCubic)
                    anim.start(QPropertyAnimation.DeleteWhenStopped)
                except (RuntimeError, AttributeError):
                    # 如果对象已被删除，重新创建
                    from PyQt5.QtWidgets import QGraphicsOpacityEffect

                    self.opacity_effect = QGraphicsOpacityEffect(self)
                    self.setGraphicsEffect(self.opacity_effect)
                    self.opacity_effect.setOpacity(1.0)
            else:
                try:
                    self.opacity_effect.setOpacity(1.0)
                except (RuntimeError, AttributeError):
                    # 如果对象已被删除，重新创建
                    from PyQt5.QtWidgets import QGraphicsOpacityEffect

                    self.opacity_effect = QGraphicsOpacityEffect(self)
                    self.setGraphicsEffect(self.opacity_effect)
                    self.opacity_effect.setOpacity(1.0)
        else:
            try:
                self.opacity_effect.setOpacity(0.0)
            except (RuntimeError, AttributeError):
                # 如果对象已被删除，重新创建
                from PyQt5.QtWidgets import QGraphicsOpacityEffect

                self.opacity_effect = QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(self.opacity_effect)
                self.opacity_effect.setOpacity(0.0)

    def _update_timer(self):
        """更新计时器显示"""
        self._elapsed_time += 0.1
        self.timer_label.setText(f"{self._elapsed_time:.1f}s")

    def _toggle_output(self):
        """切换输出区域的展开/折叠"""
        if (
            self.output_container.isVisible()
            and self.output_container.maximumHeight() > 0
        ):
            self.toggle_btn.setIcon(create_simple_arrow_icon("up", 14))
            self._collapse_output()
        else:
            self.toggle_btn.setIcon(create_simple_arrow_icon("down", 14))
            self._expand_output()

    def _expand_output(self):
        """展开输出区域"""
        self.output_container.show()

        if self.expand_animation:
            self.expand_animation.stop()

        self.expand_animation = QPropertyAnimation(
            self.output_container, b"maximumHeight", self
        )
        self.expand_animation.setDuration(400)
        self.expand_animation.setStartValue(0)
        self.expand_animation.setEndValue(300)
        self.expand_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.expand_animation.start()

    def _collapse_output(self):
        """折叠输出区域"""
        if self.expand_animation:
            self.expand_animation.stop()

        self.expand_animation = QPropertyAnimation(
            self.output_container, b"maximumHeight", self
        )
        self.expand_animation.setDuration(400)
        self.expand_animation.setStartValue(self.output_container.maximumHeight())
        self.expand_animation.setEndValue(0)
        self.expand_animation.setEasingCurve(QEasingCurve.OutCubic)

        def on_finished():
            self.output_container.hide()

        self.expand_animation.finished.connect(on_finished)
        self.expand_animation.start()

    def _update_output(self):
        """更新输出内容"""
        if self.ai_output:
            output_text = self.ai_output
            if len(output_text) > 500:
                output_text = output_text[:500] + "..."
            self.output_label.setText(output_text)
            if self.is_active or self.is_completed or self.is_cancelled:
                self.toggle_btn.show()

    def _update_styles(self):
        """更新样式"""
        completed_color = ThemeManager.get_color(ThemeManager.Colors.STEP_COMPLETED)
        error_color = ThemeManager.get_color(ThemeManager.Colors.STEP_ERROR)
        active_color = ThemeManager.get_color(ThemeManager.Colors.STEP_ACTIVE)
        border_primary = ThemeManager.get_color(ThemeManager.Colors.BORDER_PRIMARY)
        border_secondary = ThemeManager.get_color(ThemeManager.Colors.BORDER_SECONDARY)

        if self.is_completed:
            self.setStyleSheet(f"""
                QFrame#stepProgressWidget {{
                    background-color: rgba(81, 207, 102, 0.08);
                    border: 2px solid rgba(81, 207, 102, 0.3);
                    border-radius: 12px;
                }}
            """)
        elif self.is_cancelled:
            self.setStyleSheet(f"""
                QFrame#stepProgressWidget {{
                    background-color: rgba(255, 107, 107, 0.08);
                    border: 2px solid rgba(255, 107, 107, 0.3);
                    border-radius: 12px;
                }}
            """)
        elif self.is_active:
            self.setStyleSheet(f"""
                QFrame#stepProgressWidget {{
                    background-color: rgba(162, 155, 254, 0.08);
                    border: 2px solid rgba(162, 155, 254, 0.6);
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#stepProgressWidget {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                }}
                QFrame#stepProgressWidget:hover {{
                    background-color: rgba(255, 255, 255, 0.06);
                }}
            """)

    def reset(self):
        """重置步骤状态"""
        self.set_active(False)
        self.set_completed(False)
        self.set_cancelled(False)
        self.name_label.setTextColor(
            ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY)
        )
        self.timer_label.hide()
        self._elapsed_time = 0.0
        self.timer_label.setText("0.0s")
        self.ai_output = ""
        self.detail_logs = []
        self.output_label.setText("")
        self.toggle_btn.hide()
        self.output_container.hide()
        self.output_container.setMaximumHeight(0)
        self.toggle_btn.setIcon(create_simple_arrow_icon("up", 14))
        self._update_styles()
        # 检查 opacity_effect 是否存在，避免访问已删除的对象
        if hasattr(self, "opacity_effect") and self.opacity_effect:
            try:
                self.opacity_effect.setOpacity(0.0)
            except (RuntimeError, AttributeError):
                # 如果对象已被删除，重新创建
                from PyQt5.QtWidgets import QGraphicsOpacityEffect

                self.opacity_effect = QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(self.opacity_effect)
                self.opacity_effect.setOpacity(0.0)
        else:
            # 如果不存在，创建新的
            from PyQt5.QtWidgets import QGraphicsOpacityEffect

            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            self.opacity_effect.setOpacity(0.0)
        self.is_visible = False
