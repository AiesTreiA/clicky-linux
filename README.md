# 🐧 Clicky Linux (`clicky-linux`)

> **The open-source AI desktop buddy for Linux that literally points where to click.**

Inspired by [HeyClicky](https://www.heyclicky.com) / [farzaa/clicky](https://github.com/farzaa/clicky), re-architected natively for Linux (Wayland & X11).

---

## ✨ Features
- **🎯 Visual Pointer Overlay:** A non-intrusive, click-through animated pointer that renders directly over your desktop without stealing focus.
- **👁️ Multimodal Screen Understanding:** Analyzes your active workspace and returns exact `(x, y)` coordinates along with spoken guidance.
- **⚡ Token Optimization (Model Cascading):** Designed for extreme token efficiency:
  - Downscaled ROIs (Region of Interest)
  - Micro JSON schemas for fast responses
  - BYOK (*Bring Your Own Key*) + Community Token Pooling via [OpenClaw](https://openclaw.ai)
  - Full local execution option (Whisper + Ollama + Kokoro TTS = $0 / 0 tokens)
- **🐧 Native Linux Integration:** Works seamlessly on Wayland (KDE Plasma, GNOME, wlroots) and X11 via XDG Desktop Portal / Spectacle.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- PyQt6
- Desktop environment running Wayland or X11

### 2. Test Pointer Overlay
```bash
python3 -m clicky_linux.test_pointer --x 600 --y 350 --label "Click here to save"
```

### 3. Run Full Flow (Capture + Locate + Point)
```bash
export GEMINI_API_KEY="your-api-key"
python3 -m clicky_linux.main "dónde está el botón de enviar"
```

---

## 🗺️ Roadmap
- [x] **v0.1 (Iteration 1):** Core click-through Wayland/X11 overlay + screen capturer.
- [ ] **v0.2 (Iteration 2):** Multimodal ROI optimizer and OpenClaw model router.
- [ ] **v0.3 (Iteration 3):** Global Push-to-Talk hotkey + ultra-fast local STT/TTS (Whisper/Piper).
- [ ] **v0.4 (Iteration 4):** Community token pooling (crowdsourced AI tokens) & BYOK config manager.
- [ ] **v0.5 (Iteration 5):** Optional hands-free agent mode (auto-click with user approval) + Flatpak packaging.

---

## 📄 License
MIT License. Built by the open-source community.
