import sys
import threading
import clicky_linux  # ensures QT_QPA_PLATFORM=xcb on Wayland
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QSystemTrayIcon, QMenu
)
from clicky_linux.core.capture import ScreenCapturer
from clicky_linux.vision.router import VisionRouter
from clicky_linux.ui.overlay import ClickyOverlay
from clicky_linux.core.voice import VoiceSynthesizer


def create_clicky_icon() -> QIcon:
    """Creates a clean native vector icon for the system tray and app launcher."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Outer glowing circle
    painter.setBrush(QColor(14, 165, 233))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(6, 6, 52, 52)

    # Pointer triangle inside
    painter.setBrush(QColor(244, 63, 94))
    painter.drawEllipse(22, 22, 20, 20)
    painter.end()
    return QIcon(pixmap)


class WorkerSignals(QObject):
    finished = pyqtSignal(dict, int, int)
    error = pyqtSignal(str)


class ClickyFloatingBar(QWidget):
    """Spotlight-like floating bar and system tray buddy for Clicky Linux."""

    def __init__(self):
        super().__init__()
        self.capturer = ScreenCapturer()
        self.router = VisionRouter()
        self.voice = VoiceSynthesizer()
        self.overlay = ClickyOverlay()
        self.signals = WorkerSignals()
        self.signals.finished.connect(self._on_analysis_done)
        self.signals.error.connect(self._on_analysis_error)

        self._init_ui()
        self._init_tray()

    def _init_ui(self):
        self.setWindowTitle("Clicky Linux")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(15, 23, 42, 240);
                border: 1.5px solid rgba(56, 189, 248, 180);
                border-radius: 14px;
            }
            QLabel#status {
                color: #94a3b8;
                font-size: 11px;
                padding-left: 4px;
            }
            QLineEdit {
                background-color: rgba(30, 41, 59, 220);
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
            QPushButton#askBtn {
                background-color: #0ea5e9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#askBtn:hover {
                background-color: #0284c7;
            }
            QPushButton#closeBtn {
                background-color: transparent;
                color: #64748b;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton#closeBtn:hover {
                color: #f43f5e;
            }
        """)
        self.container.setObjectName("container")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        box = QVBoxLayout(self.container)
        box.setContentsMargins(14, 10, 14, 10)
        box.setSpacing(6)

        top_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("🐧 Pregúntale a Clicky (ej: ¿dónde está el botón de búsqueda?)...")
        self.input_field.returnPressed.connect(self.on_submit)

        self.ask_btn = QPushButton("Señalar 🎯")
        self.ask_btn.setObjectName("askBtn")
        self.ask_btn.clicked.connect(self.on_submit)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setToolTip("Minimizar a la bandeja del sistema (Esc)")
        self.close_btn.clicked.connect(self.hide)

        top_row.addWidget(self.input_field, stretch=1)
        top_row.addWidget(self.ask_btn)
        top_row.addWidget(self.close_btn)

        self.status_label = QLabel("Listo • Presiona Enter para analizar tu pantalla activa | Costo aprox: ~$0.0001 USD/consulta")
        self.status_label.setObjectName("status")

        box.addLayout(top_row)
        box.addWidget(self.status_label)

        # Escape key hides bar
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self.hide)

        self.resize(620, 82)
        self.center_on_active_screen()

    def _init_tray(self):
        self.tray = QSystemTrayIcon(create_clicky_icon(), self)
        self.tray.setToolTip("Clicky Linux - AI Desktop Buddy")

        menu = QMenu()
        show_action = QAction("🎯 Preguntar a Clicky", self)
        show_action.triggered.connect(self.summon_bar)

        quit_action = QAction("Salir de Clicky", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.summon_bar()

    def center_on_active_screen(self):
        mon_x, mon_y, mon_w, mon_h, _ = self.capturer.get_current_monitor_geometry()
        x = mon_x + (mon_w - self.width()) // 2
        y = mon_y + 60  # Top-center Spotlight position
        self.move(x, y)

    def summon_bar(self):
        self.center_on_active_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()
        self.input_field.selectAll()

    def on_submit(self):
        query = self.input_field.text().strip()
        if not query:
            return

        self.status_label.setText(f"👁️ Analizando pantalla para: '{query}'...")
        self.ask_btn.setEnabled(False)
        self.input_field.setEnabled(False)

        # Temporarily hide the bar for 150ms so it doesn't cover any UI elements in the screenshot
        self.hide()
        QTimer.singleShot(180, lambda: self._capture_and_run(query))

    def _capture_and_run(self, query: str):
        try:
            screen_path, offset_x, offset_y = self.capturer.capture_active_monitor()
        except Exception as e:
            self._on_analysis_error(str(e))
            return

        def worker():
            try:
                res = self.router.locate(screen_path, query)
                self.signals.finished.emit(res, offset_x, offset_y)
            except Exception as exc:
                self.signals.error.emit(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_analysis_done(self, result: dict, offset_x: int, offset_y: int):
        self.ask_btn.setEnabled(True)
        self.input_field.setEnabled(True)

        local_x = result.get("x", 500)
        local_y = result.get("y", 300)
        target_x = local_x + offset_x
        target_y = local_y + offset_y
        speech_msg = result.get("speech", "")
        vis_cost = result.get("cost_usd", 0.0)
        tts_cost = round(len(speech_msg) * 0.00005, 6) if speech_msg else 0.0
        total_cost = vis_cost + tts_cost

        self.status_label.setText(
            f"✅ {speech_msg} | Costo: ${total_cost:.5f} USD ({result.get('provider')})"
        )

        if speech_msg:
            self.voice.speak(speech_msg)

        self.overlay.show_pointer(target_x, target_y, label=speech_msg, duration_ms=6000)

    def _on_analysis_error(self, err_msg: str):
        self.ask_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.summon_bar()
        self.status_label.setText(f"⚠️ Error: {err_msg}")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    bar = ClickyFloatingBar()
    bar.summon_bar()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
