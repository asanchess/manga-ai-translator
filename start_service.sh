#!/usr/bin/env bash
# ==============================================================================
# Manga AI Translator Studio — POSIX Turnkey Service Launcher (Linux / macOS)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "  ⚡ Manga AI Translator Studio — Turnkey Service Launcher (POSIX)"
echo "======================================================================"
echo ""

# Cleanup trap to ensure background processes are gracefully stopped on exit
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down Manga AI Translator services..."
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo " -> Stopping Backend Server (PID $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo " -> Stopping Frontend Server (PID $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo "✓ All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Check Python Environment
echo "[1/4] Checking Python 3.10+ installation..."
if ! command -v python3 &>/dev/null; then
    echo "❌ [ERROR] python3 is not installed or not in PATH."
    echo "Please install Python 3.10+ using your package manager (e.g. apt, brew, dnf)."
    exit 1
fi

VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[1/4] Creating Python virtual environment in backend/venv..."
    python3 -m venv "$SCRIPT_DIR/backend/venv"
    echo "[1/4] Installing backend dependencies from backend/requirements.txt..."
    "$SCRIPT_DIR/backend/venv/bin/pip" install --upgrade pip
    "$SCRIPT_DIR/backend/venv/bin/pip" install -r "$SCRIPT_DIR/backend/requirements.txt"
fi
echo "✓ [1/4] Python environment verified: $VENV_PYTHON"
echo ""

# 2. Check Node.js and npm
echo "[2/4] Checking Node.js and Frontend dependencies..."
if ! command -v node &>/dev/null; then
    echo "❌ [ERROR] node is not installed or not in PATH."
    echo "Please install Node.js 18+ (e.g. https://nodejs.org/ or via nvm/brew/apt)."
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo "❌ [ERROR] npm is not installed or not in PATH."
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "[2/4] Installing frontend npm packages (npm install)..."
    (cd "$SCRIPT_DIR/frontend" && npm install)
fi
echo "✓ [2/4] Frontend dependencies verified."
echo ""

# 3. Launch Backend and Frontend in Background
echo "[3/4] Launching FastAPI Backend (port 8000) and Next.js Frontend (port 3000)..."
"$VENV_PYTHON" "$SCRIPT_DIR/backend/server.py" &
BACKEND_PID=$!

(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!
echo "✓ [3/4] Services spawned: Backend (PID $BACKEND_PID), Frontend (PID $FRONTEND_PID)"
echo ""

# 4. Automated Healthcheck Polling
echo "[4/4] Verifying services health status..."

# Backend Healthcheck
printf "  -> Waiting for FastAPI Backend (http://localhost:8000/api/health)... "
BACKEND_OK=0
for i in {1..45}; do
    if curl -s -f "http://localhost:8000/api/health" &>/dev/null; then
        BACKEND_OK=1
        echo " [ONLINE]"
        break
    fi
    printf "."
    sleep 1
done

if [ $BACKEND_OK -ne 1 ]; then
    echo " [TIMEOUT/FAILED]"
    echo "❌ Backend server failed to respond within 45s."
    exit 1
fi

# Frontend Healthcheck
printf "  -> Waiting for Next.js Web Studio (http://localhost:3000)... "
FRONTEND_OK=0
for i in {1..45}; do
    if curl -s -f "http://localhost:3000" &>/dev/null; then
        FRONTEND_OK=1
        echo " [ONLINE]"
        break
    fi
    printf "."
    sleep 1
done

if [ $FRONTEND_OK -ne 1 ]; then
    echo " [TIMEOUT/FAILED]"
    echo "❌ Frontend server failed to respond within 45s."
    exit 1
fi

echo ""
echo "======================================================================"
echo "  🚀 Manga AI Translator Studio is ONLINE and READY!"
echo "======================================================================"
echo "  📡 FastAPI Backend API:   http://localhost:8000  (Docs: http://localhost:8000/docs)"
echo "  🎨 Next.js Web Studio:    http://localhost:3000  (Reader & Dashboard)"
echo "  📦 Chapter Storage:       backend/data/manga"
echo "======================================================================"
echo ""

# Open browser if graphical session is available
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:3000" 2>/dev/null || true
elif command -v open &>/dev/null; then
    open "http://localhost:3000" 2>/dev/null || true
fi

echo "Press [Ctrl+C] to stop all services..."
wait
