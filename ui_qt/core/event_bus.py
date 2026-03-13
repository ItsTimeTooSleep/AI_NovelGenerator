# -*- coding: utf-8 -*-
"""
事件总线模块

提供模块间的松耦合通信机制，使用单例模式实现全局事件总线。

主要功能:
- 事件发布 (publish)
- 事件订阅 (subscribe)
- 事件取消订阅 (unsubscribe)
- 类型安全的事件定义

使用示例:
    from ui_qt.core import EventBus, EventType

    # 订阅事件
    def on_chapter_changed(event):
        print(f"Chapter changed: {event.data.get('chapter_num')}")

    event_bus = EventBus.get_instance()
    event_bus.subscribe(EventType.CHAPTER_CHANGED, on_chapter_changed)

    # 发布事件
    event_bus.publish(
        EventType.CHAPTER_CHANGED,
        source="ChapterLoader",
        chapter_num=5,
        has_content=True
    )
"""

from dataclasses import dataclass
from enum import Enum, auto
import time
from typing import Any, Callable, Dict, List, Optional
from core import get_logger

logger = get_logger()


class EventType(Enum):
    """
    事件类型枚举

    定义系统中所有可能的事件类型，确保类型安全。
    """

    PROJECT_LOADED = auto()
    PROJECT_UNLOADED = auto()
    CHAPTER_CHANGED = auto()
    GENERATION_STARTED = auto()
    GENERATION_FINISHED = auto()
    GENERATION_ERROR = auto()
    LOG_MESSAGE = auto()
    UI_STATE_CHANGED = auto()
    SKIP_BUTTONS_UPDATED = auto()
    STEP_CHANGED = auto()


@dataclass
class Event:
    """
    事件数据类

    封装事件的完整信息，包括类型、源、数据和时间戳。

    Attributes:
        type: 事件类型 (EventType)
        source: 事件源名称 (str)
        data: 事件数据字典 (Dict[str, Any], optional)
        timestamp: 事件时间戳 (float, optional)
    """

    type: EventType
    source: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


class EventBus:
    """
    事件总线 - 单例模式

    提供模块间的松耦合通信机制。所有模块通过事件总线通信，
    而不是直接依赖彼此，降低耦合度。

    使用单例模式确保全局只有一个事件总线实例。
    """

    _instance: Optional["EventBus"] = None
    _subscribers: Dict[EventType, List[Callable]] = {}
    _initialized: bool = False

    def __new__(cls):
        """
        创建或获取单例实例

        Returns:
            EventBus: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {t: [] for t in EventType}
            cls._instance._initialized = True
        return cls._instance

    @classmethod
    def get_instance(cls) -> "EventBus":
        """
        获取单例实例（便捷方法）

        Returns:
            EventBus: 单例实例
        """
        return cls()

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        订阅事件

        当指定类型的事件发布时，回调函数会被调用。

        Args:
            event_type: 要订阅的事件类型
            callback: 回调函数，签名为 callback(event: Event) -> None

        Example:
            def handler(event: Event):
                print(event.data)

            event_bus.subscribe(EventType.CHAPTER_CHANGED, handler)
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(
                "event_bus",
                f"订阅事件: {event_type.name}, 订阅者数量: {len(self._subscribers[event_type])}",
            )

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        取消订阅事件

        Args:
            event_type: 要取消订阅的事件类型
            callback: 要移除的回调函数
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event_type: EventType, source: str, **data) -> None:
        """
        发布事件

        向所有订阅了该事件类型的回调函数发送事件。

        Args:
            event_type: 事件类型
            source: 事件源名称（通常是模块名或类名）
            **data: 事件数据，作为关键字参数传递

        Example:
            event_bus.publish(
                EventType.CHAPTER_CHANGED,
                source="ChapterLoader",
                chapter_num=5,
                has_content=True
            )
        """
        event = Event(type=event_type, source=source, data=data, timestamp=time.time())
        logger.debug(
            "event_bus",
            f"发布事件: {event_type.name}, 来源: {source}, 订阅者数: {len(self._subscribers[event_type])}",
        )

        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    "event_bus",
                    f"事件回调错误: {event_type.name}, 回调: {callback.__name__}, 错误: {e}",
                )

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        获取指定事件类型的订阅者数量

        Args:
            event_type: 事件类型

        Returns:
            int: 订阅者数量
        """
        return len(self._subscribers[event_type])

    def clear_all_subscribers(self) -> None:
        """
        清除所有订阅者

        警告: 此方法仅用于测试或重置状态，生产环境慎用。
        """
        for event_type in EventType:
            self._subscribers[event_type].clear()
