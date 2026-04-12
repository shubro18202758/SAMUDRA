#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Project SAMUDRA — Localhost Edge-Node Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
C="\033[36m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; N="\033[0m"
step() { printf "${C}[*] %s${N}\n" "$1"; }
ok()   { printf "${G}[✓] %s${N}\n" "$1"; }
warn() { printf "${Y}[!] %s${N}\n" "$1"; }
fail() { printf "${R}[✗] %s${N}\n" "$1"; exit 1; }

# ─── ASCII Art ────────────────────────────────────────────────────────────────
cat << 'BANNER'

    ███████╗ █████╗ ███╗   ███╗██╗   ██╗██████╗ ██████╗  █████╗
    ██╔════╝██╔══██╗████╗ ████║██║   ██║██╔══██╗██╔══██╗██╔══██╗
    ███████╗███████║██╔████╔██║██║   ██║██║  ██║██████╔╝███████║
    ╚════██║██╔══██║██║╚██╔╝██║██║   ██║██║  ██║██╔══██╗██╔══██║
    ███████║██║  ██║██║ ╚═╝ ██║╚██████╔╝██████╔╝██║  ██║██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

            ╔══════════════════════════════════════════╗
            ║   Project SAMUDRA Edge Node Booting...   ║
            ║    Maritime Fuel Intelligence Platform    ║
            ╚══════════════════════════════════════════╝

BANNER

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PID=""
FRONTEND_PID=""

# ─── Cleanup trap ─────────────────────────────────────────────────────────────
cleanup() {
    step "Shutting down services..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null && ok "Backend stopped"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && ok "Frontend stopped"
    ok "All services stopped. Edge node offline."
}
trap cleanup EXIT INT TERM

# ─── Port check ──────────────────────────────────────────────────────────────
port_busy() {
    (echo >/dev/tcp/127.0.0.1/"$1") 2>/dev/null && return 0 || return 1
}

# ─── Validate structure ──────────────────────────────────────────────────────
step "Validating project structure..."
[ -d "$BACKEND" ]  || fail "Backend not found at $BACKEND"
[ -d "$FRONTEND" ] || fail "Frontend not found at $FRONTEND"
ok "Project root: $ROOT"

# ─── Port availability ───────────────────────────────────────────────────────
step "Checking port availability..."
port_busy $BACKEND_PORT  && fail "Port $BACKEND_PORT already in use"
ok "Port $BACKEND_PORT available (Backend/FastAPI)"
port_busy $FRONTEND_PORT && fail "Port $FRONTEND_PORT already in use"
ok "Port $FRONTEND_PORT available (Frontend/Vite)"

# ─── Prerequisites ───────────────────────────────────────────────────────────
step "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || fail "Python 3 not found"
ok "Python: $(python3 --version)"
command -v node >/dev/null 2>&1 || fail "Node.js not found"
ok "Node.js: $(node --version)"

# ─── Backend dependencies ────────────────────────────────────────────────────
step "Installing backend dependencies..."
if [ -f "$BACKEND/requirements.txt" ]; then
    pip install -q -r "$BACKEND/requirements.txt" 2>&1 | tail -1
    ok "Backend dependencies installed"
else
    warn "No requirements.txt — skipping pip install"
fi

# ─── Frontend dependencies ───────────────────────────────────────────────────
step "Installing frontend dependencies..."
if [ -f "$FRONTEND/package.json" ]; then
    (cd "$FRONTEND" && npm install --silent 2>&1 | tail -1)
    ok "Frontend dependencies installed"
else
    warn "No package.json — skipping npm install"
fi

# ─── Launch backend ──────────────────────────────────────────────────────────
step "Launching backend (uvicorn :$BACKEND_PORT)..."
(cd "$BACKEND" && python3 -m uvicorn app.main:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" \
    --ws-ping-interval 20 --ws-ping-timeout 20 \
    > "$ROOT/backend.log" 2>&1) &
BACKEND_PID=$!

# ─── Health check ────────────────────────────────────────────────────────────
step "Waiting for backend health check..."
for i in $(seq 1 30); do
    sleep 0.5
    if curl -sf "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        ok "Backend healthy at http://localhost:$BACKEND_PORT"
        break
    fi
    if [ "$i" -eq 30 ]; then
        fail "Backend failed to start within 15s. Check backend.log"
    fi
done

# ─── Launch frontend ─────────────────────────────────────────────────────────
step "Launching frontend (vite :$FRONTEND_PORT)..."
(cd "$FRONTEND" && npm run dev > "$ROOT/frontend.log" 2>&1) &
FRONTEND_PID=$!
sleep 3
ok "Frontend dev server at http://localhost:$FRONTEND_PORT"

# ─── Open browser ────────────────────────────────────────────────────────────
step "Opening browser..."
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$FRONTEND_PORT"
elif command -v open >/dev/null 2>&1; then
    open "http://localhost:$FRONTEND_PORT"
fi
ok "Browser launched"

# ─── Summary ─────────────────────────────────────────────────────────────────
printf "\n"
printf "${G}  ╔════════════════════════════════════════════════╗${N}\n"
printf "${G}  ║  SAMUDRA Edge Node Online                     ║${N}\n"
printf "${G}  ║                                               ║${N}\n"
printf "${G}  ║  Backend:   http://localhost:%-5s            ║${N}\n" "$BACKEND_PORT"
printf "${G}  ║  Frontend:  http://localhost:%-5s            ║${N}\n" "$FRONTEND_PORT"
printf "${G}  ║  WebSocket: ws://localhost:%s/ws/telemetry ║${N}\n" "$BACKEND_PORT"
printf "${G}  ║                                               ║${N}\n"
printf "${G}  ║  Press Ctrl+C to stop all services            ║${N}\n"
printf "${G}  ╚════════════════════════════════════════════════╝${N}\n\n"

# ─── Wait ─────────────────────────────────────────────────────────────────────
step "Services running. Press Ctrl+C to stop..."
wait
