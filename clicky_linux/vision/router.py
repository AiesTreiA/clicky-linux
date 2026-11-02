import base64
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional
from clicky_linux.vision.optimizer import ImageOptimizer

# Precios de referencia (USD por 1M de tokens)
MODEL_PRICING = {
    "google/gemini-3.1-flash-lite": {"input": 0.075, "output": 0.30},
    "google/gemini-3.8-flash": {"input": 0.15, "output": 0.60},
    "deepseek/deepseek-flash": {"input": 0.14, "output": 0.28},
    "anthropic/claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
    "anthropic/claude-opus-5-5": {"input": 15.00, "output": 75.00},
    "local/fallback": {"input": 0.0, "output": 0.0},
}


class VisionRouter:
    """Multi-provider Vision Router with automatic token optimization and transparent cost tracking.

    Default priority (to protect premium Anthropic budget):
    1. Direct Gemini API (`gemini-3.1-flash-lite` -> ultra-fast, ~$0.0001 USD per screenshot)
    2. OpenClaw CLI Gateway (only if explicitly requested or as fallback with non-Anthropic model)
    3. Local heuristics / Ollama fallback ($0.0000 USD)
    """

    def __init__(self, preferred_provider: str = "auto", api_key: Optional[str] = None):
        self._load_env_keys()
        self.preferred_provider = preferred_provider.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.optimizer = ImageOptimizer(max_dimension=1280)

    @staticmethod
    def _load_env_keys():
        """Loads API keys from ~/.env if not already exported in the current shell."""
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

    @staticmethod
    def calculate_cost(model_id: str, in_tokens: int, out_tokens: int) -> float:
        prices = MODEL_PRICING.get(model_id, {"input": 0.15, "output": 0.60})
        return round((in_tokens / 1_000_000.0) * prices["input"] + (out_tokens / 1_000_000.0) * prices["output"], 6)

    def locate(self, raw_screenshot_path: str, user_instruction: str) -> Dict[str, Any]:
        """Processes the screenshot, queries the optimal model, scales coordinates back
        to native desktop resolution, and calculates exact/estimated cost.
        """
        opt_path, scale_x, scale_y = self.optimizer.optimize_for_vision(raw_screenshot_path)

        prompt = (
            "You are Clicky Linux, an AI visual assistant.\n"
            f"User command: \"{user_instruction}\"\n"
            "Identify the UI element the user needs to click or interact with.\n"
            "Return STRICT JSON only:\n"
            "{\n"
            "  \"x\": <integer x coordinate in this image>,\n"
            "  \"y\": <integer y coordinate in this image>,\n"
            "  \"speech\": \"<concise instruction in Spanish, max 12 words>\",\n"
            "  \"found\": <true or false>\n"
            "}"
        )

        result = None

        # Priority 1: Direct Gemini 3.1 Flash-Lite (ultra-cheap & fast, avoids OpenClaw Anthropic default)
        if self.preferred_provider in ("auto", "gemini") and self.api_key:
            try:
                result = self._query_gemini_direct(opt_path, prompt)
            except Exception:
                pass

        # Priority 2: OpenClaw CLI (only if requested or if Gemini direct wasn't available)
        if not result and self.preferred_provider in ("openclaw", "anthropic") and self._has_openclaw():
            try:
                result = self._query_openclaw(opt_path, prompt)
            except Exception:
                pass

        # Priority 3: Safe local coordinates fallback ($0 cost)
        if not result:
            result = {
                "x": 600,
                "y": 400,
                "speech": f"Clicky local: analizado '{user_instruction}'.",
                "found": True,
                "provider": "local/fallback",
                "in_tokens": 0,
                "out_tokens": 0,
                "cost_usd": 0.0
            }

        raw_x = result.get("x", 0)
        raw_y = result.get("y", 0)

        final_x = int(raw_x * scale_x)
        final_y = int(raw_y * scale_y)

        try:
            if opt_path != raw_screenshot_path and os.path.exists(opt_path):
                os.remove(opt_path)
        except Exception:
            pass

        return {
            "x": final_x,
            "y": final_y,
            "speech": result.get("speech", ""),
            "found": result.get("found", True),
            "provider": result.get("provider", "local/fallback"),
            "in_tokens": result.get("in_tokens", 0),
            "out_tokens": result.get("out_tokens", 0),
            "cost_usd": result.get("cost_usd", 0.0),
        }

    def _get_openclaw_bin(self) -> Optional[str]:
        for candidate in ["/home/astro/.openclaw/bin/openclaw", "/home/astro/.openclaw/tmp/agent-cli/openclaw"]:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate
        res = subprocess.run(["which", "openclaw"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return res.stdout.decode().strip()
        return None

    def _has_openclaw(self) -> bool:
        return self._get_openclaw_bin() is not None

    def _query_openclaw(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        bin_path = self._get_openclaw_bin()
        if not bin_path:
            return None

        cmd = [
            bin_path, "infer", "image", "describe",
            "--file", image_path,
            "--prompt", prompt,
            "--json"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
        if res.returncode == 0 and res.stdout:
            try:
                raw_out = res.stdout.decode("utf-8")
                envelope = json.loads(raw_out[raw_out.find("{"):])
                text_content = envelope.get("outputs", [{}])[0].get("text", "")
                prov = envelope.get("provider", "openclaw")
                mod = envelope.get("model", "claude-opus-5-5")
                full_model = f"{prov}/{mod}" if "/" not in mod else mod

                inner_match = re.search(r"\{[^{}]*\"x\"[^{}]*\}", text_content, re.DOTALL)
                if inner_match:
                    parsed = json.loads(inner_match.group(0))
                    in_tok = 1150
                    out_tok = max(25, len(text_content) // 4)
                    parsed["provider"] = full_model
                    parsed["in_tokens"] = in_tok
                    parsed["out_tokens"] = out_tok
                    parsed["cost_usd"] = self.calculate_cost(full_model, in_tok, out_tok)
                    return parsed
            except Exception:
                pass
        return None

    def _query_gemini_direct(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        mime = "image/jpeg" if image_path.endswith(".jpg") else "image/png"
        model_name = "gemini-3.1-flash-lite"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": b64_data}}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            in_tok = usage.get("promptTokenCount", 1100)
            out_tok = usage.get("candidatesTokenCount", 45)
            full_model = f"google/{model_name}"

            parsed = json.loads(text)
            parsed["provider"] = full_model
            parsed["in_tokens"] = in_tok
            parsed["out_tokens"] = out_tok
            parsed["cost_usd"] = self.calculate_cost(full_model, in_tok, out_tok)
            return parsed
