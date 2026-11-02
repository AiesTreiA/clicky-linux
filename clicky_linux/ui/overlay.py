import sys
import math
from typing import Optional
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QApplication


class ClickySingleMonitorOverlay(QWidget):
    """Transparent click-through overlay window for a single screen."""

    def __init__(self, target_screen):
        super().__init__()
        self.target_screen = target_screen
        self.setScreen(target_screen)

        # Wayland/X11 transparent, frameless, click-through configuration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.rel_x = 0.0
        self.rel_y = 0.0
        self.label_text = ""
        self.active = False
        self.animation_step = 0

        # Animation timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def display(self, rel_x: float, rel_y: float, label: str):
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.label_text = label
        self.active = True
        self.animation_step = 0

        geo = self.target_screen.geometry()
        self.setGeometry(geo)
        self.show()
        self.raise_()
        self.update()

    def hide_overlay(self):
        self.active = False
        self.update()
        self.hide()

    def _on_tick(self):
        if self.active:
            self.animation_step = (self.animation_step + 1) % 360
            self.update()

    def paintEvent(self, event):
        if not self.active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rad = math.radians(self.animation_step * 4)
        bounce = math.sin(rad) * 6.0
        pulse = 1.0 + 0.15 * math.sin(rad)

        px = float(self.rel_x)
        py = float(self.rel_y)

        # 1. Pulsing target rings around the point
        ring_radius = 24.0 * pulse
        painter.setPen(QPen(QColor(56, 189, 248, 180), 2.5))
        painter.setBrush(QBrush(QColor(56, 189, 248, 40)))
        painter.drawEllipse(QPointF(px, py), ring_radius, ring_radius)

        # Inner pinpoint
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(14, 165, 233, 230)))
        painter.drawEllipse(QPointF(px, py), 6.0, 6.0)

        # 2. Animated Pointer Finger / Arrow Hand
        hand_x = px + 18.0 + bounce * 0.7
        hand_y = py + 18.0 + bounce * 0.7

        arrow_path = QPainterPath()
        arrow_path.moveTo(px + 4, py + 4)
        arrow_path.lineTo(hand_x + 18, hand_y + 6)
        arrow_path.lineTo(hand_x + 8, hand_y + 18)
        arrow_path.closeSubpath()

        painter.setPen(QPen(QColor(255, 255, 255), 2.0))
        painter.setBrush(QBrush(QColor(244, 63, 94, 240)))
        painter.drawPath(arrow_path)

        # 3. Label Badge
        if self.label_text:
            font = QFont("Sans-Serif", 11, QFont.Weight.Bold)
            painter.setFont(font)

            badge_text = f"Clicky: {self.label_text}"
            metrics = painter.fontMetrics()
            text_w = metrics.horizontalAdvance(badge_text) + 24
            text_h = metrics.height() + 12

            badge_x = px - text_w / 2
            badge_y = py - 45 - bounce
            if badge_y < 10:
                badge_y = py + 35 + bounce

            badge_rect = QRectF(badge_x, badge_y, text_w, text_h)

            painter.setPen(QPen(QColor(255, 255, 255), 80), 1.0)
            painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
            painter.drawRoundedRect(badge_rect, 8.0, 8.0)

            painter.setPen(QColor(248, 250, 252))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)


class ClickyOverlay:
    """Multi-monitor manager that routes the pointer to the exact physical monitor under Wayland."""

    def __init__(self):
        self.overlays = []
        for screen in QApplication.screens():
            self.overlays.append(ClickySingleMonitorOverlay(screen))

        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_indicator)

    def show_pointer(self, global_x: int, global_y: int, label: str = "", duration_ms: int = 5000):
        """Finds which screen contains (global_x, global_y) and displays on that screen's overlay."""
        screens = QApplication.screens()
        target_overlay = None
        rel_x = global_x
        rel_y = global_y

        for i, screen in enumerate(screens):
            geo = screen.geometry()
            if geo.contains(global_x, global_y):
                target_overlay = self.overlays[i]
                rel_x = global_x - geo.x()
                rel_y = global_y - geo.y()
                break

        if not target_overlay and self.overlays:
            # Fallback to first screen
            target_overlay = self.overlays[0]
            geo = screens[0].geometry()
            rel_x = global_x - geo.x()
            rel_y = global_y - geo.y()

        if target_overlay:
            # Hide all other screens
            for ov in self.overlays:
                if ov != target_overlay:
                    ov.hide_overlay()

            target_overlay.display(rel_x, rel_y, label)

        if duration_ms > 0:
            self.hide_timer.start(duration_ms)

    def hide_indicator(self):
        for ov in self.overlays:
            ov.hide_overlay()
