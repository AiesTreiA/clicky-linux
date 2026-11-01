#!/usr/bin/env python3
"""
benchmark_fetcher.py
Barrido de referencias en GitHub y estado del arte para:
1. farzaa/clicky (repositorio original Swift/macOS)
2. UI overlays y visual pointers en Linux (Wayland/X11)
3. Agentes de visión de pantalla (Screen-to-actions, OmniParser, UI-Tars, OS-World)
4. Herramientas de streaming de audio STT/TTS de baja latencia
"""

import urllib.request
import json
import sys
import os

REPOS = [
    "farzaa/clicky",
    "microsoft/OmniParser",
    "bytedance/UI-TARS",
    "showlab/computer_use_ootb",
    "Sentient-Engineering/clicky-companion"
]

def check_github_repo(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ClickyLinux-ResearchBot/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return {
                    "name": data.get("full_name"),
                    "stars": data.get("stargazers_count"),
                    "description": data.get("description"),
                    "language": data.get("language"),
                    "license": data.get("license", {}).get("spdx_id") if data.get("license") else None,
                    "topics": data.get("topics", [])
                }
    except Exception as e:
        return {"name": repo_full_name, "error": str(e)}

def main():
    results = []
    print("Iniciando barrido de referencias clave en GitHub...")
    for repo in REPOS:
        print(f"Consultando {repo}...")
        res = check_github_repo(repo)
        results.append(res)
    
    out_file = "research_references.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados guardados en {out_file}")
    for r in results:
        if "error" not in r:
            print(f"- {r['name']} ({r['stars']} ⭐) [{r['language']}]: {r['description']}")
        else:
            print(f"- {r['name']}: {r['error']}")

if __name__ == "__main__":
    main()
