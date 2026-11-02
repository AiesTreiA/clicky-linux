import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple
from PIL import Image
import clicky_linux  # ensures QT_QPA_PLATFORM=xcb is configured before Qt import
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCursor


class ScreenCapturer:
    """Handles desktop screen capture with exact multi-monitor coordinate cropping."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "wayland").lower()
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    def get_current_monitor_geometry(self) -> Tuple[int, int, int, int, str]:
        """Detects which monitor the user's mouse cursor is currently in,
        and returns (x, y, width, height, monitor_name).
        """
        app = QApplication.instance() or QApplication(["clicky-probe"])
        mouse_pos = QCursor.pos()
        for screen in app.screens():
            geo = screen.geometry()
            if geo.contains(mouse_pos):
                return geo.x(), geo.y(), geo.width(), geo.height(), screen.name()

        primary = app.primaryScreen()
        geo = primary.geometry()
        return geo.x(), geo.y(), geo.width(), geo.height(), primary.name()

    def capture_active_monitor(self, output_path: Optional[str] = None) -> Tuple[str, int, int]:
        """Captures the full virtual desktop and crops the exact monitor where the mouse cursor is.
        Returns (image_path, monitor_offset_x, monitor_offset_y).
        """
        if not output_path:
            output_path = os.path.join(self.temp_dir, f"clicky_screen_{int(time.time()*1000)}.png")

        mon_x, mon_y, mon_w, mon_h, mon_name = self.get_current_monitor_geometry()

        full_tmp = os.path.join(self.temp_dir, f"clicky_full_{int(time.time()*1000)}.png")
        try:
            self.capture_fullscreen(full_tmp)
            with Image.open(full_tmp) as full_img:
                # If the fullscreen image covers multiple monitors, crop to the active one
                if full_img.width >= mon_x + mon_w and full_img.height >= mon_y + mon_h:
                    cropped = full_img.crop((mon_x, mon_y, mon_x + mon_w, mon_y + mon_h))
                    cropped.save(output_path, "PNG")
                else:
                    full_img.save(output_path, "PNG")
                    mon_x, mon_y = 0, 0
        finally:
            if os.path.exists(full_tmp):
                try:
                    os.remove(full_tmp)
                except Exception:
                    pass

        return output_path, mon_x, mon_y

    def capture_fullscreen(self, output_path: Optional[str] = None) -> str:
        """Captures the entire virtual desktop across all monitors."""
        if not output_path:
            output_path = os.path.join(self.temp_dir, f"clicky_screen_{int(time.time()*1000)}.png")

        # Ensure native Wayland environment for spectacle / grim subprocesses
        sub_env = os.environ.copy()
        if self.session_type == "wayland":
            sub_env["QT_QPA_PLATFORM"] = "wayland"

        if "kde" in self.desktop or os.path.exists("/usr/bin/spectacle"):
            cmd = ["spectacle", "-b", "-n", "-f", "-o", output_path]
            try:
                res = subprocess.run(cmd, env=sub_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        if os.path.exists("/usr/bin/grim"):
            try:
                res = subprocess.run(["grim", output_path], env=sub_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
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
