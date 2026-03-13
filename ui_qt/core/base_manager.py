# -*- coding: utf-8 -*-
"""
管理器基类模块

定义所有管理器的统一接口规范，确保管理器具有一致的行为模式。

主要功能:
- 定义管理器生命周期方法 (initialize, cleanup)
- 提供通用的状态跟踪
- 强制子类实现必要方法

使用示例:
    from ui_qt.core import BaseManager

    class MyManager(BaseManager):
        def __init__(self, parent=None):
            super().__init__(parent)

        def initialize(self):
            # 初始化逻辑
            self._initialized = True

        def cleanup(self):
            # 清理逻辑
            pass
"""

from abc import ABC, abstractmethod
from typing import Optional

from PyQt5.QtWidgets import QWidget


class BaseManager(ABC):
    """
    管理器基类（抽象基类）

    所有管理器都应继承此类，提供统一的接口规范。
    管理器负责特定功能域的管理，遵循单一职责原则。

    Attributes:
        parent: 父级Widget，通常是HomeTab或MainWindow
        _initialized: 是否已初始化标志
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化管理器

        Args:
            parent: 父级Widget，通常是HomeTab
        """
        self.parent = parent
        self._initialized: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """
        初始化管理器（抽象方法，子类必须实现）

        在此方法中执行需要的初始化操作，如：
        - 初始化内部状态
        - 连接信号槽
        - 订阅事件总线

        实现时必须设置 self._initialized = True
        """

    def cleanup(self) -> None:
        """
        清理资源

        在管理器销毁前调用，用于释放资源，如：
        - 断开信号槽连接
        - 取消事件订阅
        - 释放定时器等资源

        子类可按需重写此方法。
        """

    @property
    def is_initialized(self) -> bool:
        """
        是否已初始化

        Returns:
            bool: True表示已初始化
        """
        return self._initialized

    def require_initialized(self) -> None:
        """
        检查是否已初始化，未初始化则抛出异常

        Raises:
            RuntimeError: 如果管理器未初始化
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} is not initialized")

    def __repr__(self) -> str:
        """
        字符串表示

        Returns:
            str: 管理器的字符串表示
        """
        return f"<{self.__class__.__name__} initialized={self._initialized}>"
