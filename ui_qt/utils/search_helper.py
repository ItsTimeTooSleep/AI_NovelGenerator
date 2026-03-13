"""
搜索相关工具
==============

目前预留占位，用于：
- 章节/角色等文本内容的搜索与过滤
- 后续统一封装搜索逻辑，供各个 tab 复用
"""

from __future__ import annotations

from typing import Callable, Iterable, List


def simple_filter(
    items: Iterable[str], keyword: str, key: Callable[[str], str] | None = None
) -> List[str]:
    """简单包含匹配过滤，作为后续复杂搜索的基础实现。"""
    keyword = (keyword or "").strip()
    if not keyword:
        return list(items)

    key_func = key or (lambda x: x)
    lowered = keyword.lower()
    return [item for item in items if lowered in key_func(item).lower()]


__all__ = ["simple_filter"]
