import math
import clicky_linux  # ensures QT_QPA_PLATFORM=xcb on Wayland
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QApplication


class ClickyOverlay(QWidget):
    """Transparent, click-through overlay window covering the full multi-monitor virtual desktop.
    Draws the iconic HeyClicky blue avatar mascot, speech bubble, waveform, and points at target.
    """

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.target_x = 0
        self.target_y = 0
        self.label_text = ""
        self.active = False
        self.animation_step = 0
        self.has_target = False

        # Animation timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_indicator)

    def show_companion(self, speech_text: str, target_x: int = -1, target_y: int = -1, duration_ms: int = 7000):
        """Displays Clicky as a companion tutor: talks to you and optionally points at coordinates."""
        screens = QApplication.screens()
        if screens:
            min_x = min(s.geometry().x() for s in screens)
            min_y = min(s.geometry().y() for s in screens)
            max_r = max(s.geometry().x() + s.geometry().width() for s in screens)
            max_b = max(s.geometry().y() + s.geometry().height() for s in screens)
            virtual_geo = QRect(min_x, min_y, max_r - min_x, max_b - min_y)
        else:
            virtual_geo = QApplication.primaryScreen().geometry()

        self.label_text = speech_text
        self.active = True
        self.animation_step = 0

        if target_x >= 0 and target_y >= 0:
            self.has_target = True
            self.target_x = target_x - virtual_geo.x()
            self.target_y = target_y - virtual_geo.y()
        else:
            self.has_target = False

        self.setGeometry(virtual_geo)
        self.show()
        self.raise_()
        self.update()

        if duration_ms > 0:
            self.hide_timer.start(duration_ms)

    def show_pointer(self, global_x: int, global_y: int, label: str = "", duration_ms: int = 5000):
        """Backward-compatible pointer method."""
        self.show_companion(label, target_x=global_x, target_y=global_y, duration_ms=duration_ms)

    def hide_indicator(self):
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

        rad = math.radians(self.animation_step * 5)
        bounce = math.sin(rad) * 6.0
        pulse = 1.0 + 0.15 * math.sin(rad)

        # ---------------------------------------------------------
        # Case A: We have a specific UI target to point at
        # ---------------------------------------------------------
        if self.has_target:
            px = float(self.target_x)
            py = float(self.target_y)

            # 1. Pulsing target rings around the point
            ring_radius = 24.0 * pulse
            painter.setPen(QPen(QColor(56, 189, 248, 180), 2.5))
            painter.setBrush(QBrush(QColor(56, 189, 248, 40)))
            painter.drawEllipse(QPointF(px, py), ring_radius, ring_radius)

            # Inner pinpoint
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(14, 165, 233, 230)))
            painter.drawEllipse(QPointF(px, py), 6.0, 6.0)

            # 2. HeyClicky Blue Mascot Arrow
            hand_x = px + 22.0 + bounce * 0.7
            hand_y = py + 22.0 + bounce * 0.7

            arrow_path = QPainterPath()
            arrow_path.moveTo(px + 4, py + 4)
            arrow_path.lineTo(hand_x + 22, hand_y + 6)
            arrow_path.lineTo(hand_x + 10, hand_y + 22)
            arrow_path.closeSubpath()

            painter.setPen(QPen(QColor(255, 255, 255), 2.0))
            painter.setBrush(QBrush(QColor(14, 165, 233, 245)))  # Clicky Electric Blue
            painter.drawPath(arrow_path)

            bubble_anchor_x = px
            bubble_anchor_y = py - 50 - bounce
            if bubble_anchor_y < 50:
                bubble_anchor_y = py + 45 + bounce

        # ---------------------------------------------------------
        # Case B: General advice / no specific target (companion mode)
        # ---------------------------------------------------------
        else:
            # Place buddy at bottom-right or center-right of active workspace
            screens = QApplication.screens()
            active_scr = screens[0].geometry() if screens else QRect(0, 0, 1920, 1080)
            bubble_anchor_x = active_scr.x() + active_scr.width() // 2
            bubble_anchor_y = active_scr.y() + 100 + bounce

        # 3. Speech Bubble with Mascot Badge
        if self.label_text:
            font = QFont("Sans-Serif", 11, QFont.Weight.Medium)
            painter.setFont(font)

            full_text = self.label_text
            metrics = painter.fontMetrics()
            text_w = min(max(metrics.horizontalAdvance(full_text) + 60, 240), 650)

            # Calculate wrapped text rectangle
            bounding_doc = metrics.boundingRect(QRect(0, 0, text_w - 40, 1000), Qt.TextFlag.TextWordWrap, full_text)
            box_h = max(bounding_doc.height() + 32, 54)

            box_x = bubble_anchor_x - text_w / 2
            box_y = bubble_anchor_y - box_h

            bubble_rect = QRectF(box_x, box_y, text_w, box_h)

            # Bubble background with modern dark glassmorphism
            painter.setPen(QPen(QColor(56, 189, 248, 140), 1.5))
            painter.setBrush(QBrush(QColor(15, 23, 42, 245)))
            painter.drawRoundedRect(bubble_rect, 12.0, 12.0)

            # Mascot avatar badge on the left
            mascot_rect = QRectF(box_x + 10, box_y + 10, 24, 24)
            painter.setBrush(QBrush(QColor(14, 165, 233)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(mascot_rect)

            # Cute face inside mascot
            painter.setPen(QPen(QColor(255, 255, 255), 1.5))
            painter.drawPoint(QPointF(box_x + 18, box_y + 20))
            painter.drawPoint(QPointF(box_x + 26, box_y + 20))

            # Speech text inside bubble
            text_rect = QRectF(box_x + 42, box_y + 10, text_w - 52, box_h - 20)
            painter.setPen(QColor(248, 250, 252))
            painter.drawText(text_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignVCenter, full_text)
