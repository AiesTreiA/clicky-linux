"""BudgetGuard: protege tu presupuesto de la API de Anthropic al usar Claude vía OpenClaw.

Uso:
    python3 -m clicky_linux.core.budget_guard "tu tarea"            # estima y pide confirmación
    python3 -m clicky_linux.core.budget_guard -f tarea.md --yes     # sin preguntar si cabe en el tope
    python3 -m clicky_linux.core.budget_guard "tarea" --dry-run     # solo estima
    python3 -m clicky_linux.core.budget_guard --status              # gasto del mes

Notas:
- Los precios son configurables (PRICES) y deben verificarse en anthropic.com/pricing.
- La estimación de entrada se basa en el tamaño real del prompt (~4 caracteres/token);
  la salida se asume como `--max-output` tokens (peor caso razonable).
- Solo protege lo que se lanza por este comando. No intercepta Telegram/TUI/otros usos.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OPENCLAW_BIN = os.environ.get("OPENCLAW_BIN", "/home/astro/.openclaw/bin/openclaw")
DEFAULT_MODEL = "anthropic/claude-sonnet-5-5"

# USD por 1M de tokens (verificar en anthropic.com/pricing)
PRICES = {
    "anthropic/claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
}

LEDGER = Path(os.path.expanduser("~/.config/clicky-linux/spend.json"))
PER_TASK_AUTO_USD = 0.05   # bajo este costo no pregunta si se usa --yes
PER_TASK_MAX_USD = 0.50    # sobre esto se exige --force
MONTHLY_CAP_USD = 5.00     # tope mensual (estimado, no gasto real facturado)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICES.get(model)
    if not p:
        raise ValueError(f"Sin precio configurado para {model}; agrégalo a PRICES.")
    return round(in_tokens / 1e6 * p["input"] + out_tokens / 1e6 * p["output"], 5)


def _load_ledger() -> dict:
    try:
        return json.loads(LEDGER.read_text())
    except Exception:
        return {}


def month_spent() -> float:
    return float(_load_ledger().get(datetime.now().strftime("%Y-%m"), 0.0))


def record_spend(amount: float) -> None:
    data = _load_ledger()
    key = datetime.now().strftime("%Y-%m")
    data[key] = round(float(data.get(key, 0.0)) + amount, 5)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, indent=2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ejecuta Claude vía OpenClaw con control de gasto")
    ap.add_argument("prompt", nargs="?", help="Texto de la tarea")
    ap.add_argument("-f", "--file", help="Leer la tarea desde un archivo")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-output", type=int, default=2000, help="Tokens de salida asumidos")
    ap.add_argument("--yes", action="store_true", help="No preguntar si el costo es bajo")
    ap.add_argument("--force", action="store_true", help="Permitir costo sobre el máximo por tarea/mes")
    ap.add_argument("--dry-run", action="store_true", help="Solo estimar, no ejecutar")
    ap.add_argument("--status", action="store_true", help="Mostrar gasto estimado del mes")
    args = ap.parse_args(argv)

    if args.status:
        print(f"Gasto estimado este mes: ${month_spent():.4f} / ${MONTHLY_CAP_USD:.2f}")
        return 0

    text = Path(args.file).read_text(encoding="utf-8") if args.file else args.prompt
    if not text:
        ap.error("Indica un prompt o -f archivo")

    in_tok = estimate_tokens(text)
    cost = estimate_cost(args.model, in_tok, args.max_output)
    spent = month_spent()

    print("\n[BudgetGuard]")
    print(f"  Modelo: {args.model}")
    print(f"  Tokens: ~{in_tok} entrada + ~{args.max_output} salida (peor caso)")
    print(f"  Costo estimado: ${cost:.4f} USD")
    print(f"  Mes: ${spent:.4f} + ${cost:.4f} de tope ${MONTHLY_CAP_USD:.2f}")

    if args.dry_run:
        return 0

    if cost > PER_TASK_MAX_USD and not args.force:
        print(f"BLOQUEADO: supera ${PER_TASK_MAX_USD} por tarea. Usa --force si es necesario.")
        return 2
    if spent + cost > MONTHLY_CAP_USD and not args.force:
        print(f"BLOQUEADO: superaría el tope mensual de ${MONTHLY_CAP_USD}. Usa --force.")
        return 2
    if not (args.yes and cost <= PER_TASK_AUTO_USD):
        if input("¿Ejecutar? [s/N] ").strip().lower() not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado.")
            return 1

    cmd = [OPENCLAW_BIN, "agent", "--agent", "main", "--model", args.model]
    if args.file:
        cmd += ["--message-file", args.file]
    else:
        cmd += ["--message", text]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        record_spend(cost)  # estimado; el gasto real puede diferir
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
