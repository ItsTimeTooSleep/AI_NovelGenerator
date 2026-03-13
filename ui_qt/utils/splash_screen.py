# -*- coding: utf-8 -*-
"""
AI Novel Generator - 启动画面模块
==================================

本模块提供应用启动画面的创建和管理功能。
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
    QRadialGradient,
)
from PyQt5.QtWidgets import QApplication, QSplashScreen

SPLASH_WIDTH = 560
SPLASH_HEIGHT = 360
BORDER_RADIUS = 20
ICON_SIZE = 72


def _get_icon_path() -> str:
    """
    获取应用图标路径。

    Returns:
        str: 图标文件的绝对路径，如果找不到则返回空字符串
    """
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    icon_path = os.path.join(base_path, "icon.ico")
    if os.path.exists(icon_path):
        return icon_path
    return ""


def create_splash_pixmap() -> QPixmap:
    """
    创建启动画面的像素图（带圆角，支持高DPI）

    Returns:
        QPixmap: 绘制好的启动画面像素图
    """
    app = QApplication.instance()
    device_pixel_ratio = app.devicePixelRatio() if app else 1.0

    splash_pix = QPixmap(
        int(SPLASH_WIDTH * device_pixel_ratio), int(SPLASH_HEIGHT * device_pixel_ratio)
    )
    splash_pix.setDevicePixelRatio(device_pixel_ratio)
    splash_pix.fill(Qt.transparent)

    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

    rounded_path = QPainterPath()
    rounded_path.addRoundedRect(
        0, 0, SPLASH_WIDTH, SPLASH_HEIGHT, BORDER_RADIUS, BORDER_RADIUS
    )
    painter.setClipPath(rounded_path)

    gradient = QLinearGradient(0, 0, 0, SPLASH_HEIGHT)
    gradient.setColorAt(0, QColor("#ffffff"))
    gradient.setColorAt(0.5, QColor("#f8fafc"))
    gradient.setColorAt(1, QColor("#f1f5f9"))
    painter.fillRect(0, 0, SPLASH_WIDTH, SPLASH_HEIGHT, QBrush(gradient))

    glow_gradient1 = QRadialGradient(200, 140, 200)
    glow_gradient1.setColorAt(0, QColor(139, 92, 246, 25))
    glow_gradient1.setColorAt(0.5, QColor(139, 92, 246, 8))
    glow_gradient1.setColorAt(1, QColor(139, 92, 246, 0))
    painter.fillRect(0, 0, SPLASH_WIDTH, SPLASH_HEIGHT, QBrush(glow_gradient1))

    glow_gradient2 = QRadialGradient(420, 280, 160)
    glow_gradient2.setColorAt(0, QColor(59, 130, 246, 15))
    glow_gradient2.setColorAt(1, QColor(59, 130, 246, 0))
    painter.fillRect(0, 0, SPLASH_WIDTH, SPLASH_HEIGHT, QBrush(glow_gradient2))

    painter.setPen(Qt.NoPen)

    painter.setBrush(QColor(139, 92, 246, 15))
    painter.drawEllipse(450, 40, 100, 100)

    painter.setBrush(QColor(59, 130, 246, 12))
    painter.drawEllipse(40, 260, 70, 70)

    painter.setBrush(QColor(139, 92, 246, 20))
    painter.drawEllipse(480, 280, 45, 45)

    painter.setBrush(QColor(139, 92, 246, 8))
    for i in range(0, SPLASH_WIDTH, 30):
        for j in range(0, SPLASH_HEIGHT, 30):
            if (i + j) % 60 == 0:
                painter.drawEllipse(i, j, 2, 2)

    icon_path = _get_icon_path()
    icon_x = (SPLASH_WIDTH - ICON_SIZE) // 2
    icon_y = 45
    if icon_path:
        icon = QIcon(icon_path)
        icon_pixmap = icon.pixmap(ICON_SIZE, ICON_SIZE)

        icon_glow = QRadialGradient(
            icon_x + ICON_SIZE // 2, icon_y + ICON_SIZE // 2, ICON_SIZE
        )
        icon_glow.setColorAt(0, QColor(139, 92, 246, 30))
        icon_glow.setColorAt(0.5, QColor(139, 92, 246, 10))
        icon_glow.setColorAt(1, QColor(139, 92, 246, 0))
        painter.setBrush(QBrush(icon_glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(icon_x - 15, icon_y - 15, ICON_SIZE + 30, ICON_SIZE + 30)

        painter.drawPixmap(icon_x, icon_y, icon_pixmap)

    painter.setPen(QColor("#1e293b"))
    title_font = QFont()
    title_font.setFamily("Segoe UI")
    title_font.setPointSize(26)
    title_font.setWeight(QFont.Bold)
    title_font.setLetterSpacing(QFont.PercentageSpacing, 105)
    title_font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(title_font)
    painter.drawText(0, 130, SPLASH_WIDTH, 40, Qt.AlignCenter, "AI Novel")
    painter.drawText(0, 165, SPLASH_WIDTH, 40, Qt.AlignCenter, "Generator")

    painter.setPen(QColor("#7c3aed"))
    subtitle_font = QFont()
    subtitle_font.setFamily("Segoe UI")
    subtitle_font.setPointSize(12)
    subtitle_font.setWeight(QFont.Normal)
    subtitle_font.setLetterSpacing(QFont.PercentageSpacing, 108)
    subtitle_font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(subtitle_font)
    painter.drawText(0, 205, SPLASH_WIDTH, 30, Qt.AlignCenter, "Enhanced Edition")

    painter.setPen(QColor("#64748b"))
    tagline_font = QFont()
    tagline_font.setFamily("Segoe UI")
    tagline_font.setPointSize(11)
    tagline_font.setWeight(QFont.Normal)
    tagline_font.setLetterSpacing(QFont.PercentageSpacing, 105)
    tagline_font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(tagline_font)
    painter.drawText(
        0, 275, SPLASH_WIDTH, 35, Qt.AlignCenter, "基于大模型的长篇小说创作工具"
    )

    for i in range(5):
        x = 245 + i * 18
        y = 325

        base_size = 10
        size_variation = 3 if i % 2 == 0 else 0
        size = base_size + size_variation

        colors = [
            QColor("#7c3aed"),
            QColor("#8b5cf6"),
            QColor("#a78bfa"),
            QColor("#8b5cf6"),
            QColor("#7c3aed"),
        ]

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(colors[i]))
        painter.drawEllipse(x, y, size, size)

        glow = QRadialGradient(x + size / 2, y + size / 2, size)
        glow.setColorAt(
            0, QColor(colors[i].red(), colors[i].green(), colors[i].blue(), 60)
        )
        glow.setColorAt(
            1, QColor(colors[i].red(), colors[i].green(), colors[i].blue(), 0)
        )
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(x - 4, y - 4, size + 8, size + 8)

    painter.end()
    return splash_pix


def create_splash_screen() -> QSplashScreen:
    """
    创建启动画面组件（带圆角效果）

    Returns:
        QSplashScreen: 配置好的启动画面组件
    """
    splash_pix = create_splash_pixmap()
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_TranslucentBackground)
    return splash
