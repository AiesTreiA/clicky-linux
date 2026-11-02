# Contributing to Clicky Linux & Community Token Pool 🐧🤝

¡Gracias por tu interés en contribuir a **Clicky Linux**! Este proyecto nace para darle a la comunidad de Linux un asistente visual de escritorio nativo, ligero y abierto.

---

## 1. Cómo aportar Tokens / Cómputo de IA (Community Token Pool)

Uno de los objetivos principales de **Clicky Linux** es democratizar el acceso a asistentes visuales sin obligar a cada usuario a pagar suscripciones costosas:

### A. Bring Your Own Key (BYOK)
Puedes conectar tus propias claves de bajo costo o capas gratuitas:
- **Google Gemini Flash / Flash-Lite:** Cuenta con una capa gratuita generosa en Google AI Studio.
- **DeepSeek Flash:** Costo ultra-bajo por millón de tokens.
- **OpenClaw Gateway:** Enruta automáticamente entre tus proveedores locales y en la nube.

Configúralo con:
```bash
python3 -m clicky_linux.main --set api_keys.gemini=TU_API_KEY
```

### B. Ejecución 100% Local ($0 / 0 Tokens)
Si tienes GPU o CPU moderna, puedes correr modelos locales vía **Ollama** (`qwen2.5-vl` / `qwen3.5:4b`), **faster-whisper** para voz y **spd-say / Piper** para síntesis de habla.

### C. Donación de Nodos al Pool Comunitario
Si deseas compartir cuota ociosa o levantar un nodo local/remoto para la comunidad o para entrenar/afinar modelos open-source de detección de UI (como *OmniParser* o *UI-TARS* adaptados a escritorios KDE/GNOME/Hyprland):
1. Revisa el estado del pool con:
   ```bash
   python3 -m clicky_linux.main --pool-status
   ```
2. Abre un Issue o Pull Request con la etiqueta `community-node` o `dataset-contribution` para compartir capturas anonimizadas de interfaces Linux (GTK4, Qt6, libadwaita) que ayuden a mejorar la precisión de coordenadas `(x, y)` en Linux.

---

## 2. Desarrollo y Pull Requests

### Estructura del Proyecto
- `clicky_linux/ui/overlay.py`: Ventana transparente click-through en PyQt6 (60 FPS).
- `clicky_linux/core/capture.py`: Captura de pantalla multi-entorno (Wayland Spectacle, Grim, Scrot, Qt fallback).
- `clicky_linux/vision/optimizer.py`: Compresión y reescalado Lanczos para ahorrar hasta un 80% de tokens visuales.
- `clicky_linux/vision/router.py`: Enrutador entre OpenClaw, Gemini API y modo local.
- `clicky_linux/core/voice.py` & `listener.py`: TTS y STT para Linux.
- `clicky_linux/core/agent_executor.py`: Modo agente Hands-Free con diálogo nativo de confirmación (`kdialog` / `zenity`).
- `clicky_linux/core/budget_guard.py`: Guardián de presupuesto con tope por tarea y mensual para llamadas a modelos premium (Claude Sonnet).

### Ejecutar los Tests
```bash
python3 -m unittest discover -s tests
```
