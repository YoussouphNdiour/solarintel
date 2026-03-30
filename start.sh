#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# SolarIntel — Launcher
# FastAPI sert index.html + /3d/ viewer + API sur un seul port
# ──────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

API_PORT=8000

# Cleanup on exit
cleanup() {
    echo ""
    echo "[SolarIntel] Arret en cours..."
    kill "$API_PID" 2>/dev/null || true
    echo "[SolarIntel] Termine."
}
trap cleanup EXIT INT TERM

# 0. Build 3D viewer if dist is missing or sources are newer
VIEWER_DIR="$SCRIPT_DIR/solarintel-3d"
VIEWER_DIST="$VIEWER_DIR/dist"
if [ -d "$VIEWER_DIR" ] && command -v npm &>/dev/null; then
    if [ ! -d "$VIEWER_DIST" ] || [ "$VIEWER_DIR/src" -nt "$VIEWER_DIST" ]; then
        echo "[SolarIntel] Build du viewer 3D (premiere fois ou sources modifiees)..."
        (cd "$VIEWER_DIR" && npm install --prefer-offline && npm run build)
        echo "[SolarIntel] Viewer 3D pret -> $VIEWER_DIST"
    else
        echo "[SolarIntel] Viewer 3D deja a jour."
    fi
fi

# 1. Start FastAPI (serves /, /3d/, /api/*, /assets/*)
echo "[SolarIntel] Demarrage FastAPI sur le port $API_PORT..."
uvicorn solarintel.api:app --host 0.0.0.0 --port "$API_PORT" --log-level info &
API_PID=$!

# 2. Wait then open browser
sleep 2
URL="http://localhost:$API_PORT"
echo "[SolarIntel] Ouverture de $URL"

if command -v open &>/dev/null; then
    open "$URL"
elif command -v xdg-open &>/dev/null; then
    xdg-open "$URL"
elif command -v start &>/dev/null; then
    start "$URL"
else
    echo "[SolarIntel] Ouvrez manuellement : $URL"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  SolarIntel est pret !"
echo "  App      : http://localhost:$API_PORT"
echo "  Viewer3D : http://localhost:$API_PORT/3d/"
echo "  API docs : http://localhost:$API_PORT/docs"
echo "  Ctrl+C pour arreter"
echo "════════════════════════════════════════════════════════"
echo ""

# Keep script alive
wait
