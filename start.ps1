#!/usr/bin/env pwsh
# ═══════════════════════════════════════════════════════════════════════════════
# Project SAMUDRA — Localhost Edge-Node Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ─── ASCII Art ────────────────────────────────────────────────────────────────
function Show-Banner {
    $banner = @"

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

"@
    Write-Host $banner -ForegroundColor Cyan
}

# ─── Logging helpers ──────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red }

# ─── Port check ──────────────────────────────────────────────────────────────
function Test-Port {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpClient]::new()
        $listener.Connect("127.0.0.1", $Port)
        $listener.Close()
        return $true
    } catch {
        return $false
    }
}

# ─── Main ─────────────────────────────────────────────────────────────────────
Show-Banner

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$backendPort  = 8000
$frontendPort = 3000

# — Validate directory structure ——————————————————————————————————————————
Write-Step "Validating project structure..."
if (-not (Test-Path $backendDir))  { Write-Fail "Backend not found at $backendDir";  exit 1 }
if (-not (Test-Path $frontendDir)) { Write-Fail "Frontend not found at $frontendDir"; exit 1 }
Write-Ok "Project root: $root"

# — Check port availability ——————————————————————————————————————————————
Write-Step "Checking port availability..."
if (Test-Port $backendPort) {
    Write-Fail "Port $backendPort already in use. Stop the existing process first."
    exit 1
}
Write-Ok "Port $backendPort available (Backend/FastAPI)"

if (Test-Port $frontendPort) {
    Write-Fail "Port $frontendPort already in use. Stop the existing process first."
    exit 1
}
Write-Ok "Port $frontendPort available (Frontend/Vite)"

# — Check prerequisites ——————————————————————————————————————————————————
Write-Step "Checking prerequisites..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Fail "Python not found. Install Python 3.12+"; exit 1
}
$pyVer = python --version 2>&1
Write-Ok "Python: $pyVer"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Fail "Node.js not found. Install Node 22+"; exit 1
}
$nodeVer = node --version 2>&1
Write-Ok "Node.js: $nodeVer"

# — Install backend dependencies ——————————————————————————————————————————
Write-Step "Installing backend dependencies..."
Push-Location $backendDir
try {
    if (Test-Path "requirements.txt") {
        pip install -q -r requirements.txt 2>&1 | Out-Null
        Write-Ok "Backend dependencies installed"
    } else {
        Write-Warn "No requirements.txt — skipping pip install"
    }
} finally {
    Pop-Location
}

# — Install frontend dependencies ————————————————————————————————————————
Write-Step "Installing frontend dependencies..."
Push-Location $frontendDir
try {
    if (Test-Path "package.json") {
        npm install --silent 2>&1 | Out-Null
        Write-Ok "Frontend dependencies installed"
    } else {
        Write-Warn "No package.json — skipping npm install"
    }
} finally {
    Pop-Location
}

# — Launch backend ———————————————————————————————————————————————————————
Write-Step "Launching backend (uvicorn :$backendPort)..."
$backendProc = Start-Process -PassThru -NoNewWindow -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$backendPort", "--ws-ping-interval", "20", "--ws-ping-timeout", "20" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput (Join-Path $root "backend.log") `
    -RedirectStandardError (Join-Path $root "backend-err.log")

# Wait for backend health check
Write-Step "Waiting for backend health check..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:$backendPort/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp) { $ready = $true; break }
    } catch { }
}
if ($ready) {
    Write-Ok "Backend healthy at http://localhost:$backendPort"
} else {
    Write-Fail "Backend failed to start within 15s. Check backend-err.log"
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# — Launch frontend ——————————————————————————————————————————————————————
Write-Step "Launching frontend (vite :$frontendPort)..."
$frontendProc = Start-Process -PassThru -NoNewWindow -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput (Join-Path $root "frontend.log") `
    -RedirectStandardError (Join-Path $root "frontend-err.log")

# Give Vite a moment to bind
Start-Sleep -Seconds 3
Write-Ok "Frontend dev server at http://localhost:$frontendPort"

# — Open browser ————————————————————————————————————————————————————
Write-Step "Opening browser..."
Start-Process "http://localhost:$frontendPort"
Write-Ok "Browser launched"

# — Summary ——————————————————————————————————————————————————————————
Write-Host ""
Write-Host "  ╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║  SAMUDRA Edge Node Online                     ║" -ForegroundColor Green
Write-Host "  ║                                               ║" -ForegroundColor Green
Write-Host "  ║  Backend:   http://localhost:$backendPort            ║" -ForegroundColor Green
Write-Host "  ║  Frontend:  http://localhost:$frontendPort            ║" -ForegroundColor Green
Write-Host "  ║  WebSocket: ws://localhost:$backendPort/ws/telemetry ║" -ForegroundColor Green
Write-Host "  ║                                               ║" -ForegroundColor Green
Write-Host "  ║  Press Ctrl+C to stop all services            ║" -ForegroundColor Green
Write-Host "  ╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# — Cleanup on exit ——————————————————————————————————————————————————
try {
    Write-Step "Services running. Press Ctrl+C to stop..."
    while ($true) {
        if ($backendProc.HasExited) { Write-Warn "Backend exited unexpectedly"; break }
        if ($frontendProc.HasExited) { Write-Warn "Frontend exited unexpectedly"; break }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Step "Shutting down services..."
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
    Write-Ok "All services stopped. Edge node offline."
}
