# -*- coding: utf-8 -*-
"""
AI Novel Generator - 样式与主题模块
==================================

本模块定义了应用程序的样式常量和颜色主题：
- 深色/浅色主题颜色定义
- QSS 样式表
- 书籍封面颜色生成函数

主要组件：
- ThemeManager: 统一主题管理器
- Styles: 样式表集合
- get_book_cover_color: 生成书籍封面颜色的函数
"""

from PyQt5.QtGui import QColor
from qfluentwidgets import isDarkTheme


class ThemeManager:
    """
    主题管理器，统一管理应用程序的主题颜色

    提供集中式的颜色管理，支持深色/浅色模式切换，
    使用语义化的颜色名称，避免在代码中硬编码颜色值。
    """

    class Colors:
        """
        语义化颜色定义枚举
        """

        # 毛玻璃效果颜色
        GLASS_BG = "GLASS_BG"
        GLASS_BORDER = "GLASS_BORDER"
        GLASS_HOVER_BG = "GLASS_HOVER_BG"
        GLASS_HOVER_BORDER = "GLASS_HOVER_BORDER"

        # 文本颜色
        TEXT_PRIMARY = "TEXT_PRIMARY"
        TEXT_SECONDARY = "TEXT_SECONDARY"
        TEXT_TERTIARY = "TEXT_TERTIARY"
        TEXT_INVERTED = "TEXT_INVERTED"

        # 背景颜色
        BG_PRIMARY = "BG_PRIMARY"
        BG_SECONDARY = "BG_SECONDARY"
        BG_OVERLAY = "BG_OVERLAY"
        BG_CARD = "BG_CARD"

        # 边框颜色
        BORDER_PRIMARY = "BORDER_PRIMARY"
        BORDER_SECONDARY = "BORDER_SECONDARY"

        # 状态颜色
        SUCCESS = "SUCCESS"
        ERROR = "ERROR"
        WARNING = "WARNING"
        INFO = "INFO"

        # 差异显示背景颜色
        SUCCESS_BG = "SUCCESS_BG"
        ERROR_BG = "ERROR_BG"

        # 品牌颜色
        PRIMARY = "PRIMARY"
        PRIMARY_LIGHT = "PRIMARY_LIGHT"
        PRIMARY_DARK = "PRIMARY_DARK"
        SECONDARY = "SECONDARY"
        ACCENT = "ACCENT"

        # UI组件特定颜色
        SCROLLBAR_BG = "SCROLLBAR_BG"
        SCROLLBAR_HANDLE = "SCROLLBAR_HANDLE"
        SCROLLBAR_HANDLE_HOVER = "SCROLLBAR_HANDLE_HOVER"

        SELECTION_BG = "SELECTION_BG"
        SELECTION_TEXT = "SELECTION_TEXT"

        LIST_ITEM_HOVER = "LIST_ITEM_HOVER"
        LIST_ITEM_SELECTED = "LIST_ITEM_SELECTED"

        # 搜索匹配颜色
        SEARCH_MATCH_BG = "SEARCH_MATCH_BG"
        SEARCH_MATCH_CURRENT_BG = "SEARCH_MATCH_CURRENT_BG"
        SEARCH_MATCH_FG = "SEARCH_MATCH_FG"

        # 步骤进度颜色
        STEP_IDLE = "STEP_IDLE"
        STEP_ACTIVE = "STEP_ACTIVE"
        STEP_COMPLETED = "STEP_COMPLETED"
        STEP_ERROR = "STEP_ERROR"

        # 阴影颜色
        SHADOW_PRIMARY = "SHADOW_PRIMARY"

        # 特殊品牌颜色
        PRO_MODE = "PRO_MODE"

    # 深色模式调色板
    _DARK_PALETTE = {
        Colors.GLASS_BG: "#1f2937",
        Colors.GLASS_BORDER: "#374151",
        Colors.GLASS_HOVER_BG: "#374151",
        Colors.GLASS_HOVER_BORDER: "#8B5CF6",
        Colors.TEXT_PRIMARY: "#ffffff",
        Colors.TEXT_SECONDARY: "#d1d5db",
        Colors.TEXT_TERTIARY: "#9ca3af",
        Colors.TEXT_INVERTED: "#000000",
        Colors.BG_PRIMARY: "#111827",
        Colors.BG_SECONDARY: "#1f2937",
        Colors.BG_OVERLAY: "#111827",
        Colors.BG_CARD: "#1f2937",
        Colors.BORDER_PRIMARY: "#374151",
        Colors.BORDER_SECONDARY: "#1f2937",
        Colors.SUCCESS: "#10B981",
        Colors.ERROR: "#EF4444",
        Colors.WARNING: "#F59E0B",
        Colors.INFO: "#3B82F6",
        Colors.SUCCESS_BG: "#064E3B",
        Colors.ERROR_BG: "#7F1D1D",
        Colors.PRIMARY: "#8B5CF6",
        Colors.PRIMARY_LIGHT: "#A78BFA",
        Colors.PRIMARY_DARK: "#7C3AED",
        Colors.SECONDARY: "#06B6D4",
        Colors.ACCENT: "#10B981",
        Colors.SCROLLBAR_BG: "#111827",
        Colors.SCROLLBAR_HANDLE: "#4b5563",
        Colors.SCROLLBAR_HANDLE_HOVER: "#6b7280",
        Colors.SELECTION_BG: "#8B5CF6",
        Colors.SELECTION_TEXT: "#ffffff",
        Colors.LIST_ITEM_HOVER: "#374151",
        Colors.LIST_ITEM_SELECTED: "#7C3AED",
        Colors.SEARCH_MATCH_BG: "#FCD34D",
        Colors.SEARCH_MATCH_CURRENT_BG: "#FBBF24",
        Colors.SEARCH_MATCH_FG: "#000000",
        Colors.STEP_IDLE: "#6b7280",
        Colors.STEP_ACTIVE: "#8B5CF6",
        Colors.STEP_COMPLETED: "#10B981",
        Colors.STEP_ERROR: "#EF4444",
        Colors.SHADOW_PRIMARY: "#8B5CF6",
        Colors.PRO_MODE: "#EC4899",
    }

    # 浅色模式调色板
    _LIGHT_PALETTE = {
        Colors.GLASS_BG: "#ffffff",
        Colors.GLASS_BORDER: "#e5e7eb",
        Colors.GLASS_HOVER_BG: "#f3f4f6",
        Colors.GLASS_HOVER_BORDER: "#8B5CF6",
        Colors.TEXT_PRIMARY: "#1f2937",
        Colors.TEXT_SECONDARY: "#4b5563",
        Colors.TEXT_TERTIARY: "#6b7280",
        Colors.TEXT_INVERTED: "#ffffff",
        Colors.BG_PRIMARY: "#f9fafb",
        Colors.BG_SECONDARY: "#ffffff",
        Colors.BG_OVERLAY: "#f9fafb",
        Colors.BG_CARD: "#ffffff",
        Colors.BORDER_PRIMARY: "#e5e7eb",
        Colors.BORDER_SECONDARY: "#f3f4f6",
        Colors.SUCCESS: "#10B981",
        Colors.ERROR: "#EF4444",
        Colors.WARNING: "#F59E0B",
        Colors.INFO: "#3B82F6",
        Colors.SUCCESS_BG: "#D1FAE5",
        Colors.ERROR_BG: "#FEE2E2",
        Colors.PRIMARY: "#8B5CF6",
        Colors.PRIMARY_LIGHT: "#A78BFA",
        Colors.PRIMARY_DARK: "#7C3AED",
        Colors.SECONDARY: "#06B6D4",
        Colors.ACCENT: "#10B981",
        Colors.SCROLLBAR_BG: "#f9fafb",
        Colors.SCROLLBAR_HANDLE: "#d1d5db",
        Colors.SCROLLBAR_HANDLE_HOVER: "#9ca3af",
        Colors.SELECTION_BG: "#8B5CF6",
        Colors.SELECTION_TEXT: "#ffffff",
        Colors.LIST_ITEM_HOVER: "#f3f4f6",
        Colors.LIST_ITEM_SELECTED: "#A78BFA",
        Colors.SEARCH_MATCH_BG: "#FCD34D",
        Colors.SEARCH_MATCH_CURRENT_BG: "#FBBF24",
        Colors.SEARCH_MATCH_FG: "#000000",
        Colors.STEP_IDLE: "#9ca3af",
        Colors.STEP_ACTIVE: "#8B5CF6",
        Colors.STEP_COMPLETED: "#10B981",
        Colors.STEP_ERROR: "#EF4444",
        Colors.SHADOW_PRIMARY: "#8B5CF6",
        Colors.PRO_MODE: "#EC4899",
    }

    @classmethod
    def get_color(cls, color_name: str, is_dark: bool = None) -> str:
        """
        获取指定名称和主题的颜色值

        Args:
            color_name: 颜色名称（使用 ThemeManager.Colors 枚举）
            is_dark: 是否为深色模式，如果为 None 则自动检测

        Returns:
            str: 颜色值字符串 (hex 或 rgba)
        """
        if is_dark is None:
            is_dark = isDarkTheme()
        palette = cls._DARK_PALETTE if is_dark else cls._LIGHT_PALETTE
        return palette.get(color_name, "#ff00ff")


class _Styles:
    """
    样式表集合
    """

    @property
    def QListWidget(self):
        is_dark = isDarkTheme()
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.LIST_ITEM_HOVER, is_dark)
        selected_bg = ThemeManager.get_color(
            ThemeManager.Colors.LIST_ITEM_SELECTED, is_dark
        )

        return f"""
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            color: {text_color};
        }}
        QListWidget::item {{
            padding: 10px 12px;
            border-radius: 8px;
            color: {text_color};
            margin: 2px 4px;
        }}
        QListWidget::item:hover {{
            background-color: {hover_bg};
        }}
        QListWidget::item:selected {{
            background-color: {selected_bg};
            color: {text_color};
        }}
        """

    @property
    def StatusLabelSuccess(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.SUCCESS, is_dark)
        return f"color: {color}; font-weight: bold;"

    @property
    def StatusLabelError(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.ERROR, is_dark)
        return f"color: {color}; font-weight: bold;"

    @property
    def StatusLabelWarning(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.WARNING, is_dark)
        return f"color: {color}; font-weight: bold;"

    @property
    def StatusLabelGray(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY, is_dark)
        return f"color: {color};"

    @property
    def StatusLabelInfo(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.INFO, is_dark)
        return f"color: {color}; font-weight: bold;"

    @property
    def ProjectCard(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.GLASS_BG, is_dark)
        border_color = ThemeManager.get_color(ThemeManager.Colors.GLASS_BORDER, is_dark)
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.GLASS_HOVER_BG, is_dark)
        hover_border = ThemeManager.get_color(
            ThemeManager.Colors.GLASS_HOVER_BORDER, is_dark
        )
        ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)

        return f"""
        ProjectCard {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
        }}
        ProjectCard:hover {{
            background-color: {hover_bg};
            border: 2px solid {hover_border};
            border-radius: 12px;
        }}
        """

    @property
    def ProjectCardShadow(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.GLASS_BG, is_dark)
        border_color = ThemeManager.get_color(ThemeManager.Colors.GLASS_BORDER, is_dark)
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.GLASS_HOVER_BG, is_dark)
        hover_border = ThemeManager.get_color(
            ThemeManager.Colors.GLASS_HOVER_BORDER, is_dark
        )
        return f"""
        CardWidget {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
        }}
        CardWidget:hover {{
            background-color: {hover_bg};
            border: 2px solid {hover_border};
            border-radius: 12px;
        }}
        """

    @property
    def ContentCard(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_CARD, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )

        return f"""
        QWidget#contentCard {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 16px;
        }}
        """

    @property
    def ScrollArea(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.SCROLLBAR_BG, is_dark)
        handle_color = ThemeManager.get_color(
            ThemeManager.Colors.SCROLLBAR_HANDLE, is_dark
        )
        handle_hover = ThemeManager.get_color(
            ThemeManager.Colors.SCROLLBAR_HANDLE_HOVER, is_dark
        )

        return f"""
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            width: 8px;
            background: {bg_color};
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle_color};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            height: 8px;
            background: {bg_color};
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle_color};
            min-width: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
        """

    @property
    def ScrollBar(self):
        """
        纯滚动条样式，适用于任何有滚动条的控件

        Returns:
            str: 滚动条样式字符串，支持主题感知
        """
        is_dark = isDarkTheme()
        handle_color = ThemeManager.get_color(
            ThemeManager.Colors.SCROLLBAR_HANDLE, is_dark
        )
        handle_hover = ThemeManager.get_color(
            ThemeManager.Colors.SCROLLBAR_HANDLE_HOVER, is_dark
        )

        return f"""
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {handle_color};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle_color};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
        """

    @property
    def PlainTextEdit(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        selection_bg = ThemeManager.get_color(ThemeManager.Colors.SELECTION_BG, is_dark)
        selection_text_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_PRIMARY, is_dark
        )
        focus_border = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        focus_bg = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)

        return f"""
        QPlainTextEdit {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px;
            color: {text_color};
            selection-background-color: {selection_bg};
            selection-color: {selection_text_color};
        }}
        QPlainTextEdit:focus {{
            border: 1px solid {focus_border};
            background-color: {focus_bg};
        }}
        """

    @property
    def TextEdit(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_PRIMARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        selection_bg = ThemeManager.get_color(ThemeManager.Colors.SELECTION_BG, is_dark)
        selection_text_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_PRIMARY, is_dark
        )
        focus_border = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        focus_bg = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)

        return f"""
        QTextEdit {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px;
            color: {text_color};
            selection-background-color: {selection_bg};
            selection-color: {selection_text_color};
        }}
        QTextEdit:focus {{
            border: 1px solid {focus_border};
            background-color: {focus_bg};
        }}
        """

    @property
    def TransparentBackground(self):
        return "background-color: transparent;"

    @property
    def HintText(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY, is_dark)
        return f"color: {color};"

    @property
    def SecondaryText(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY, is_dark)
        return f"color: {color};"

    @property
    def StepProgressContainer(self):
        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_OVERLAY, is_dark)
        return f"""
            QWidget#step1ProgressContainer {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
        """

    @property
    def MenuButton(self):
        is_dark = isDarkTheme()
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.GLASS_HOVER_BG, is_dark)
        pressed_bg = ThemeManager.get_color(
            ThemeManager.Colors.GLASS_HOVER_BORDER, is_dark
        )

        return f"""
            ToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            ToolButton:hover {{
                background-color: {hover_bg};
            }}
            ToolButton:pressed {{
                background-color: {pressed_bg};
            }}
        """

    @property
    def DangerButton(self):
        is_dark = isDarkTheme()
        error_color = ThemeManager.get_color(ThemeManager.Colors.ERROR, is_dark)
        return f"""
            PushButton {{ color: {error_color}; }}
            PushButton:hover {{ color: {error_color}; }}
        """

    @property
    def PlaceholderTitle(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY, is_dark)
        return f"font-size: 18px; color: {color};"

    @property
    def PlaceholderDescription(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY, is_dark)
        return f"color: {color}; font-size: 14px;"

    @property
    def ChapterStatusSuccess(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.SUCCESS, is_dark)
        return f"color: {color};"

    @property
    def ChapterStatusNormal(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.TEXT_TERTIARY, is_dark)
        return f"color: {color};"

    @property
    def WarningText(self):
        is_dark = isDarkTheme()
        color = ThemeManager.get_color(ThemeManager.Colors.WARNING, is_dark)
        return f"color: {color}; font-size: 12px;"

    @property
    def BaseScrollArea(self):
        return """
            BaseProjectInterface {{ background-color: transparent; border: none; }}
        """

    @property
    def BaseView(self):
        return """
            QWidget#projectBaseView {{ background-color: transparent; }}
        """

    @property
    def PlaceholderWidget(self):
        return """
            QWidget#placeholderWidget {{
                background-color: transparent;
            }}
        """


Styles = _Styles()


def get_book_cover_color(title, is_dark=True):
    """
    为书籍封面生成一致的柔和现代颜色

    根据书籍标题的哈希值生成一个固定的颜色，
    确保同一本书总是显示相同的封面颜色。

    Args:
        title: 书籍标题，用于生成哈希值
        is_dark: 是否为深色模式，默认 True

    Returns:
        QColor: 生成的颜色对象
    """
    hash_val = sum(ord(c) for c in title)

    color_palette = [
        QColor(139, 92, 246),
        QColor(6, 182, 212),
        QColor(16, 185, 129),
        QColor(245, 158, 11),
        QColor(236, 72, 153),
        QColor(59, 130, 246),
    ]

    return color_palette[hash_val % len(color_palette)]
