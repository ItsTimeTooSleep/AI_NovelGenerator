# -*- coding: utf-8 -*-
"""
通知管理器模块

提供统一的通知系统，封装 InfoBar 的调用，支持：
- 统一的通知样式和位置
- 错误消息点击复制功能
- 通知历史记录
- 通过 EventBus 发布通知事件

使用示例:
    from ui_qt.utils.notification_manager import NotificationManager

    notify = NotificationManager(parent_widget)

    notify.success("保存成功", "配置已保存")
    notify.error("错误", "连接失败，点击复制错误信息", copyable=True)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition, PushButton, FluentIcon as FIF


class NotificationType(Enum):
    """
    通知类型枚举

    Attributes:
        SUCCESS: 成功通知
        ERROR: 错误通知
        WARNING: 警告通知
        INFO: 信息通知
    """

    SUCCESS = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class NotificationRecord:
    """
    通知记录数据类

    存储单条通知的完整信息，用于历史记录功能。

    Attributes:
        type: 通知类型
        title: 通知标题
        content: 通知内容
        timestamp: 通知时间戳
        copyable: 是否可复制
        duration: 显示时长（毫秒）
    """

    type: NotificationType
    title: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    copyable: bool = False
    duration: int = 3000


class NotificationManager:
    """
    通知管理器

    提供统一的通知系统，封装 InfoBar 的调用。

    Features:
        - 统一的通知样式和位置
        - 错误消息点击复制功能
        - 通知历史记录（最近 100 条）
        - 支持持久通知（duration=-1）
        - 线程安全的通知显示

    Example:
        notify = NotificationManager(parent_widget)

        notify.success("保存成功", "配置已保存")
        notify.error("错误", "连接失败", copyable=True)
        notify.warning("警告", "磁盘空间不足")
        notify.info("提示", "正在处理...", duration=-1)
    """

    _MAX_HISTORY = 100

    def __init__(
        self,
        parent: QWidget,
        position: InfoBarPosition = InfoBarPosition.TOP_RIGHT,
        default_duration: int = 3000,
    ):
        """
        初始化通知管理器

        Args:
            parent: 父控件，用于确定通知显示位置
            position: 通知显示位置，默认右上角
            default_duration: 默认显示时长（毫秒），默认 3000ms
        """
        self._parent = parent
        self._position = position
        self._default_duration = default_duration
        self._history: List[NotificationRecord] = []
        self._active_bars: List[InfoBar] = []

    def _get_parent_window(self) -> QWidget:
        """
        获取父窗口

        Returns:
            QWidget: 父窗口控件
        """
        return self._parent.window() if self._parent else None

    def _add_to_history(self, record: NotificationRecord) -> None:
        """
        添加通知到历史记录

        Args:
            record: 通知记录
        """
        self._history.append(record)
        if len(self._history) > self._MAX_HISTORY:
            self._history.pop(0)

    def _create_copy_button(self, content: str) -> PushButton:
        """
        创建复制按钮

        Args:
            content: 要复制的内容

        Returns:
            PushButton: 复制按钮控件
        """
        copy_btn = PushButton("复制", None)
        copy_btn.setFixedHeight(28)

        def on_copy():
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            self._show_copy_success()

        copy_btn.clicked.connect(on_copy)
        return copy_btn

    def _show_copy_success(self) -> None:
        """
        显示复制成功提示
        """
        parent = self._get_parent_window()
        if not parent:
            return

        InfoBar.success(
            title="",
            content="已复制到剪贴板",
            parent=parent,
            position=self._position,
            duration=1500,
        )

    def _show_notification(
        self,
        notification_type: NotificationType,
        title: str,
        content: str,
        duration: Optional[int] = None,
        copyable: bool = False,
        isClosable: bool = True,
    ) -> Optional[InfoBar]:
        """
        显示通知（内部方法）

        Args:
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），None 使用默认值，-1 表示持久显示
            copyable: 是否显示复制按钮
            isClosable: 是否显示关闭按钮

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例，如果创建失败返回 None
        """
        parent = self._get_parent_window()
        if not parent:
            return None

        actual_duration = duration if duration is not None else self._default_duration

        record = NotificationRecord(
            type=notification_type,
            title=title,
            content=content,
            copyable=copyable,
            duration=actual_duration,
        )
        self._add_to_history(record)

        type_method_map = {
            NotificationType.SUCCESS: InfoBar.success,
            NotificationType.ERROR: InfoBar.error,
            NotificationType.WARNING: InfoBar.warning,
            NotificationType.INFO: InfoBar.info,
        }

        method = type_method_map.get(notification_type, InfoBar.info)

        bar = method(
            title=title,
            content=content,
            parent=parent,
            position=self._position,
            duration=actual_duration,
            isClosable=isClosable,
        )

        if copyable and content:
            copy_btn = self._create_copy_button(content)
            bar.addWidget(copy_btn)

        self._active_bars.append(bar)
        bar.closedSignal.connect(lambda: self._remove_bar(bar))

        return bar

    def _remove_bar(self, bar: InfoBar) -> None:
        """
        从活动列表中移除 InfoBar

        Args:
            bar: 要移除的 InfoBar
        """
        if bar in self._active_bars:
            self._active_bars.remove(bar)

    def success(
        self,
        title: str,
        content: str = "",
        duration: Optional[int] = None,
    ) -> Optional[InfoBar]:
        """
        显示成功通知

        Args:
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），None 使用默认值

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例

        Example:
            notify.success("保存成功", "配置已保存到文件")
        """
        return self._show_notification(
            NotificationType.SUCCESS, title, content, duration
        )

    def error(
        self,
        title: str,
        content: str = "",
        duration: Optional[int] = None,
        copyable: bool = True,
    ) -> Optional[InfoBar]:
        """
        显示错误通知

        Args:
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），None 使用默认值
            copyable: 是否显示复制按钮，默认 True

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例

        Example:
            notify.error("连接失败", "无法连接到服务器: timeout", copyable=True)
        """
        return self._show_notification(
            NotificationType.ERROR, title, content, duration, copyable=copyable
        )

    def warning(
        self,
        title: str,
        content: str = "",
        duration: Optional[int] = None,
    ) -> Optional[InfoBar]:
        """
        显示警告通知

        Args:
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），None 使用默认值

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例

        Example:
            notify.warning("磁盘空间不足", "剩余空间不足 1GB")
        """
        return self._show_notification(
            NotificationType.WARNING, title, content, duration
        )

    def info(
        self,
        title: str,
        content: str = "",
        duration: Optional[int] = None,
    ) -> Optional[InfoBar]:
        """
        显示信息通知

        Args:
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），None 使用默认值，-1 表示持久显示

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例

        Example:
            notify.info("正在处理", "请稍候...", duration=-1)
        """
        return self._show_notification(NotificationType.INFO, title, content, duration)

    def persistent(
        self,
        notification_type: NotificationType,
        title: str,
        content: str = "",
        copyable: bool = False,
    ) -> Optional[InfoBar]:
        """
        显示持久通知（不会自动关闭）

        Args:
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            copyable: 是否显示复制按钮

        Returns:
            Optional[InfoBar]: 创建的 InfoBar 实例

        Example:
            bar = notify.persistent(NotificationType.INFO, "处理中", "正在生成内容...")
            bar.close()
        """
        return self._show_notification(
            notification_type, title, content, duration=-1, copyable=copyable
        )

    def show_from_thread(
        self,
        notification_type: NotificationType,
        title: str,
        content: str = "",
        duration: Optional[int] = None,
        copyable: bool = False,
    ) -> None:
        """
        从非主线程显示通知（线程安全）

        使用 QTimer.singleShot 确保在主线程中创建通知。

        Args:
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒）
            copyable: 是否显示复制按钮

        Example:
            def worker_thread():
                notify.show_from_thread(NotificationType.SUCCESS, "完成", "后台任务完成")
        """
        QTimer.singleShot(
            0,
            lambda: self._show_notification(
                notification_type, title, content, duration, copyable
            ),
        )

    def get_history(self, limit: int = 20) -> List[NotificationRecord]:
        """
        获取通知历史记录

        Args:
            limit: 返回的最大记录数，默认 20

        Returns:
            List[NotificationRecord]: 通知记录列表（按时间倒序）

        Example:
            history = notify.get_history(10)
            for record in history:
                print(f"[{record.timestamp}] {record.title}: {record.content}")
        """
        return self._history[-limit:][::-1]

    def clear_history(self) -> None:
        """
        清除通知历史记录
        """
        self._history.clear()

    def close_all(self) -> None:
        """
        关闭所有活动中的通知
        """
        for bar in self._active_bars[:]:
            try:
                bar.close()
            except Exception:
                pass
        self._active_bars.clear()

    def update_parent(self, parent: QWidget) -> None:
        """
        更新父控件

        Args:
            parent: 新的父控件
        """
        self._parent = parent

    @property
    def position(self) -> InfoBarPosition:
        """
        获取当前通知位置

        Returns:
            InfoBarPosition: 通知位置
        """
        return self._position

    @position.setter
    def position(self, value: InfoBarPosition) -> None:
        """
        设置通知位置

        Args:
            value: 新的通知位置
        """
        self._position = value

    @property
    def default_duration(self) -> int:
        """
        获取默认显示时长

        Returns:
            int: 默认显示时长（毫秒）
        """
        return self._default_duration

    @default_duration.setter
    def default_duration(self, value: int) -> None:
        """
        设置默认显示时长

        Args:
            value: 新的默认显示时长（毫秒）
        """
        self._default_duration = value


def create_notify(parent: QWidget, **kwargs) -> NotificationManager:
    """
    创建通知管理器的便捷函数

    Args:
        parent: 父控件
        **kwargs: 传递给 NotificationManager 的其他参数

    Returns:
        NotificationManager: 通知管理器实例

    Example:
        notify = create_notify(self, position=InfoBarPosition.BOTTOM_RIGHT)
    """
    return NotificationManager(parent, **kwargs)
