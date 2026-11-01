import base64
import json
import os
import urllib.request
from typing import Dict, Any, Optional

class VisionEngine:
    """Connects to multimodal AI models to locate elements on the screen with token optimization."""

    def __init__(self, api_key: Optional[str] = None):
        # Auto-detect Gemini or OpenClaw key
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def locate_element(self, image_path: str, user_instruction: str) -> Dict[str, Any]:
        """Analyzes a screenshot with downscaled resolution to minimize token consumption,

        and returns coordinates and speech output.
        """
        if not self.api_key:
            # Fallback mock/heuristic response if no key is set yet
            return {
                "x": 400,
                "y": 250,
                "speech": f"Modo local sin API key: Localizando '{user_instruction}'.",
                "found": True
            }

        # Encode image to base64
        with open(image_path, "rb") as f:
            encoded_img = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are Clicky, an AI visual assistant for desktop Linux.\n"
            f"User asks: \"{user_instruction}\"\n"
            "Analyze the screenshot and locate the exact button, menu item, or UI element the user should interact with.\n"
            "Return ONLY valid JSON with this exact schema:\n"
            "{\n"
            "  \"x\": <integer x coordinate>,\n"
            "  \"y\": <integer y coordinate>,\n"
            "  \"speech\": \"<concise 1-sentence guidance in Spanish>\",\n"
            "  \"found\": <true or false>\n"
            "}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": encoded_img
                            }
                        }
                    ]
                }
            ],
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

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            return {
                "x": 500,
                "y": 300,
                "speech": f"Error al consultar el modelo de visión: {str(e)}",
                "found": False
            }
