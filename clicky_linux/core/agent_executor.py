import os
import subprocess
import time
from typing import Tuple, Optional


class ActionExecutor:
    """Executes optional physical mouse clicks or cursor movements on Linux (Wayland/X11)
    with explicit user approval (Hands-Free Agent Mode).
    """

    def __init__(self, require_confirmation: bool = True):
        self.require_confirmation = require_confirmation

    def request_user_approval(self, action_desc: str, x: int, y: int) -> bool:
        """Displays a native desktop confirmation dialog (kdialog / zenity / terminal)
        before executing any automated click.
        """
        if not self.require_confirmation:
            return True

        prompt_msg = f"Clicky Agent quiere hacer clic en ({x}, {y}):\n\"{action_desc}\"\n\n¿Autorizar acción?"

        # 1. KDE Native Dialog
        if os.path.exists("/usr/bin/kdialog"):
            res = subprocess.run(
                ["kdialog", "--title", "Clicky Agent - Confirmación", "--yesno", prompt_msg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return res.returncode == 0

        # 2. GNOME / GTK Zenity Dialog
        if os.path.exists("/usr/bin/zenity"):
            res = subprocess.run(
                ["zenity", "--question", "--title=Clicky Agent", f"--text={prompt_msg}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return res.returncode == 0

        # 3. Terminal Fallback
        ans = input(f"\n[Clicky Agent] {prompt_msg} [s/N]: ").strip().lower()
        return ans in ("s", "si", "sí", "y", "yes")

    def click_at(self, x: int, y: int, action_desc: str = "Hacer clic aquí") -> bool:
        """Moves cursor and clicks at (x, y) after approval."""
        if not self.request_user_approval(action_desc, x, y):
            print("🛑 Acción cancelada por el usuario.")
            return False

        # 1. ydotool (Wayland & X11 universal via uinput)
        if os.path.exists("/usr/bin/ydotool"):
            subprocess.run(["ydotool", "mousemove", "--absolute", "-x", str(x), "-y", str(y)], check=False)
            time.sleep(0.1)
            subprocess.run(["ydotool", "click", "0xC0"], check=False)
            return True

        # 2. xdotool (X11 / XWayland)
        if os.path.exists("/usr/bin/xdotool"):
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=False)
            return True

        # 3. PyQt6 cursor move fallback (moves cursor visually to target)
        try:
            from PyQt6.QtGui import QCursor
            QCursor.setPos(x, y)
            print(f"🖱️ Cursor movido a ({x}, {y}). (Instala 'ydotool' para clic físico automático en Wayland).")
            return True
        except Exception as e:
            print(f"⚠️ No se pudo mover el cursor automáticamente: {e}")
            return False
