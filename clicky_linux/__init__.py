"""Clicky Linux - An open-source AI desktop buddy for Linux."""
import os

# En sesiones Wayland (KDE/GNOME), el protocolo nativo impide posicionar ventanas
# libremente en coordenadas globales (x, y) o leer QCursor.pos() fuera de foco.
# Al usar el backend XCB (XWayland) para Qt, KWin/Mutter permiten posicionamiento
# absoluto exacto en configuraciones multi-monitor y lectura real de QCursor.pos().
if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" and "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

__version__ = "0.5.1"
