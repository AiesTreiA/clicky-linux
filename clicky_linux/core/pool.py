import time
import random
from typing import Dict, Any, Optional

class TokenPoolManager:
    """Simulates and manages community token pooling and BYOK failover."""

    def __init__(self, byok_key: Optional[str] = None, allow_pool: bool = True):
        self.byok_key = byok_key
        self.allow_pool = allow_pool
        # Simulated community relay health
        self.pool_nodes = [
            {"id": "node-us-east-1", "model": "gemini-flash", "quota_pct": 82, "status": "online"},
            {"id": "node-eu-central-1", "model": "deepseek-flash", "quota_pct": 64, "status": "online"},
            {"id": "node-local-ollama", "model": "qwen3.5:4b", "quota_pct": 100, "status": "online"}
        ]

    def select_active_node(self) -> Dict[str, Any]:
        """Returns the optimal node based on available community credits or personal key."""
        if self.byok_key:
            return {
                "type": "byok",
                "provider": "direct",
                "description": "Usando tu propia API Key personal"
            }
        
        if self.allow_pool:
            online_nodes = [n for n in self.pool_nodes if n["status"] == "online"]
            if online_nodes:
                selected = random.choice(online_nodes)
                return {
                    "type": "community_pool",
                    "node_id": selected["id"],
                    "model": selected["model"],
                    "description": f"Usando pool comunitario ({selected['id']} - {selected['model']})"
                }

        return {
            "type": "offline_mock",
            "provider": "local",
            "description": "Sin cuota comunitaria ni API Key: modo offline"
        }
