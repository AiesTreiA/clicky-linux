import json
import os
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional


class VoiceSynthesizer:
    """Multi-provider neural Text-To-Speech (TTS) engine for Clicky Linux.

    Cascades automatically through:
    1. ElevenLabs (`eleven_flash_v2_5` - ~75ms ultra-low latency neural voice in Spanish)
    2. Fal.ai (`fal-ai/kokoro` or `fal-ai/f5-tts` high-speed TTS)
    3. BytePlus / Volcano Engine (`ARK_API_KEY` / `BYTEPLUS_API_KEY` OpenAI-compatible or Volcano TTS)
    4. OpenClaw TTS (`openclaw infer tts convert`)
    5. Native Linux fallback (`spd-say`)
    """

    # Default ElevenLabs voice: Laura (Enthusiast, Quirky, natural Spanish pronunciation)
    DEFAULT_ELEVEN_VOICE_ID = "FGY2WhTYpPnrIDTdsKH5"
    DEFAULT_ELEVEN_MODEL = "eleven_flash_v2_5"

    def __init__(self, preferred_provider: str = "auto", voice_id: Optional[str] = None):
        self._load_env_keys()
        self.preferred_provider = preferred_provider.lower()
        self.eleven_key = os.environ.get("ELEVENLABS_API_KEY")
        self.fal_key = os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")
        self.byteplus_key = os.environ.get("BYTEPLUS_API_KEY") or os.environ.get("ARK_API_KEY")
        self.voice_id = voice_id or os.environ.get("CLICKY_VOICE_ID") or self.DEFAULT_ELEVEN_VOICE_ID

    @staticmethod
    def _load_env_keys():
        """Loads API keys from ~/.env if not already exported in the shell."""
        env_paths = [
            Path.home() / ".env",
            Path.cwd() / ".env",
        ]
        for p in env_paths:
            if p.exists():
                try:
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
                except Exception:
                    pass

    def speak(self, text: str, non_blocking: bool = True):
        """Synthesizes and plays the given speech text."""
        if not text:
            return

        if non_blocking:
            threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()
        else:
            self._speak_sync(text)

    def _speak_sync(self, text: str):
        providers = (
            [self.preferred_provider]
            if self.preferred_provider != "auto"
            else ["elevenlabs", "fal", "byteplus", "openclaw", "local"]
        )

        for prov in providers:
            try:
                if prov == "elevenlabs" and self.eleven_key:
                    if self._speak_elevenlabs(text):
                        return
                elif prov == "fal" and self.fal_key:
                    if self._speak_fal(text):
                        return
                elif prov == "byteplus" and self.byteplus_key:
                    if self._speak_byteplus(text):
                        return
                elif prov == "openclaw":
                    if self._speak_openclaw(text):
                        return
                elif prov == "local":
                    if self._speak_local(text):
                        return
            except Exception:
                continue

        # Ultimate fallback
        self._speak_local(text)

    def _play_audio_file(self, audio_path: str) -> bool:
        """Plays an MP3/WAV file using native PipeWire/FFmpeg/PulseAudio players."""
        try:
            if os.path.exists("/usr/bin/ffplay"):
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20
                )
                return True
            if os.path.exists("/usr/bin/pw-play"):
                subprocess.run(
                    ["pw-play", audio_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20
                )
                return True
            if os.path.exists("/usr/bin/paplay"):
                subprocess.run(
                    ["paplay", audio_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20
                )
                return True
        finally:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                pass
        return False

    def _speak_elevenlabs(self, text: str) -> bool:
        """Synthesizes speech using ElevenLabs Flash v2.5 (ultra-low latency)."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format=mp3_44100_128"
        payload = {
            "text": text,
            "model_id": self.DEFAULT_ELEVEN_MODEL,
            "language_code": "es",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.80,
                "style": 0.15,
                "use_speaker_boost": True
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": self.eleven_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
        )
        out_mp3 = os.path.join(tempfile.gettempdir(), f"clicky_eleven_{int(time.time()*1000)}.mp3")
        with urllib.request.urlopen(req, timeout=10) as resp:
            audio_bytes = resp.read()
            if len(audio_bytes) > 500:
                with open(out_mp3, "wb") as f:
                    f.write(audio_bytes)
                return self._play_audio_file(out_mp3)
        return False

    def _speak_fal(self, text: str) -> bool:
        """Synthesizes speech using Fal.ai Kokoro Multilingual TTS endpoint."""
        url = "https://fal.run/fal-ai/kokoro/spanish"
        payload = {
            "prompt": text,
            "voice": "ef_dora",
            "speed": 1.05
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Key {self.fal_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            audio_url = data.get("audio", {}).get("url")
            if audio_url:
                out_wav = os.path.join(tempfile.gettempdir(), f"clicky_fal_{int(time.time()*1000)}.wav")
                urllib.request.urlretrieve(audio_url, out_wav)
                return self._play_audio_file(out_wav)
        return False

    def _speak_byteplus(self, text: str) -> bool:
        """Synthesizes speech via BytePlus Audio / ModelArk TTS API."""
        base_url = os.environ.get("BYTEPLUS_TTS_URL", "https://ark.ap-southeast.bytepluses.com/api/v3/audio/speech")
        model = os.environ.get("BYTEPLUS_TTS_MODEL", "tts-1")
        payload = {
            "model": model,
            "input": text,
            "voice": os.environ.get("BYTEPLUS_TTS_VOICE", "alloy"),
            "response_format": "mp3"
        }
        req = urllib.request.Request(
            base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.byteplus_key}",
                "Content-Type": "application/json"
            }
        )
        out_mp3 = os.path.join(tempfile.gettempdir(), f"clicky_byteplus_{int(time.time()*1000)}.mp3")
        with urllib.request.urlopen(req, timeout=10) as resp:
            audio_bytes = resp.read()
            if len(audio_bytes) > 500:
                with open(out_mp3, "wb") as f:
                    f.write(audio_bytes)
                return self._play_audio_file(out_mp3)
        return False

    def _speak_openclaw(self, text: str) -> bool:
        """Synthesizes speech via OpenClaw TTS convert CLI."""
        openclaw_bin = "/home/astro/.openclaw/bin/openclaw"
        if not os.path.exists(openclaw_bin):
            return False
        out_mp3 = os.path.join(tempfile.gettempdir(), f"clicky_oc_{int(time.time()*1000)}.mp3")
        cmd = [openclaw_bin, "infer", "tts", "convert", "--text", text, "--output", out_mp3]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
        if res.returncode == 0 and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 500:
            return self._play_audio_file(out_mp3)
        return False

    def _speak_local(self, text: str) -> bool:
        """Zero-token local Linux speech-dispatcher fallback."""
        if os.path.exists("/usr/bin/spd-say"):
            subprocess.run(
                ["spd-say", "-r", "10", "-t", "female2", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        return False
