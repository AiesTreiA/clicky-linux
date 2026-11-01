import os
import subprocess
import threading
from typing import Optional

class VoiceSynthesizer:
    """Zero-cost local Text-To-Speech (TTS) engine for Linux desktop."""

    def __init__(self, voice_speed: int = 150):
        self.voice_speed = voice_speed

    def speak(self, text: str, non_blocking: bool = True):
        """Speaks the given text out loud using native Linux speech dispatch or OpenClaw TTS."""
        if not text:
            return

        if non_blocking:
            threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()
        else:
            self._speak_sync(text)

    def _speak_sync(self, text: str):
        # 1. Native spd-say (standard on Linux desktops)
        if os.path.exists("/usr/bin/spd-say"):
            try:
                subprocess.run(["spd-say", "-r", "10", "-t", "female2", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass

        # 2. OpenClaw infer TTS
        cmd = ["openclaw", "infer", "tts", "--text", text]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass
