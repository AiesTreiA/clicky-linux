import argparse
import sys
from PyQt6.QtWidgets import QApplication
from clicky_linux.ui.overlay import ClickyOverlay

def main():
    parser = argparse.ArgumentParser(description="Test Clicky pointer overlay on Linux")
    parser.add_argument("--x", type=int, default=500, help="Target X coordinate")
    parser.add_argument("--y", type=int, default=300, help="Target Y coordinate")
    parser.add_argument("--label", type=str, default="Haz clic aquí", help="Label text")
    parser.add_argument("--duration", type=int, default=4000, help="Duration in milliseconds")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    overlay = ClickyOverlay()
    overlay.show_pointer(args.x, args.y, args.label, duration_ms=args.duration)

    # Quit when hide_timer triggers
    overlay.hide_timer.timeout.connect(app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
