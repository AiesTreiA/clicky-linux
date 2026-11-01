import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

class ScreenCapturer:
    """Handles desktop screen capture across Wayland (KDE/GNOME/wlroots) and X11."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "wayland").lower()
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    def capture_fullscreen(self, output_path: Optional[str] = None) -> str:
        """Captures the entire screen and saves it to a PNG file."""
        if not output_path:
            output_path = os.path.join(self.temp_dir, f"clicky_screen_{int(time.time()*1000)}.png")

        # 1. Wayland + KDE: spectacle command line
        if "kde" in self.desktop or os.path.exists("/usr/bin/spectacle"):
            cmd = ["spectacle", "-b", "-n", "-o", output_path]
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        # 2. wlroots: grim
        if os.path.exists("/usr/bin/grim"):
            try:
                res = subprocess.run(["grim", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        # 3. X11 / Generic: scrot
        if os.path.exists("/usr/bin/scrot"):
            try:
                res = subprocess.run(["scrot", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        # 4. Fallback to PyQt6 QScreen grab if GUI loop is available
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QGuiApplication
            app = QApplication.instance()
            created_app = False
            if app is None:
                app = QApplication(["clicky-capture"])
                created_app = True
            
            screen = QGuiApplication.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(0)
                pixmap.save(output_path, "PNG")
                if os.path.exists(output_path):
                    return output_path
        except Exception as e:
            raise RuntimeError(f"Failed to capture screen using available methods: {e}")

        raise RuntimeError(f"No functional screenshot tool found for {self.session_type} ({self.desktop})")
