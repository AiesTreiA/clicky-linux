import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCursor


class ScreenCapturer:
    """Handles desktop screen capture with smart active-monitor detection for multi-head Wayland/X11."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "wayland").lower()
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    def get_current_monitor_offset(self) -> Tuple[int, int, str]:
        """Detects which monitor the user's mouse cursor is currently in,

        and returns (offset_x, offset_y, monitor_name).
        """
        app = QApplication.instance() or QApplication(["clicky-probe"])
        mouse_pos = QCursor.pos()
        for screen in app.screens():
            if screen.geometry().contains(mouse_pos):
                geo = screen.geometry()
                return geo.x(), geo.y(), screen.name()

        # Fallback to primary screen
        primary = app.primaryScreen()
        return primary.geometry().x(), primary.geometry().y(), primary.name()

    def capture_active_monitor(self, output_path: Optional[str] = None) -> Tuple[str, int, int]:
        """Captures ONLY the active monitor where the user is currently working.

        Returns (image_path, monitor_offset_x, monitor_offset_y).
        """
        if not output_path:
            output_path = os.path.join(self.temp_dir, f"clicky_screen_{int(time.time()*1000)}.png")

        offset_x, offset_y, screen_name = self.get_current_monitor_offset()

        # KDE Spectacle -m captures the active monitor (1920x1080)
        if "kde" in self.desktop or os.path.exists("/usr/bin/spectacle"):
            cmd = ["spectacle", "-b", "-n", "-m", "-o", output_path]
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path, offset_x, offset_y
            except Exception:
                pass

        # Fallback: capture fullscreen and return offset 0, 0
        return self.capture_fullscreen(output_path), 0, 0

    def capture_fullscreen(self, output_path: Optional[str] = None) -> str:
        """Captures the entire virtual desktop across all monitors."""
        if not output_path:
            output_path = os.path.join(self.temp_dir, f"clicky_screen_{int(time.time()*1000)}.png")

        if "kde" in self.desktop or os.path.exists("/usr/bin/spectacle"):
            cmd = ["spectacle", "-b", "-n", "-f", "-o", output_path]
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        if os.path.exists("/usr/bin/grim"):
            try:
                res = subprocess.run(["grim", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        if os.path.exists("/usr/bin/scrot"):
            try:
                res = subprocess.run(["scrot", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        raise RuntimeError(f"No functional screenshot tool found for {self.session_type}")
