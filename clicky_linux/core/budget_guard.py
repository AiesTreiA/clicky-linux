import os
import sys
import json
import subprocess
from typing import Dict, Any

# Precios oficiales de referencia (USD por 1M tokens) para Claude 3.5 Sonnet
PRICE_INPUT_1M = 3.00   # $3 por millón de tokens de entrada
PRICE_OUTPUT_1M = 15.00 # $15 por millón de tokens de salida

# Umbral máximo permitido por ejecución sin confirmación explícita (en USD)
MAX_COST_THRESHOLD_USD = 0.05  # $0.05 USD por tarea

class BudgetGuard:
    """Protects Anthropic API budget by requiring cost estimation and confirmation

    before running expensive tasks on Claude 3.5 Sonnet via OpenClaw.
    """

    @staticmethod
    def estimate_cost(est_input_tokens: int, est_output_tokens: int) -> float:
        cost_input = (est_input_tokens / 1_000_000.0) * PRICE_INPUT_1M
        cost_output = (est_output_tokens / 1_000_000.0) * PRICE_OUTPUT_1M
        return round(cost_input + cost_output, 5)

    @classmethod
    def run_guarded_sonnet(cls, prompt: str, est_input_tokens: int = 15000, est_output_tokens: int = 2000, force: bool = False):
        cost = cls.estimate_cost(est_input_tokens, est_output_tokens)
        print(f"\n🛡️ [BudgetGuard] Estimación de costo para Sonnet:")
        print(f"   • Tokens estimados: ~{est_input_tokens} entrada | ~{est_output_tokens} salida")
        print(f"   • Costo proyectado: ${cost:.4f} USD (Límite automático: ${MAX_COST_THRESHOLD_USD} USD)")

        if cost > MAX_COST_THRESHOLD_USD and not force:
            print(f"⚠️ Alerta: El costo supera el umbral seguro de ${MAX_COST_THRESHOLD_USD} USD.")
            print(f"   Para autorizar, ejecuta con flag --force o usa el fallback económico (DeepSeek/Gemini Flash).")
            return None

        print(f"✅ Dentro del presupuesto seguro. Ejecutando agente con Claude 3.5 Sonnet...")
        cmd = [
            "/home/astro/.openclaw/bin/openclaw",
            "agent",
            "--model", "anthropic/claude-3-5-sonnet",
            "--message", prompt
        ]
        return subprocess.run(cmd)

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Evaluar plan de Clicky Linux"
    BudgetGuard.run_guarded_sonnet(prompt)
