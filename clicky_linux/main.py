import argparse
import sys
import os
from PyQt6.QtWidgets import QApplication
from clicky_linux.core.capture import ScreenCapturer
from clicky_linux.vision.router import VisionRouter
from clicky_linux.ui.overlay import ClickyOverlay
from clicky_linux.core.voice import VoiceSynthesizer
from clicky_linux.core.config import ConfigManager
from clicky_linux.core.pool import TokenPoolManager
from clicky_linux.core.agent_executor import ActionExecutor


def run_config_cli(args):
    cfg = ConfigManager()
    if args.set_key:
        k, v = args.set_key.split("=", 1)
        cfg.set(k.strip(), v.strip())
        print(f"✅ Configuración actualizada: {k.strip()} = {v.strip()}")
    else:
        import json
        print("🔧 Configuración actual de Clicky Linux (~/.config/clicky-linux/config.json):")
        print(json.dumps(cfg.config_data, indent=2, ensure_ascii=False))


def run_pool_cli():
    cfg = ConfigManager()
    pool = TokenPoolManager(
        byok_key=os.environ.get("GEMINI_API_KEY") or cfg.get("api_keys.gemini"),
        allow_pool=cfg.get("tokens.community_pool_enabled", True)
    )
    active = pool.select_active_node()
    print("🌐 Estado del Pool Comunitario de Tokens & BYOK:")
    print(f"   • Modo activo: {active['type']}")
    print(f"   • Detalle: {active['description']}")
    print("\nNodos comunitarios registrados:")
    for n in pool.pool_nodes:
        print(f"   - [{n['status'].upper()}] {n['id']} | Modelo: {n['model']} | Cuota disponible: {n['quota_pct']}%")


def main():
    parser = argparse.ArgumentParser(
        prog="clicky",
        description="Clicky Linux: Tu asistente visual de IA que apunta en tu pantalla (Wayland & X11)"
    )
    parser.add_argument("query", nargs="?", default=None, help="Qué elemento buscar en la pantalla (ej. 'dónde está el botón de guardar')")
    parser.add_argument("--duration", type=int, default=5000, help="Duración del puntero en milisegundos (default: 5000)")
    parser.add_argument("--mute", action="store_true", help="Silenciar la síntesis de voz (TTS)")
    parser.add_argument("--tts-provider", type=str, default="auto", choices=["auto", "elevenlabs", "fal", "byteplus", "openclaw", "local"], help="Proveedor de voz TTS (default: auto -> prioriza ElevenLabs Flash v2.5)")
    parser.add_argument("--voice-id", type=str, default=None, help="ID de voz personalizado para ElevenLabs")
    parser.add_argument("--auto-click", action="store_true", help="Modo Agente Hands-Free: solicita permiso para hacer clic físico en las coordenadas")
    parser.add_argument("--config", action="store_true", help="Mostrar la configuración actual")
    parser.add_argument("--set", dest="set_key", metavar="KEY=VAL", help="Modificar un valor de configuración (ej. tokens.max_resolution_px=1280)")
    parser.add_argument("--pool-status", action="store_true", help="Ver estado del Pool Comunitario de Tokens y BYOK")
    args = parser.parse_args()

    if args.config or args.set_key:
        run_config_cli(args)
        return

    if args.pool_status:
        run_pool_cli()
        return

    query = args.query or "dónde está la barra de búsqueda o el botón principal"

    print("👁️ Clicky capturando monitor activo...")
    capturer = ScreenCapturer()
    screen_path, offset_x, offset_y = capturer.capture_active_monitor()
    print(f"📸 Captura completada: {screen_path} (Monitor offset: x={offset_x}, y={offset_y})")

    print(f"🤖 Analizando con VisionRouter optimizado: '{query}'...")
    router = VisionRouter()
    result = router.locate(screen_path, query)

    local_x = result.get("x", 500)
    local_y = result.get("y", 300)
    target_x = local_x + offset_x
    target_y = local_y + offset_y
    speech_msg = result.get("speech", "")

    print("\n=== Resultado Clicky ===")
    print(f"Proveedor   : {result.get('provider', 'auto')}")
    print(f"Coordenadas : ({target_x}, {target_y}) [local: {local_x}, {local_y}]")
    print(f"Voz/Mensaje : {speech_msg}")
    print("========================\n")

    # Speech output (TTS)
    if not args.mute and speech_msg:
        voice = VoiceSynthesizer(preferred_provider=args.tts_provider, voice_id=args.voice_id)
        voice.speak(speech_msg)

    app = QApplication(sys.argv)
    overlay = ClickyOverlay()
    overlay.show_pointer(
        target_x,
        target_y,
        label=speech_msg,
        duration_ms=args.duration
    )

    if args.auto_click:
        executor = ActionExecutor(require_confirmation=True)
        executor.click_at(target_x, target_y, action_desc=speech_msg or query)

    overlay.hide_timer.timeout.connect(app.quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
