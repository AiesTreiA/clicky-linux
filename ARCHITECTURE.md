# Clicky Linux: Estado del Arte, Optimización de Modelos y Arquitectura

Documento base para la implementación de **Clicky para Linux** utilizando la infraestructura disponible (Antigravity + OpenClaw + Ecosistema Open Source).

---

## 1. Inventario y Estrategia de Optimización de Tokens (Model Cascading)

En tu entorno tienes acceso a múltiples modelos en **Antigravity** y en **OpenClaw** (DeepSeek, Gemini Flash-Lite, GPT/Codex, y Ollama local).

Para que Clicky consuma el **mínimo número de tokens** y permita a la comunidad colaborar sin agotar cuotas, aplicamos la técnica de **Cascada Jerárquica de Modelos**:

```
[ Usuario habla (Push-to-Talk) ]
               │
               ▼
1. Capa Local (0 Tokens / Costo Cero)
   • STT: Whisper local (faster-whisper)
   • Detección de intención básica
               │
               ▼
2. Filtro de Visión y Contexto (Ultra-Bajo Consumo)
   • OmniParser / UI OCR local o Gemini 3.1 Flash-Lite / DeepSeek Flash
   • Downscaling inteligente de resolución de pantalla (720p / recortes ROIs)
               │
               ▼
3. Razonamiento Multimodal (Si se requiere instrucción compleja)
   • OpenClaw Gateway / Gemini Flash / GPT-5.6
   • Devuelve exclusivamente:
     {"action": "point", "x": 1042, "y": 380, "speech": "Haz clic en Guardar"}
               │
               ▼
4. Síntesis de Voz Local (0 Tokens)
   • Piper TTS o Kokoro TTS local
```

### Tabla de Routing de Modelos

| Tarea | Modelo Óptimo | Proveedor / Runtime | Costo / Tokens |
| :--- | :--- | :--- | :--- |
| **STT (Audio a Texto)** | Whisper-base | Local (`faster-whisper`) | 0 tokens |
| **Parsing de UI (Bounding boxes)** | OmniParser / Screen-OCR | Local / ONNX | 0 tokens |
| **Detección rápida y Coordenadas** | `google/gemini-3.1-flash-lite` | OpenClaw / Antigravity | Ultra-bajo |
| **Fallback y Chat general** | `deepseek/deepseek-flash` | OpenClaw | Muy bajo |
| **Tareas complejas de Agente** | `openai/gpt-5.6-terra` | OpenClaw OAuth | Premium / Bajo demanda |
| **TTS (Texto a Audio)** | Kokoro-82M / Piper | Local | 0 tokens |

---

## 2. Hallazgos del Estado del Arte (GitHub Benchmarks)

Del barrido ejecutado en el script `benchmark_fetcher.py`:

1. **[farzaa/clicky](https://github.com/farzaa/clicky) (7,843 ⭐):**
   * *Core en Swift para macOS*: Emplea un overlay transparente passthrough sobre la pantalla y hotkeys globales de push-to-talk.
   * *Lección:* La interfaz debe ser minimalista: sólo una mano/cursor animado y voz que guía al usuario paso a paso sin saturar la pantalla.

2. **[microsoft/OmniParser](https://github.com/microsoft/OmniParser) (25,594 ⭐):**
   * Convierte capturas de pantalla de cualquier SO en elementos interactivos parseados con cajas delimitadoras (bounding boxes).
   * *Lección:* Si pasamos la pantalla primero por OmniParser local o crop de UI, el prompt enviado al LLM requiere solo una lista estructurada o una imagen con etiquetas numéricas, reduciendo los tokens de visión en un **70-80%**.

3. **[bytedance/UI-TARS](https://github.com/bytedance/UI-TARS) (11,646 ⭐):**
   * Agente nativo de visión GUI que predice directamente coordenadas absolutas `(x, y)` para clicks y navegación sin necesidad de APIs propietarias complejas.

4. **[showlab/computer_use_ootb](https://github.com/showlab/computer_use_ootb) (1,976 ⭐):**
   * Muestra la estructura para desacoplar el bucle de visión, captura y ejecución de acciones.

---

## 3. Arquitectura Específica para Linux (Wayland + X11)

### Componentes:
1. **Screen Capture:**
   * Wayland: `XDG Desktop Portal (org.freedesktop.portal.ScreenCast / Screenshot)` o `grim` en compositores wlroots (Hyprland/Sway).
   * X11: `xlib` o `scrot`.
2. **Transparent Overlay Window:**
   * Ventana transparente con bandera click-through (`XShape` en X11 o `wlr-layer-shell` / `GtkWindow` con `cairo_region_create()` en Wayland).
   * Dibuja un sprite animado de un dedo/cursor señalando las coordenadas `(x, y)`.
3. **Global Push-to-Talk:**
   * Wayland: `XDG Global Shortcuts Portal` o lectura de eventos vía `/dev/input/event*` (con `evdev`).
4. **Pool Comunitario de Tokens:**
   * Permitir `Bring-Your-Own-Key` (BYOK) para DeepSeek, Gemini, OpenAI u Ollama local.
   * Conexión directa a través de OpenClaw Gateway (`openclaw agent`).
