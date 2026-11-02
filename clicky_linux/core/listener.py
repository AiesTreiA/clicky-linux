import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Optional


class AudioListener:
    """Zero-setup Linux audio recorder and transcriber for Push-to-Talk (Hold Shift to Talk)."""

    def __init__(self):
        self.current_proc = None
        self.temp_wav = None
        self._load_env_keys()

    @staticmethod
    def _load_env_keys():
        for p in [Path.home() / ".env", Path.cwd() / ".env"]:
            if p.exists():
                try:
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
                except Exception:
                    pass

    def start_recording(self) -> str:
        """Starts recording from the default Linux microphone via arecord (PipeWire/ALSA)."""
        self.temp_wav = os.path.join(tempfile.gettempdir(), f"clicky_voice_{int(time.time()*1000)}.wav")
        # 16-bit, 16kHz mono audio (universal voice AI standard)
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
        """Stops the audio recording process and returns the recorded WAV path."""
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
        """Transcribes voice audio to Spanish text using Gemini Flash multimodal audio or OpenClaw."""
        if not wav_path or not os.path.exists(wav_path):
            return ""

        # Priority 1: Gemini 3.1 Flash-Lite Audio Transcription (ultra-accurate, ~$0.00002 USD)
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                with open(wav_path, "rb") as f:
                    b64_audio = base64.b64encode(f.read()).decode("utf-8")

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Transcribe the spoken audio query verbatim. Return ONLY the transcription text in Spanish, with no quotes or preamble."},
                            {"inline_data": {"mime_type": "audio/wav", "data": b64_audio}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.0}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        return text
            except Exception:
                pass

        # Priority 2: OpenClaw infer audio CLI
        openclaw_bin = "/home/astro/.openclaw/bin/openclaw"
        if os.path.exists(openclaw_bin):
            cmd = [openclaw_bin, "infer", "audio", "--file", wav_path]
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
                if res.returncode == 0 and res.stdout:
                    return res.stdout.decode("utf-8").strip()
            except Exception:
                pass

        return ""
