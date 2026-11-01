import argparse
import sys
import os
from PyQt6.QtWidgets import QApplication
from clicky_linux.core.capture import ScreenCapturer
from clicky_linux.vision.router import VisionRouter
from clicky_linux.ui.overlay import ClickyOverlay

def main():
    parser = argparse.ArgumentParser(description="Clicky Linux: Ask AI to find and point to any UI element")
    parser.add_argument("query", nargs="?", default="dónde está la barra de búsqueda o el botón principal", help="What to look for")
    parser.add_argument("--duration", type=int, default=5000, help="Pointer display duration in ms")
    args = parser.parse_args()

    print(f"👁️ Clicky capturando pantalla...")
    capturer = ScreenCapturer()
    screen_path = capturer.capture_fullscreen()
    print(f"📸 Captura completada: {screen_path}")

    print(f"🤖 Analizando con VisionRouter optimizado: '{args.query}'...")
    router = VisionRouter()
    result = router.locate(screen_path, args.query)
    
    print("\n=== Resultado Clicky ===")
    print(f"Coordenadas: ({result.get('x')}, {result.get('y')})")
    print(f"Voz/Mensaje: {result.get('speech')}")
    print("========================\n")

    app = QApplication(sys.argv)
    overlay = ClickyOverlay()
    overlay.show_pointer(
        result.get("x", 500),
        result.get("y", 300),
        label=result.get("speech", ""),
        duration_ms=args.duration
    )
    overlay.hide_timer.timeout.connect(app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
