# -*- coding: utf-8 -*-
"""
Token消耗信息对话框（完善版）
============================

本模块实现了完善的Token消耗信息展示对话框，包含：
- 顶部总览卡片区（4个卡片）
- 使用分析区（支持4种视图切换 + 悬浮详情）
- 多模型明细区（与使用分析联动）
"""

import csv
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    DropDownPushButton,
    MessageBoxBase,
    SegmentedWidget,
    StrongBodyLabel,
    SubtitleLabel,
    TableWidget,
    TitleLabel,
    ToolButton,
    isDarkTheme,
)
from qfluentwidgets import FluentIcon as FIF

from core.tokens_manager import (
    TokensManager,
)

from ..utils.dialog_sizer import DialogSizer
from ..utils.styles import Styles, ThemeManager
from .placeholder_widget import PlaceholderWidget


class GlobalStatCard(QFrame):
    """
    全局核心总数据卡片
    """

    def __init__(self, label: str, value: Any, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.value = value
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        is_dark = isDarkTheme()
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_SECONDARY, is_dark)
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )

        self.setStyleSheet(f"""
            GlobalStatCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        label_widget = CaptionLabel(self.label_text, self)
        label_widget.setStyleSheet(f"""
            color: {text_color};
            font-size: 13px;
            font-weight: 500;
        """)
        label_widget.setAlignment(Qt.AlignCenter)

        value_widget = StrongBodyLabel(str(self.value), self)
        value_widget.setStyleSheet(f"""
            color: {primary_color};
            font-size: 24px;
            font-weight: 800;
            font-family: 'Segoe UI', sans-serif;
        """)
        value_widget.setAlignment(Qt.AlignCenter)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)


class DonutChartWidget(QWidget):
    """
    环形图组件
    """

    def __init__(self, data: List[Dict], parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.hovered_index = -1

    def set_data(self, data: List[Dict]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.data:
            return

        total = sum(item["value"] for item in self.data)
        if total == 0:
            return

        center_x = self.width() // 2
        center_y = self.height() // 2
        outer_radius = min(center_x, center_y) - 20
        inner_radius = outer_radius * 0.6

        start_angle = 0
        for i, item in enumerate(self.data):
            value = item["value"]
            color = QColor(item["color"])

            span_angle = int((value / total) * 360 * 16)

            path = QPainterPath()
            path.moveTo(center_x, center_y)
            path.arcTo(
                center_x - outer_radius,
                center_y - outer_radius,
                outer_radius * 2,
                outer_radius * 2,
                -start_angle,
                -span_angle / 16,
            )
            path.closeSubpath()

            inner_path = QPainterPath()
            inner_path.moveTo(center_x, center_y)
            inner_path.arcTo(
                center_x - inner_radius,
                center_y - inner_radius,
                inner_radius * 2,
                inner_radius * 2,
                -start_angle,
                -span_angle / 16,
            )
            inner_path.closeSubpath()

            donut_path = path.subtracted(inner_path)

            if i == self.hovered_index:
                painter.setBrush(QBrush(color.lighter(120)))
            else:
                painter.setBrush(QBrush(color))

            painter.setPen(Qt.NoPen)
            painter.drawPath(donut_path)

            start_angle += span_angle / 16

    def mouseMoveEvent(self, event):
        if not self.data:
            return

        total = sum(item["value"] for item in self.data)
        if total == 0:
            return

        center_x = self.width() // 2
        center_y = self.height() // 2

        dx = event.x() - center_x
        dy = event.y() - center_y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < 20 or distance > min(center_x, center_y) - 20:
            self.hovered_index = -1
            QToolTip.hideText()
            self.update()
            return

        if dx == 0:
            if dy > 0:
                angle = 180
            else:
                angle = 0
        else:
            angle = (360 - (dy > 0) * 360 - (dx > 0 and dy < 0) * 360) % 360
            if dx > 0:
                angle = (90 - (dy / abs(dx)) * 45) % 360
            else:
                angle = (270 + (dy / abs(dx)) * 45) % 360

        start_angle = 0
        hovered = -1

        for i, item in enumerate(self.data):
            value = item["value"]
            span_angle = (value / total) * 360

            if start_angle <= angle < start_angle + span_angle:
                hovered = i
                break

            start_angle += span_angle

        if hovered != self.hovered_index:
            self.hovered_index = hovered
            if hovered >= 0:
                item = self.data[hovered]
                tooltip_text = f"{item['label']}\n数值: {item['value']}\n占比: {(item['value']/total*100):.1f}%"
                QToolTip.showText(event.globalPos(), tooltip_text, self)
            else:
                QToolTip.hideText()
            self.update()


class UsageAnalysisWidget(QFrame):
    """
    使用分析组件（支持4种视图切换）
    """

    def __init__(self, tokens_manager: TokensManager, parent=None):
        super().__init__(parent)
        self.tokens_manager = tokens_manager
        self.current_view = "input_output"
        self.current_sub_view = "input"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)

        self.setStyleSheet(f"""
            UsageAnalysisWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        # 标题 + 视图切换器
        header_layout = QHBoxLayout()

        title = SubtitleLabel("使用分析", self)
        title.setStyleSheet(f"""
            color: {text_color};
            font-size: 16px;
            font-weight: 600;
        """)

        self.view_pivot = SegmentedWidget(self)
        self.view_pivot.addItem("input_output", "输入vs输出")
        self.view_pivot.addItem("model", "模型维度")
        self.view_pivot.addItem("step", "步骤维度")
        self.view_pivot.addItem("single_model", "单模型内部")
        self.view_pivot.setCurrentItem("input_output")
        self.view_pivot.currentItemChanged.connect(self._on_view_changed)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.view_pivot)

        layout.addLayout(header_layout)

        # 子视图切换器（用于模型维度）
        self.sub_view_layout = QHBoxLayout()
        self.sub_view_pivot = SegmentedWidget(self)
        self.sub_view_pivot.addItem("input", "输入占比")
        self.sub_view_pivot.addItem("output", "输出占比")
        self.sub_view_pivot.addItem("calls", "调用次数")
        self.sub_view_pivot.setCurrentItem("input")
        self.sub_view_pivot.currentItemChanged.connect(self._on_sub_view_changed)
        self.sub_view_pivot.setVisible(False)

        self.sub_view_layout.addWidget(self.sub_view_pivot)
        self.sub_view_layout.addStretch()
        layout.addLayout(self.sub_view_layout)

        # 内容区域
        self.content_stack = QStackedWidget(self)
        self._create_views()
        layout.addWidget(self.content_stack)

    def _create_views(self):
        total_stats = self.tokens_manager.get_total_stats()

        # 视图A：输入vs输出
        self.view_a = self._create_input_output_view(total_stats)
        self.content_stack.addWidget(self.view_a)

        # 视图B：模型维度
        self.view_b = self._create_model_view(total_stats)
        self.content_stack.addWidget(self.view_b)

        # 视图C：步骤维度
        self.view_c = self._create_step_view(total_stats)
        self.content_stack.addWidget(self.view_c)

        # 视图D：单模型内部
        self.view_d = self._create_single_model_view()
        self.content_stack.addWidget(self.view_d)

    def _create_input_output_view(self, total_stats: Dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        input_tokens = total_stats.get("total_input_tokens", 0)
        output_tokens = total_stats.get("total_output_tokens", 0)
        total_stats.get("total_cached_tokens", 0)
        total = input_tokens + output_tokens

        if total == 0:
            no_data = BodyLabel("暂无使用数据", widget)
            layout.addWidget(no_data, alignment=Qt.AlignCenter)
            return widget

        data = [
            {
                "label": "输入Token",
                "value": input_tokens,
                "color": ThemeManager.get_color(ThemeManager.Colors.INFO),
            },
            {
                "label": "输出Token",
                "value": output_tokens,
                "color": ThemeManager.get_color(ThemeManager.Colors.SUCCESS),
            },
        ]

        chart = DonutChartWidget(data, widget)
        layout.addWidget(chart, alignment=Qt.AlignCenter)

        return widget

    def _create_model_view(self, total_stats: Dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        model_stats = self.tokens_manager.get_model_stats()
        if not model_stats:
            no_data = BodyLabel("暂无模型数据", widget)
            layout.addWidget(no_data, alignment=Qt.AlignCenter)
            return widget

        self._update_model_view_content(layout, model_stats, "input")

        return widget

    def _update_model_view_content(
        self, layout: QVBoxLayout, model_stats: Dict, sub_view: str
    ):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        total_input = sum(
            stats.get("total_input_tokens", 0) for stats in model_stats.values()
        )
        total_output = sum(
            stats.get("total_output_tokens", 0) for stats in model_stats.values()
        )
        total_calls = sum(
            stats.get("record_count", 0) for stats in model_stats.values()
        )

        data = []
        for model_name, stats in model_stats.items():
            if sub_view == "input":
                value = stats.get("total_input_tokens", 0)
                total = total_input
                color = ThemeManager.get_color(ThemeManager.Colors.INFO)
            elif sub_view == "output":
                value = stats.get("total_output_tokens", 0)
                total = total_output
                color = ThemeManager.get_color(ThemeManager.Colors.SUCCESS)
            else:
                value = stats.get("record_count", 0)
                total = total_calls
                color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY)

            data.append({"label": model_name, "value": value, "color": color})

        if total == 0:
            no_data = BodyLabel("暂无数据", self)
            layout.addWidget(no_data, alignment=Qt.AlignCenter)
            return

        chart = DonutChartWidget(data, self)
        layout.addWidget(chart, alignment=Qt.AlignCenter)

    def _create_step_view(self, total_stats: Dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        step_stats = self.tokens_manager.get_step_stats()
        if not step_stats:
            no_data = BodyLabel("暂无步骤数据", widget)
            layout.addWidget(no_data, alignment=Qt.AlignCenter)
            return widget

        data = []
        colors = ["#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#3B82F6"]
        for i, (step_name, stats) in enumerate(step_stats.items()):
            total_tokens = stats.get("total_tokens", 0)
            data.append(
                {
                    "label": step_name,
                    "value": total_tokens,
                    "color": colors[i % len(colors)],
                }
            )

        chart = DonutChartWidget(data, widget)
        layout.addWidget(chart, alignment=Qt.AlignCenter)

        return widget

    def _create_single_model_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.single_model_placeholder = BodyLabel(
            "请先在多模型明细中选择一个模型", widget
        )
        self.single_model_placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.single_model_placeholder, alignment=Qt.AlignCenter)

        self.single_model_content = QWidget()
        self.single_model_layout = QVBoxLayout(self.single_model_content)
        self.single_model_content.setVisible(False)
        layout.addWidget(self.single_model_content)

        return widget

    def update_single_model_view(self, model_name: str):
        if model_name == "全部模型" or not model_name:
            self.single_model_placeholder.setVisible(True)
            self.single_model_content.setVisible(False)
            return

        model_stats = self.tokens_manager.get_model_stats()
        if model_name not in model_stats:
            self.single_model_placeholder.setVisible(True)
            self.single_model_content.setVisible(False)
            return

        self.single_model_placeholder.setVisible(False)
        self.single_model_content.setVisible(True)

        for i in reversed(range(self.single_model_layout.count())):
            self.single_model_layout.itemAt(i).widget().setParent(None)

        stats = model_stats[model_name]
        input_tokens = stats.get("total_input_tokens", 0)
        output_tokens = stats.get("total_output_tokens", 0)
        cached_tokens = stats.get("total_cached_tokens", 0)
        total = input_tokens + output_tokens + cached_tokens

        if total == 0:
            no_data = BodyLabel("该模型暂无数据", self.single_model_content)
            self.single_model_layout.addWidget(no_data, alignment=Qt.AlignCenter)
            return

        data = []
        if input_tokens > 0:
            data.append(
                {
                    "label": "输入Token",
                    "value": input_tokens,
                    "color": ThemeManager.get_color(ThemeManager.Colors.INFO),
                }
            )
        if output_tokens > 0:
            data.append(
                {
                    "label": "输出Token",
                    "value": output_tokens,
                    "color": ThemeManager.get_color(ThemeManager.Colors.SUCCESS),
                }
            )
        if cached_tokens > 0:
            data.append(
                {
                    "label": "缓存Token",
                    "value": cached_tokens,
                    "color": ThemeManager.get_color(ThemeManager.Colors.WARNING),
                }
            )

        chart = DonutChartWidget(data, self.single_model_content)
        self.single_model_layout.addWidget(chart, alignment=Qt.AlignCenter)

    def _on_view_changed(self, view_key: str):
        self.current_view = view_key
        self.sub_view_pivot.setVisible(view_key == "model")

        view_index = ["input_output", "model", "step", "single_model"].index(view_key)
        self.content_stack.setCurrentIndex(view_index)

    def _on_sub_view_changed(self, sub_view_key: str):
        self.current_sub_view = sub_view_key
        model_stats = self.tokens_manager.get_model_stats()
        if model_stats:
            layout = self.view_b.layout()
            self._update_model_view_content(layout, model_stats, sub_view_key)


class ModelDetailTableWidget(TableWidget):
    """
    模型明细表格组件（单条请求记录展示
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setBorderVisible(True)
        self.setAlternatingRowColors(False)
        self.setEditTriggers(self.NoEditTriggers)  # 禁止编辑
        self.setSelectionMode(self.NoSelection)  # 禁止选择

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        header_bg = ThemeManager.get_color(ThemeManager.Colors.BG_OVERLAY, is_dark)
        header_text = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_SECONDARY, is_dark
        )
        item_border = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.LIST_ITEM_HOVER, is_dark)

        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            [
                "请求日期",
                "小说生成步骤",
                "模型名称",
                "输入Token",
                "输入命中缓存Token",
                "输出Token",
            ]
        )

        self.setStyleSheet(f"""
            TableWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                font-size: 14px;
                color: {text_color};
                gridline-color: transparent;
            }}
            TableWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {item_border};
            }}
            TableWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {header_text};
                padding: 14px 16px;
                border: none;
                border-bottom: 1px solid {item_border};
                font-weight: 600;
                font-size: 13px;
            }}
        """)

        # 美化表头
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(120)

        # 手动调整部分列的最小宽度
        for i, width in [(0, 180), (1, 200), (2, 150), (3, 120), (4, 150), (5, 120)]:
            if i < self.columnCount():
                header.resizeSection(i, width)

    def update_data(self, records: List[Dict[str, Any]]):
        """
        更新表格数据

        Args:
            records: Token记录列表，每条记录为一个字典
        """
        from PyQt5.QtWidgets import QTableWidgetItem

        self.setRowCount(len(records))

        for row, record in enumerate(records):
            timestamp_str = record.get("timestamp", "")
            if timestamp_str:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(timestamp_str)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_time = timestamp_str
            else:
                formatted_time = ""

            input_tokens = record.get("input_tokens", 0)
            output_tokens = record.get("output_tokens", 0)
            input_estimated = record.get("input_estimated", False)
            output_estimated = record.get("output_estimated", False)

            if input_tokens == -1:
                input_display = "未知"
            elif input_estimated:
                input_display = f"{input_tokens}(估算)"
            else:
                input_display = str(input_tokens)

            if output_tokens == -1:
                output_display = "未知"
            elif output_estimated:
                output_display = f"{output_tokens}(估算)"
            else:
                output_display = str(output_tokens)

            items = [
                QTableWidgetItem(formatted_time),
                QTableWidgetItem(record.get("step_name", "")),
                QTableWidgetItem(record.get("model_name", "")),
                QTableWidgetItem(input_display),
                QTableWidgetItem(str(record.get("cached_tokens", 0))),
                QTableWidgetItem(output_display),
            ]

            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, col, item)

        self.resizeColumnsToContents()


class NovelTokenStatsDialog(MessageBoxBase):
    """
    小说总体Token消耗统计对话框（完善版）
    支持尺寸自适应和内容滚动。
    """

    def __init__(self, tokens_manager: TokensManager, parent=None):
        super().__init__(parent)
        self.tokens_manager = tokens_manager
        self.current_model = "全部模型"
        self.init_ui()

    def init_ui(self):
        self.widget.setAttribute(Qt.WA_StyledBackground)

        is_dark = isDarkTheme()
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_PRIMARY, is_dark)

        self.widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: none;
                border-radius: 16px;
            }}
        """)

        palette = self.widget.palette()
        palette.setColor(self.widget.backgroundRole(), QColor(bg_color))
        self.widget.setPalette(palette)
        self.widget.setAutoFillBackground(True)

        total_stats = self.tokens_manager.get_total_stats()

        if total_stats["record_count"] == 0:
            self._show_empty_state()
        else:
            self._show_content()

        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)
        self.buttonGroup.setVisible(False)

        sizer = DialogSizer(
            width_ratio=0.70,
            height_ratio=0.75,
            min_width=900,
            min_height=650,
            max_width=1500,
            max_height=950,
        )
        sizer.apply_to_widget(self.widget, parent=self)

    def _show_empty_state(self):
        placeholder = PlaceholderWidget(
            icon=FIF.DOCUMENT,
            title="暂无Token消耗记录",
            description="开始创作后，这里将显示详细的Token消耗统计信息。",
            parent=self,
        )
        placeholder.setMinimumHeight(400)
        self.viewLayout.addWidget(placeholder)

    def _show_content(self):
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            {Styles.ScrollBar}
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 16, 0)
        content_layout.setSpacing(24)

        # 1. 顶部标题区
        header_layout = self._create_header()
        content_layout.addLayout(header_layout)

        # 2. 顶部总览卡片区
        global_stats_layout = self._create_global_stats()
        content_layout.addLayout(global_stats_layout)

        # 3. 使用分析区
        self.usage_analysis = UsageAnalysisWidget(self.tokens_manager, self)
        content_layout.addWidget(self.usage_analysis)

        # 4. 多模型明细区
        model_detail_layout = self._create_model_detail()
        content_layout.addLayout(model_detail_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        self.viewLayout.addWidget(scroll_area)

    def _create_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        is_dark = isDarkTheme()
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)

        title = TitleLabel("Token消耗统计（总体）", self)
        title.setStyleSheet(f"""
            color: {primary_color};
            font-size: 24px;
            font-weight: 800;
            padding: 8px 0;
            background: transparent;
        """)

        layout.addWidget(title)
        layout.addStretch()

        refresh_btn = ToolButton(FIF.SYNC, self)
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self._refresh_data)
        refresh_btn.setToolTip("刷新数据")

        close_btn = ToolButton(FIF.CLOSE, self)
        close_btn.setFixedSize(36, 36)
        close_btn.clicked.connect(self.accept)
        close_btn.setToolTip("关闭")

        layout.addWidget(refresh_btn)
        layout.addWidget(close_btn)

        return layout

    def _create_global_stats(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(16)

        total_stats = self.tokens_manager.get_total_stats()

        total_input = total_stats.get("total_input_tokens", 0)
        total_output = total_stats.get("total_output_tokens", 0)
        unknown_input = total_stats.get("unknown_input_count", 0)
        unknown_output = total_stats.get("unknown_output_count", 0)

        input_display = f"{total_input}"
        if unknown_input > 0:
            input_display += f" (+{unknown_input}未知)"

        output_display = f"{total_output}"
        if unknown_output > 0:
            output_display += f" (+{unknown_output}未知)"

        stat_items = [
            ("总调用次数", total_stats.get("record_count", 0)),
            ("总输入Token", input_display),
            ("总输入命中缓存Token", total_stats.get("total_cached_tokens", 0)),
            ("总输出Token", output_display),
        ]

        for label, value in stat_items:
            card = GlobalStatCard(label, value, self)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(card)

        return layout

    def _create_model_detail(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        is_dark = isDarkTheme()
        text_color = ThemeManager.get_color(ThemeManager.Colors.TEXT_PRIMARY, is_dark)
        sub_text_color = ThemeManager.get_color(
            ThemeManager.Colors.TEXT_SECONDARY, is_dark
        )
        primary_color = ThemeManager.get_color(ThemeManager.Colors.PRIMARY, is_dark)
        bg_color = ThemeManager.get_color(ThemeManager.Colors.BG_SECONDARY, is_dark)
        border_color = ThemeManager.get_color(
            ThemeManager.Colors.BORDER_SECONDARY, is_dark
        )
        hover_bg = ThemeManager.get_color(ThemeManager.Colors.LIST_ITEM_HOVER, is_dark)
        selected_bg = ThemeManager.get_color(
            ThemeManager.Colors.LIST_ITEM_SELECTED, is_dark
        )

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title = SubtitleLabel("多模型明细", self)
        title.setStyleSheet(f"""
            color: {text_color};
            font-size: 16px;
            font-weight: 600;
        """)

        label = CaptionLabel("模型选择：", self)
        label.setStyleSheet(f"color: {sub_text_color}; font-size: 13px;")

        self.model_combo = QComboBox(self)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px 16px;
                min-width: 200px;
                font-size: 14px;
                color: {text_color};
                selection-background-color: {primary_color};
                selection-color: white;
            }}
            QComboBox:hover {{
                border: 1px solid {primary_color};
                background-color: {bg_color};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 12px;
            }}
            QComboBox::down-arrow {{
                width: 16px;
                height: 16px;
                color: {text_color};
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 0;
                margin-top: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 10px 16px;
                margin: 2px 8px;
                border-radius: 6px;
                color: {text_color};
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {hover_bg};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {selected_bg};
                color: white;
            }}
        """)
        self._populate_model_combo()
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

        # 导出按钮
        export_btn = DropDownPushButton(FIF.SHARE, "导出", self)
        export_btn.setFixedSize(100, 36)
        from qfluentwidgets import RoundMenu

        menu = RoundMenu(parent=self)
        csv_action = QAction("导出为CSV", export_btn)
        csv_action.triggered.connect(self._export_csv)
        menu.addAction(csv_action)
        excel_action = QAction("导出为Excel", export_btn)
        excel_action.triggered.connect(self._export_excel)
        menu.addAction(excel_action)
        export_btn.setMenu(menu)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(label)
        header_layout.addWidget(self.model_combo)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        self.model_table = ModelDetailTableWidget(self)
        self.model_table.setMinimumHeight(300)
        self._update_model_table()

        layout.addWidget(self.model_table)

        return layout

    def _populate_model_combo(self):
        self.model_combo.clear()
        self.model_combo.addItem("全部模型")

        model_stats = self.tokens_manager.get_model_stats()
        for model_name in sorted(model_stats.keys()):
            self.model_combo.addItem(model_name)

    def _on_model_changed(self, model_name: str):
        self.current_model = model_name
        self._update_model_table()
        self.usage_analysis.update_single_model_view(model_name)

    def _update_model_table(self):
        all_records = self.tokens_manager.get_all_records()

        if self.current_model == "全部模型":
            filtered_records = all_records
        else:
            filtered_records = [
                r for r in all_records if r.get("model_name", "") == self.current_model
            ]

        self.model_table.update_data(filtered_records)

    def _refresh_data(self):
        self._populate_model_combo()
        self._update_model_table()

    def _export_csv(self):
        """导出为CSV文件"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出CSV文件",
            "token_stats.csv",
            "CSV Files (*.csv);;All Files (*)",
            options=options,
        )

        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "请求日期",
                        "小说生成步骤",
                        "模型名称",
                        "输入Token",
                        "输入命中缓存Token",
                        "输出Token",
                    ]
                )

                all_records = self.tokens_manager.get_all_records()

                if self.current_model != "全部模型":
                    filtered_records = [
                        r
                        for r in all_records
                        if r.get("model_name", "") == self.current_model
                    ]
                else:
                    filtered_records = all_records

                for record in filtered_records:
                    timestamp_str = record.get("timestamp", "")
                    if timestamp_str:
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(timestamp_str)
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            formatted_time = timestamp_str
                    else:
                        formatted_time = ""

                    input_tokens = record.get("input_tokens", 0)
                    output_tokens = record.get("output_tokens", 0)
                    input_estimated = record.get("input_estimated", False)
                    output_estimated = record.get("output_estimated", False)

                    if input_tokens == -1:
                        input_display = "未知"
                    elif input_estimated:
                        input_display = f"{input_tokens}(估算)"
                    else:
                        input_display = str(input_tokens)

                    if output_tokens == -1:
                        output_display = "未知"
                    elif output_estimated:
                        output_display = f"{output_tokens}(估算)"
                    else:
                        output_display = str(output_tokens)

                    writer.writerow(
                        [
                            formatted_time,
                            record.get("step_name", ""),
                            record.get("model_name", ""),
                            input_display,
                            record.get("cached_tokens", 0),
                            output_display,
                        ]
                    )

    def _export_excel(self):
        """导出为Excel文件"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出Excel文件",
            "token_stats.xlsx",
            "Excel Files (*.xlsx);;All Files (*)",
            options=options,
        )

        if file_path:
            try:
                import pandas as pd

                all_records = self.tokens_manager.get_all_records()

                if self.current_model != "全部模型":
                    filtered_records = [
                        r
                        for r in all_records
                        if r.get("model_name", "") == self.current_model
                    ]
                else:
                    filtered_records = all_records

                data = []
                for record in filtered_records:
                    timestamp_str = record.get("timestamp", "")
                    if timestamp_str:
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(timestamp_str)
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            formatted_time = timestamp_str
                    else:
                        formatted_time = ""

                    input_tokens = record.get("input_tokens", 0)
                    output_tokens = record.get("output_tokens", 0)
                    input_estimated = record.get("input_estimated", False)
                    output_estimated = record.get("output_estimated", False)

                    if input_tokens == -1:
                        input_display = "未知"
                    elif input_estimated:
                        input_display = f"{input_tokens}(估算)"
                    else:
                        input_display = str(input_tokens)

                    if output_tokens == -1:
                        output_display = "未知"
                    elif output_estimated:
                        output_display = f"{output_tokens}(估算)"
                    else:
                        output_display = str(output_tokens)

                    data.append(
                        {
                            "请求日期": formatted_time,
                            "小说生成步骤": record.get("step_name", ""),
                            "模型名称": record.get("model_name", ""),
                            "输入Token": input_display,
                            "输入命中缓存Token": record.get("cached_tokens", 0),
                            "输出Token": output_display,
                        }
                    )

                df = pd.DataFrame(data)
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Token统计")
            except ImportError:
                # 如果没有pandas，降级为CSV
                self._export_csv()


__all__ = [
    "NovelTokenStatsDialog",
]
