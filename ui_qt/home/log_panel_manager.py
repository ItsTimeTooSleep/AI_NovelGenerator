# -*- coding: utf-8 -*-
"""
日志面板管理器模块

负责日志面板的显示、隐藏、动画控制和日志消息输出。

主要功能:
- 日志面板的显示/隐藏切换
- 平滑的动画效果
- 日志消息输出
- Step 3 时自动隐藏

使用示例:
    from ui_qt.home import LogPanelManager

    log_manager = LogPanelManager(home_tab)
    log_manager.initialize()
    log_manager.log("Hello, world!")
    log_manager.toggle_panel()
"""

from typing import Optional

from PyQt5.QtCore import QMargins, QTimer
from PyQt5.QtGui import QColor, QFont, QTextCharFormat
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import FluentIcon as FIF

from ..core import BaseManager, EventBus, EventType
from ..utils.styles import ThemeManager

try:
    from core import LogLevel, LogRecord, get_logger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class LogPanelManager(BaseManager):
    """
    日志面板管理器

    负责管理日志面板的所有交互，包括：
    - 显示/隐藏切换
    - 平滑动画
    - 日志消息输出
    - 根据步骤状态自动调整可见性
    - 支持按级别着色显示
    """

    def __init__(self, home_tab: QWidget):
        """
        初始化日志面板管理器

        Args:
            home_tab: HomeTab 实例，用于访问UI组件
        """
        super().__init__(home_tab)
        self._log_panel_expanded: bool = False
        self._animation_timer: Optional[QTimer] = None
        self._anim_start_width: int = 0
        self._anim_end_width: int = 0
        self._anim_step: int = 0
        self._anim_total_steps: int = 30
        self._target_log_width: int = 280
        self._original_margins: QMargins = QMargins(12, 12, 12, 12)

        if LOGGER_AVAILABLE:
            self._setup_logger_integration()

    def initialize(self) -> None:
        """
        初始化日志面板管理器

        设置初始状态，连接事件订阅。
        """
        self._init_initial_state()
        self._subscribe_events()
        self._initialized = True

    def _init_initial_state(self) -> None:
        """
        初始化UI初始状态

        设置日志面板为隐藏状态。
        """
        if hasattr(self.parent, "rightPartSplitter"):
            total_width = self._get_splitter_total_width()
            self.parent.rightPartSplitter.setSizes([total_width, 0])

        if hasattr(self.parent, "logPanel"):
            self.parent.logPanel.setMinimumWidth(0)
            self.parent.logPanel.setMaximumWidth(0)
            self.parent.logPanel.hide()

        self._log_panel_expanded = False

        if hasattr(self.parent, "logToggleBtn"):
            self.parent.logToggleBtn.setIcon(FIF.LEFT_ARROW)
            self.parent.logToggleBtn.setToolTip("显示日志面板")

    def _subscribe_events(self) -> None:
        """
        订阅事件总线事件

        监听相关事件以自动调整日志面板状态。
        """
        event_bus = EventBus.get_instance()
        event_bus.subscribe(EventType.LOG_MESSAGE, self._on_log_message)
        event_bus.subscribe(EventType.STEP_CHANGED, self._on_step_changed)

    def _on_log_message(self, event) -> None:
        """
        处理日志消息事件

        Args:
            event: 事件对象，包含 message 字段
        """
        message = event.data.get("message", "")
        if message:
            self.log(message)

    def _on_step_changed(self, event) -> None:
        """
        处理步骤变化事件

        在 Step 3 时自动隐藏日志面板。

        Args:
            event: 事件对象，包含 step 字段
        """
        step = event.data.get("step", "")
        if step == "step3":
            self.set_visible_in_step3(False)
        else:
            self.set_visible_in_step3(True)

    def toggle_panel(self) -> None:
        """
        切换日志面板的显示/隐藏状态

        带有平滑的动画效果。仅在 Step 1 和 Step 2 时可用。
        """
        if getattr(self.parent, "_entered_full_layout", False):
            return

        self._stop_existing_animation()

        if self._log_panel_expanded:
            self._hide_panel_with_animation()
        else:
            self._show_panel_with_animation()

    def show_panel(self) -> None:
        """
        显示日志面板

        带动画效果。
        """
        self._stop_existing_animation()
        self._show_panel_with_animation()

    def hide_panel(self) -> None:
        """
        隐藏日志面板

        带动画效果。
        """
        self._stop_existing_animation()
        self._hide_panel_with_animation()

    def _get_splitter_total_width(self) -> int:
        """
        获取 splitter 的总宽度

        Returns:
            int: splitter 总宽度
        """
        if hasattr(self.parent, "rightPartSplitter"):
            sizes = self.parent.rightPartSplitter.sizes()
            if len(sizes) >= 2:
                return sum(sizes)
        return 800

    def _show_panel_with_animation(self) -> None:
        """
        显示日志面板（内部方法，带动画）
        """
        self._log_panel_expanded = True
        if hasattr(self.parent, "logToggleBtn"):
            self.parent.logToggleBtn.setIcon(FIF.RIGHT_ARROW)
            self.parent.logToggleBtn.setToolTip("隐藏日志面板")

        if hasattr(self.parent, "logPanel"):
            self.parent.logPanel.setMinimumWidth(0)

        if hasattr(self.parent, "logPanelLayout") and hasattr(
            self, "_original_margins"
        ):
            self.parent.logPanelLayout.setContentsMargins(self._original_margins)

        total_width = self._get_splitter_total_width()
        current_sizes = (
            self.parent.rightPartSplitter.sizes()
            if hasattr(self.parent, "rightPartSplitter")
            else [total_width, 0]
        )
        current_log_width = current_sizes[1] if len(current_sizes) > 1 else 0

        self._anim_start_width = current_log_width
        self._anim_end_width = self._target_log_width
        self._anim_step = 0
        self._total_width = total_width
        self._content_shown = False

        print(
            f"[动画调试] 显示动画: start={self._anim_start_width}, end={self._anim_end_width}, total={total_width}"
        )

        self._animation_timer = QTimer(self.parent)
        self._animation_timer.setInterval(10)
        self._animation_timer.timeout.connect(self._update_show_animation)
        self._animation_timer.start()

    def _hide_panel_with_animation(self) -> None:
        """
        隐藏日志面板（内部方法，带动画）
        """
        self._log_panel_expanded = False
        if hasattr(self.parent, "logToggleBtn"):
            self.parent.logToggleBtn.setIcon(FIF.LEFT_ARROW)
            self.parent.logToggleBtn.setToolTip("显示日志面板")

        if hasattr(self.parent, "logPanel"):
            self.parent.logPanel.setMinimumWidth(0)
            for child in self.parent.logPanel.findChildren(QWidget):
                child.setMinimumWidth(0)
                child.setMaximumWidth(16777215)
            if hasattr(self.parent, "logPanelLabel"):
                self.parent.logPanelLabel.setMinimumWidth(0)
                self.parent.logPanelLabel.setMaximumWidth(16777215)
            if hasattr(self.parent, "logOutput"):
                self.parent.logOutput.setMinimumWidth(0)
                self.parent.logOutput.setMaximumWidth(16777215)
                v_scroll = self.parent.logOutput.verticalScrollBar()
                if v_scroll:
                    v_scroll.setMinimumWidth(0)
                h_scroll = self.parent.logOutput.horizontalScrollBar()
                if h_scroll:
                    h_scroll.setMinimumWidth(0)
            if hasattr(self.parent, "logPanelLayout"):
                self._original_margins = self.parent.logPanelLayout.contentsMargins()
                self.parent.logPanelLayout.setContentsMargins(0, 0, 0, 0)

        if hasattr(self.parent, "rightPartSplitter"):
            self.parent.rightPartSplitter.setCollapsible(1, True)
            self.parent.rightPartSplitter.setHandleWidth(1)

        if hasattr(self.parent, "logPanelLabel"):
            self.parent.logPanelLabel.hide()
        if hasattr(self.parent, "logOutput"):
            self.parent.logOutput.hide()

        total_width = self._get_splitter_total_width()
        current_sizes = (
            self.parent.rightPartSplitter.sizes()
            if hasattr(self.parent, "rightPartSplitter")
            else [total_width, 0]
        )
        current_log_width = current_sizes[1] if len(current_sizes) > 1 else 0

        self._anim_start_width = current_log_width
        self._anim_end_width = 0
        self._anim_step = 0
        self._total_width = total_width

        print(
            f"[动画调试] 隐藏动画: start={self._anim_start_width}, end={self._anim_end_width}, total={total_width}"
        )

        self._animation_timer = QTimer(self.parent)
        self._animation_timer.setInterval(10)
        self._animation_timer.timeout.connect(self._update_hide_animation)
        self._animation_timer.start()

    def _update_show_animation(self) -> None:
        """
        更新显示动画帧

        使用 OutBack 缓动曲线实现精致的弹出效果
        """
        self._anim_step += 1
        t = self._anim_step / self._anim_total_steps

        eased = self._ease_out_back(t)

        new_log_width = int(
            self._anim_start_width
            + (self._anim_end_width - self._anim_start_width) * eased
        )
        new_main_width = self._total_width - new_log_width

        if hasattr(self.parent, "rightPartSplitter"):
            self.parent.rightPartSplitter.setSizes([new_main_width, new_log_width])

        min_content_width = 100
        if new_log_width >= min_content_width and not getattr(
            self, "_content_shown", False
        ):
            self._content_shown = True
            if hasattr(self.parent, "logPanelLabel"):
                self.parent.logPanelLabel.show()
            if hasattr(self.parent, "logOutput"):
                self.parent.logOutput.show()

        if self._anim_step % 10 == 0:
            print(f"[动画调试] 显示步骤 {self._anim_step}, log_width={new_log_width}")

        if self._anim_step >= self._anim_total_steps:
            self._stop_existing_animation()
            if hasattr(self.parent, "rightPartSplitter"):
                final_main = self._total_width - self._anim_end_width
                self.parent.rightPartSplitter.setSizes(
                    [final_main, self._anim_end_width]
                )
            if hasattr(self.parent, "logPanel"):
                self.parent.logPanel.setMinimumWidth(200)
            print(f"[动画调试] 显示动画结束, log_width={self._anim_end_width}")

    def _update_hide_animation(self) -> None:
        """
        更新隐藏动画帧

        使用 InQuad 缓动曲线实现平滑的收起效果
        """
        self._anim_step += 1
        t = self._anim_step / self._anim_total_steps

        eased = self._ease_in_quad(t)

        new_log_width = int(
            self._anim_start_width
            + (self._anim_end_width - self._anim_start_width) * eased
        )
        new_main_width = self._total_width - new_log_width

        if hasattr(self.parent, "rightPartSplitter"):
            self.parent.rightPartSplitter.setSizes([new_main_width, new_log_width])

        if self._anim_step % 10 == 0:
            actual_sizes = (
                self.parent.rightPartSplitter.sizes()
                if hasattr(self.parent, "rightPartSplitter")
                else []
            )
            print(
                f"[动画调试] 隐藏步骤 {self._anim_step}, log_width={new_log_width}, actual_sizes={actual_sizes}"
            )

        if self._anim_step >= self._anim_total_steps:
            self._stop_existing_animation()
            if hasattr(self.parent, "rightPartSplitter"):
                self.parent.rightPartSplitter.setSizes([self._total_width, 0])
                final_sizes = self.parent.rightPartSplitter.sizes()
                print(f"[动画调试] 隐藏动画结束, 最终 sizes={final_sizes}")
            print("[动画调试] 隐藏动画结束, log_width=0")

    def set_visible_in_step3(self, visible: bool) -> None:
        """
        设置在 Step 3 时的可见性

        Args:
            visible: True表示显示，False表示隐藏
        """
        import logging
        logging.info(f"[DEBUG] LogPanelManager.set_visible_in_step3 开始执行, visible={visible}")
        
        try:
            if visible:
                logging.info("[DEBUG] 调用 _show_log_panel_in_steps_1_2()")
                self._show_log_panel_in_steps_1_2()
            else:
                logging.info("[DEBUG] 调用 _hide_log_panel_in_step3()")
                self._hide_log_panel_in_step3()
            logging.info("[DEBUG] LogPanelManager.set_visible_in_step3 执行成功")
        except Exception as e:
            logging.error(f"[DEBUG] LogPanelManager.set_visible_in_step3 执行失败: {e}")
            import traceback
            logging.error(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")

    def _hide_log_panel_in_step3(self) -> None:
        """
        在 Step 3 时隐藏日志面板和开关按钮
        """
        import logging
        logging.info("[DEBUG] LogPanelManager._hide_log_panel_in_step3 开始执行")
        
        try:
            logging.info("[DEBUG] 获取 splitter 总宽度")
            total_width = self._get_splitter_total_width()
            logging.info(f"[DEBUG] splitter 总宽度: {total_width}")
            
            if hasattr(self.parent, "rightPartSplitter"):
                logging.info("[DEBUG] 设置 rightPartSplitter 大小")
                self.parent.rightPartSplitter.setSizes([total_width, 0])
                sizes = self.parent.rightPartSplitter.sizes()
                logging.info(f"[DEBUG] rightPartSplitter 新大小: {sizes}")
            
            logging.info("[DEBUG] 设置 _log_panel_expanded 为 False")
            self._log_panel_expanded = False

            if hasattr(self.parent, "logPanel"):
                logging.info("[DEBUG] 设置 logPanel 最小宽度为 0")
                self.parent.logPanel.setMinimumWidth(0)
                logging.info("[DEBUG] 设置 logPanel 最大宽度为 0")
                self.parent.logPanel.setMaximumWidth(0)
                logging.info("[DEBUG] 隐藏 logPanel")
                self.parent.logPanel.hide()

            if hasattr(self.parent, "logToggleBtn"):
                logging.info("[DEBUG] 隐藏 logToggleBtn")
                self.parent.logToggleBtn.hide()
            
            logging.info("[DEBUG] LogPanelManager._hide_log_panel_in_step3 执行成功")
        except Exception as e:
            logging.error(f"[DEBUG] LogPanelManager._hide_log_panel_in_step3 执行失败: {e}")
            import traceback
            logging.error(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")

    def _show_log_panel_in_steps_1_2(self) -> None:
        """
        在 Step 1 和 Step 2 时显示日志面板开关按钮
        """
        if hasattr(self.parent, "logToggleBtn"):
            self.parent.logToggleBtn.show()

        if hasattr(self.parent, "logPanel"):
            self.parent.logPanel.setMinimumWidth(0)
            self.parent.logPanel.setMaximumWidth(16777215)
            self.parent.logPanel.show()

        total_width = self._get_splitter_total_width()
        if hasattr(self.parent, "rightPartSplitter"):
            self.parent.rightPartSplitter.setSizes([total_width, 0])
        self._log_panel_expanded = False

        if hasattr(self.parent, "logToggleBtn"):
            self.parent.logToggleBtn.setIcon(FIF.LEFT_ARROW)
            self.parent.logToggleBtn.setToolTip("显示日志面板")

    def _setup_logger_integration(self) -> None:
        """
        设置与新日志系统的集成

        将UI日志回调注册到全局日志管理器，
        这样所有日志都会自动显示在UI面板中。
        """
        try:
            logger = get_logger()
            logger.set_ui_callback(self._on_log_record)
        except Exception as e:
            print(f"无法集成日志系统: {e}")

    def _get_level_color(self, level: LogLevel) -> QColor:
        """
        获取日志级别的对应颜色

        Args:
            level: 日志级别

        Returns:
            QColor: 对应的颜色对象
        """
        color_map = {
            LogLevel.DEBUG: QColor(
                ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY)
            ),
            LogLevel.INFO: QColor(ThemeManager.get_color(ThemeManager.Colors.SUCCESS)),
            LogLevel.WARN: QColor(ThemeManager.get_color(ThemeManager.Colors.WARNING)),
            LogLevel.ERROR: QColor(ThemeManager.get_color(ThemeManager.Colors.ERROR)),
        }
        return color_map.get(
            level, QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY))
        )

    def _on_log_record(self, record: LogRecord) -> None:
        """
        处理来自日志管理器的日志记录

        Args:
            record: LogRecord 对象
        """
        if LOGGER_AVAILABLE:
            logger = get_logger()
            configured_level = logger.get_configured_level()

            if record.level.value < configured_level.value:
                return

        if hasattr(self.parent, "logOutput"):
            text_edit = self.parent.logOutput
            cursor = text_edit.textCursor()
            cursor.movePosition(cursor.End)

            timestamp_str = record.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            level_str = record.level.name
            module_str = record.module
            message_str = record.message

            timestamp_format = QTextCharFormat()
            timestamp_format.setFont(QFont("Consolas", 9))
            timestamp_format.setForeground(
                QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY))
            )

            level_format = QTextCharFormat()
            level_format.setFont(QFont("Consolas", 9))
            level_format.setForeground(self._get_level_color(record.level))

            module_format = QTextCharFormat()
            module_format.setFont(QFont("Consolas", 9))
            module_format.setForeground(
                QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY))
            )

            message_format = QTextCharFormat()
            message_format.setFont(QFont("Consolas", 9))
            message_format.setForeground(
                QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY))
            )

            cursor.setCharFormat(timestamp_format)
            cursor.insertText(f"[{timestamp_str}] ")

            cursor.setCharFormat(level_format)
            cursor.insertText(f"[{level_str}] ")

            cursor.setCharFormat(module_format)
            cursor.insertText(f"[{module_str}] ")

            cursor.setCharFormat(message_format)
            cursor.insertText(message_str + "\n")

            text_edit.setTextCursor(cursor)
            text_edit.ensureCursorVisible()

    def log(self, message: str) -> None:
        """
        输出日志消息（向后兼容）

        Args:
            message: 要输出的日志消息
        """
        if LOGGER_AVAILABLE:
            logger = get_logger()
            logger.info("ui_log_panel", message)
        else:
            if hasattr(self.parent, "logOutput"):
                text_edit = self.parent.logOutput
                cursor = text_edit.textCursor()
                cursor.movePosition(cursor.End)

                char_format = QTextCharFormat()
                char_format.setFont(QFont("Consolas", 9))
                char_format.setForeground(
                    QColor(ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY))
                )

                cursor.setCharFormat(char_format)
                cursor.insertText(message + "\n")

                text_edit.setTextCursor(cursor)
                text_edit.ensureCursorVisible()

    def _stop_existing_animation(self) -> None:
        """
        停止正在进行的动画
        """
        if hasattr(self, "_animation_timer") and self._animation_timer:
            if self._animation_timer.isActive():
                self._animation_timer.stop()

    def _ease_out_back(self, t: float) -> float:
        """
        OutBack 缓动曲线

        产生轻微的过冲效果，使动画看起来更有弹性。
        适用于展开动画，给人一种"弹出"的感觉。

        Args:
            t: 进度值，范围 [0, 1]

        Returns:
            float: 缓动后的值
        """
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    def _ease_in_quad(self, t: float) -> float:
        """
        InQuad 缓动曲线

        二次方缓入，开始慢然后加速。
        适用于收起动画，给人一种"快速收起"的感觉。

        Args:
            t: 进度值，范围 [0, 1]

        Returns:
            float: 缓动后的值
        """
        return t * t

    def _ease_out_cubic(self, t: float) -> float:
        """
        OutCubic 缓动曲线

        三次方缓出，开始快然后减速。
        适用于需要平滑结束的动画。

        Args:
            t: 进度值，范围 [0, 1]

        Returns:
            float: 缓动后的值
        """
        return 1 - pow(1 - t, 3)

    def _get_safe_right_part_width(self) -> int:
        """
        获取安全的右侧区域宽度

        优先使用 splitter 的实际总宽度，确保动画过程中宽度计算一致。

        Returns:
            int: 安全的宽度值
        """
        if hasattr(self.parent, "rightPartSplitter"):
            current_sizes = self.parent.rightPartSplitter.sizes()
            if len(current_sizes) >= 2:
                total = sum(current_sizes)
                if total > 0:
                    return total

        if not hasattr(self.parent, "rightPartInnerWidget"):
            return 600

        width = self.parent.rightPartInnerWidget.width()
        if width <= 0:
            return 600
        return width

    def cleanup(self) -> None:
        """
        清理资源

        停止动画，取消事件订阅。
        """
        self._stop_existing_animation()

        event_bus = EventBus.get_instance()
        event_bus.unsubscribe(EventType.LOG_MESSAGE, self._on_log_message)
        event_bus.unsubscribe(EventType.STEP_CHANGED, self._on_step_changed)

    @property
    def is_expanded(self) -> bool:
        """
        日志面板是否展开

        Returns:
            bool: True表示展开
        """
        return self._log_panel_expanded
