# 🐧 Clicky Linux (`clicky-linux`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux Wayland & X11](https://img.shields.io/badge/Platform-Wayland%20%7C%20X11-orange.svg)](#)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](#)

> **The open-source AI desktop buddy for Linux that literally points where to click.**

Inspired by [HeyClicky](https://www.heyclicky.com) ([farzaa/clicky](https://github.com/farzaa/clicky)), built natively for the Linux desktop ecosystem (KDE Plasma, GNOME, Hyprland/wlroots, and X11) with community-driven token optimization.

---

## ✨ Key Features

- **🎯 Click-Through Visual Pointer Overlay:** A non-intrusive, 60 FPS animated pointer rendered via PyQt6 (`WindowTransparentForInput`) directly over your active screen without stealing focus or blocking mouse clicks.
- **👁️ Multimodal Screen Understanding:** Captures your screen (`spectacle`, `grim`, `scrot`, or Qt grab) and locates exact `(x, y)` coordinates for any button, menu, or UI element.
- **⚡ Extreme Token Optimization (Model Cascading):**
  - Automatic Lanczos downscaling to 1280px before vision inference (saves up to **75–80% of vision tokens**) with automatic coordinate re-scaling back to native 4K/2K resolution.
  - Supports **OpenClaw** multi-model routing, **Gemini Flash**, **DeepSeek**, and **100% free local models** via **Ollama**.
- **🔊 Zero-Token Local Voice (TTS & STT):** Speaks instructions out loud using native Linux `spd-say` / OpenClaw TTS, and records voice queries via PipeWire/ALSA (`arecord`).
- **🤝 Community Token Pool & BYOK:** Bring Your Own Key or connect to community-contributed inference nodes to help train and run open-source Linux GUI agents.
- **🛡️ BudgetGuard for Premium Models:** Built-in cost estimator and monthly cap ledger (`clicky_linux.core.budget_guard`) so you never accidentally overspend on premium APIs like Claude Sonnet.
- **🖱️ Optional Hands-Free Agent Mode (`--auto-click`):** Can move the cursor or click on your behalf after asking for explicit approval via a native `kdialog` / `zenity` confirmation popup.

---

## 🚀 Quick Start

### 1. Install Desktop App (Menu Icon + System Tray + Spotlight Bar)
```bash
git clone https://github.com/AiesTreiA/clicky-linux.git
cd clicky-linux
./install.sh
```
Once installed:
- **Global Hotkey:** Press **`Super + C`** (Windows key + C) from anywhere on your desktop to summon Clicky instantly.
- **Menu Launcher:** Press your **Super / Windows** key and open **Clicky Linux** from your application menu (or run `clicky-app`).
- A sleek floating bar appears on your active screen and an icon stays in your **System Tray** (next to the clock).
- Type or ask what you are looking for, press **Enter**, and Clicky will hide its bar, analyze your active monitor, speak to you with natural voice, and guide you directly on your screen!

### 2. Test the Visual Pointer Overlay
```bash
python3 -m clicky_linux.test_pointer --x 600 --y 350 --label "Haz clic aquí para guardar"
```

### 3. Ask Clicky to Find Any Element on Your Screen
```bash
# Uses OpenClaw Gateway or GEMINI_API_KEY automatically
python3 -m clicky_linux.main "dónde está el botón de configuración"
```

### 4. Hands-Free Agent Mode (with Native Approval Dialog)
```bash
python3 -m clicky_linux.main "botón de cerrar o guardar" --auto-click
```

### 5. Manage Configuration & Community Token Pool
```bash
# View current configuration
python3 -m clicky_linux.main --config

# Set a custom configuration parameter
python3 -m clicky_linux.main --set tokens.max_resolution_px=1280

# Check Community Token Pool status
python3 -m clicky_linux.main --pool-status
```

### 6. Use BudgetGuard (Protected Claude Sonnet CLI via OpenClaw)
```bash
# Dry-run cost estimation
python3 -m clicky_linux.core.budget_guard "Analiza la arquitectura de este módulo" --dry-run

# Check monthly estimated spend
python3 -m clicky_linux.core.budget_guard --status
```

---

## 🗺️ Roadmap (v0.1 → v0.5 Completed!)

- [x] **v0.1 (Iteration 1):** Core click-through Wayland/X11 overlay + universal screen capturer.
- [x] **v0.2 (Iteration 2):** Multimodal Lanczos image optimizer & OpenClaw / Gemini router.
- [x] **v0.3 (Iteration 3):** Local zero-token Linux TTS (`spd-say`) & audio listener (`arecord`).
- [x] **v0.4 (Iteration 4):** Community Token Pool manager, BYOK config CLI, and `BudgetGuard` ledger.
- [x] **v0.5 (Iteration 5):** Hands-Free Agent Mode with native KDE/GNOME confirmation dialog, unit tests, `pyproject.toml`, and public GitHub documentation.

---

## 🤝 Contributing & Donating Tokens

Want to contribute code, UI datasets for Linux desktops, or idle AI tokens to the community pool? Read [CONTRIBUTING.md](CONTRIBUTING.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## 📄 License

Released under the [MIT License](LICENSE).
