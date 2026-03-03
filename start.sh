#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# SolarIntel — Launcher
# Starts FastAPI backend + serves index.html + opens browser
# ──────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

API_PORT=8000
HTTP_PORT=8080

# Cleanup on exit
cleanup() {
    echo ""
    echo "[SolarIntel] Arret en cours..."
    kill "$API_PID" 2>/dev/null || true
    kill "$HTTP_PID" 2>/dev/null || true
    echo "[SolarIntel] Termine."
}
trap cleanup EXIT INT TERM

# 1. Start FastAPI backend
echo "[SolarIntel] Demarrage de l'API FastAPI sur le port $API_PORT..."
uvicorn solarintel.api:app --host 0.0.0.0 --port "$API_PORT" --log-level info &
API_PID=$!

# 2. Serve static files (index.html)
echo "[SolarIntel] Serveur HTTP sur le port $HTTP_PORT..."
python3 -m http.server "$HTTP_PORT" --bind 0.0.0.0 &
HTTP_PID=$!

# 3. Wait a moment then open browser
sleep 2
URL="http://localhost:$HTTP_PORT/index.html"
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
echo "  Frontend : http://localhost:$HTTP_PORT/index.html"
echo "  API docs : http://localhost:$API_PORT/docs"
echo "  Ctrl+C pour arreter"
echo "════════════════════════════════════════════════════════"
echo ""

# Keep script alive
wait
