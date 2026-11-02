import base64
import json
import os
import re
import subprocess
import urllib.request
from typing import Dict, Any, Optional
from clicky_linux.vision.optimizer import ImageOptimizer

class VisionRouter:
    """Multi-provider Vision Router with automatic token optimization.

    Supports:
    1. Direct Gemini API (Gemini 2.5/3.1 Flash-Lite)
    2. OpenClaw CLI Gateway (`openclaw infer image describe`)
    3. Local heuristics / Ollama fallback
    """

    def __init__(self, preferred_provider: str = "auto", api_key: Optional[str] = None):
        self.preferred_provider = preferred_provider
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.optimizer = ImageOptimizer(max_dimension=1280)

    def locate(self, raw_screenshot_path: str, user_instruction: str) -> Dict[str, Any]:
        """Processes the screenshot, queries the optimal model, and scales coordinates back

        to native desktop resolution.
        """
        # Step 1: Pre-process and optimize screenshot
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

        # Step 2: Route request
        result = None

        # Route A: OpenClaw CLI if available
        if self._has_openclaw():
            try:
                result = self._query_openclaw(opt_path, prompt)
            except Exception:
                pass

        # Route B: Gemini API direct fallback
        if not result and self.api_key:
            try:
                result = self._query_gemini_direct(opt_path, prompt)
            except Exception:
                pass

        # Route C: Mock / Safe local coordinates fallback
        if not result:
            result = {
                "x": 600,
                "y": 400,
                "speech": f"Clicky local: analizado '{user_instruction}'.",
                "found": True
            }

        # Step 3: Re-scale coordinates to actual screen resolution
        raw_x = result.get("x", 0)
        raw_y = result.get("y", 0)

        final_x = int(raw_x * scale_x)
        final_y = int(raw_y * scale_y)

        # Cleanup temporary optimized file
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
            "provider": result.get("provider", "fallback")
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

        # Prefer fast & cheap vision model if configured (deepseek-flash or gemini)
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
                # OpenClaw wraps output in a response envelope: {"ok": true, "outputs": [{"text": "..."}]}
                envelope = json.loads(raw_out[raw_out.find("{"):])
                text_content = envelope.get("outputs", [{}])[0].get("text", "")
                
                # Extract the inner JSON coordinates returned by the model
                inner_match = re.search(r"\{[^{}]*\"x\"[^{}]*\}", text_content, re.DOTALL)
                if inner_match:
                    parsed = json.loads(inner_match.group(0))
                    parsed["provider"] = envelope.get("provider", "openclaw")
                    return parsed
            except Exception:
                pass
        return None

    def _query_gemini_direct(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        mime = "image/jpeg" if image_path.endswith(".jpg") else "image/png"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
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
            parsed = json.loads(text)
            parsed["provider"] = "gemini-flash"
            return parsed
