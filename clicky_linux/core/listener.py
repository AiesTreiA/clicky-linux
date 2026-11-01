import os
import subprocess
import tempfile
import time
from typing import Optional

class AudioListener:
    """Zero-setup Linux audio recorder and transcriber."""

    def __init__(self):
        self.current_proc = None
        self.temp_wav = None

    def start_recording(self) -> str:
        """Starts recording from the default Linux microphone via arecord (ALSA/PipeWire)."""
        self.temp_wav = os.path.join(tempfile.gettempdir(), f"clicky_voice_{int(time.time()*1000)}.wav")
        # Record 16-bit, 16kHz mono audio (ideal format for Whisper / STT)
        cmd = [
            "arecord",
            "-D", "default",
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "1",
            "-t", "wav",
            "-q",
            self.temp_wav
        ]
        self.current_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.temp_wav

    def stop_recording(self) -> Optional[str]:
        """Stops the audio recording process and returns the path to the recorded WAV file."""
        if self.current_proc:
            try:
                self.current_proc.terminate()
                self.current_proc.wait(timeout=2)
            except Exception:
                self.current_proc.kill()
            self.current_proc = None

        if self.temp_wav and os.path.exists(self.temp_wav) and os.path.getsize(self.temp_wav) > 1000:
            return self.temp_wav
        return None

    def transcribe(self, wav_path: str) -> str:
        """Transcribes the voice query using OpenClaw infer audio or local Whisper."""
        if not wav_path or not os.path.exists(wav_path):
            return ""

        # Option A: OpenClaw infer audio
        cmd = ["openclaw", "infer", "audio", "--file", wav_path]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if res.returncode == 0 and res.stdout:
                return res.stdout.decode("utf-8").strip()
        except Exception:
            pass

        return ""
