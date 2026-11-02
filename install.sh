#!/usr/bin/env bash
set -e

echo "🐧 Instalando Clicky Linux como aplicación de escritorio..."

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"

mkdir -p "$BIN_DIR"
mkdir -p "$APPS_DIR"

# 1. Crear lanzador ejecutable en ~/.local/bin/clicky-app
cat <<EOF > "$BIN_DIR/clicky-app"
#!/usr/bin/env bash
export PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"
exec python3 -m clicky_linux.ui.app "\$@"
EOF
chmod +x "$BIN_DIR/clicky-app"

# 2. Crear lanzador CLI rápido en ~/.local/bin/clicky
cat <<EOF > "$BIN_DIR/clicky"
#!/usr/bin/env bash
export PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"
exec python3 -m clicky_linux.main "\$@"
EOF
chmod +x "$BIN_DIR/clicky"

# 3. Crear entrada en el menú de aplicaciones de Linux (KDE / GNOME)
cat <<EOF > "$APPS_DIR/clicky-linux.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Clicky Linux
GenericName=AI Desktop Visual Assistant
Comment=Tu asistente visual de IA que señala dónde hacer clic
Exec=$BIN_DIR/clicky-app
Icon=preferences-desktop-cursors
Terminal=false
Categories=Utility;Accessibility;ArtificialIntelligence;
Keywords=AI;Clicky;Assistant;Pointer;
StartupNotify=false
EOF

chmod +x "$APPS_DIR/clicky-linux.desktop"
update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo ""
echo "✅ ¡Clicky Linux ha sido instalado con éxito!"
echo "   • Desde tu menú de aplicaciones (Super / Windows key): busca 'Clicky Linux'"
echo "   • O ejecútalo desde cualquier lugar con: clicky-app"
echo "   • El ícono quedará activo en tu bandeja del sistema (junto al reloj)."
