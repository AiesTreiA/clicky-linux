import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/clicky-linux/config.json")

DEFAULT_CONFIG = {
    "version": "1.0",
    "provider": "auto",  # auto, openclaw, gemini, ollama, custom_api
    "models": {
        "vision": "gemini-2.5-flash",
        "chat": "deepseek-flash",
        "agent": "gpt-5.6-terra"
    },
    "tokens": {
        "byok_enabled": True,
        "community_pool_enabled": True,
        "max_resolution_px": 1280
    },
    "api_keys": {
        "gemini": "",
        "anthropic": "",
        "openai": "",
        "deepseek": ""
    },
    "audio": {
        "tts_enabled": True,
        "stt_engine": "local"  # local (arecord+whisper) or openclaw
    }
}

class ConfigManager:
    """Manages Clicky Linux configuration, BYOK credentials, and token pool toggles."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config_dir = self.config_path.parent
        self.config_data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            self._save_default()
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save_default(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2)

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        val = self.config_data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any):
        keys = key_path.split(".")
        d = self.config_data
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self.save()
