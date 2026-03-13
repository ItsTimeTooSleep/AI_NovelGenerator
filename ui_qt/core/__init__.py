# -*- coding: utf-8 -*-
"""
核心基础设施模块

本模块提供 UI 层的核心基础设施，包括：
- event_bus: 事件总线，用于模块间松耦合通信
- base_manager: 管理器基类，定义统一接口规范
"""

from .base_manager import BaseManager
from .event_bus import Event, EventBus, EventType

__all__ = [
    "EventBus",
    "Event",
    "EventType",
    "BaseManager",
]
