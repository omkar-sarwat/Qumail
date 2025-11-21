#!/usr/bin/env pwsh
# QuMail Electron Development Mode Startup Script
# This script properly coordinates starting Vite dev server, compiling Electron, and launching the app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Electron Development Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set error handling
$ErrorActionPreference = "Stop"

# Set paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "qumail-frontend"
$BACKEND_DIR = Join-Path $SCRIPT_DIR "qumail-backend"
$KME_DIR = Join-Path $SCRIPT_DIR "next-door-key-simulator"

# Check if directories exist
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "ERROR: Frontend directory not found at $FRONTEND_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "[1/6] Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process | Where-Object { 
    $_.ProcessName -like "*electron*" -or 
    $_.ProcessName -like "*node*" -and $_.Id -ne $PID 
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[2/6] Starting Backend Server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($BackendDir)
    Set-Location $BackendDir
    if (Test-Path "venv/Scripts/Activate.ps1") {
        & "venv/Scripts/Activate.ps1"
    }
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList $BACKEND_DIR

Write-Host "   Backend starting in background (Job ID: $($backendJob.Id))..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host "[3/6] Starting KME Servers..." -ForegroundColor Yellow
$kme1Job = Start-Job -ScriptBlock {
    param($KmeDir)
    Set-Location $KmeDir
    $env:KME_PORT = "8010"
    $env:KME_ID = "KME1"
    python app.py
} -ArgumentList $KME_DIR

$kme2Job = Start-Job -ScriptBlock {
    param($KmeDir)
    Set-Location $KmeDir
    $env:KME_PORT = "8020"
    $env:KME_ID = "KME2"
    python app.py
} -ArgumentList $KME_DIR

Write-Host "   KME1 starting (Job ID: $($kme1Job.Id))..." -ForegroundColor Gray
Write-Host "   KME2 starting (Job ID: $($kme2Job.Id))..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host "[4/6] Starting Vite Dev Server..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR
$viteProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -NoNewWindow
Write-Host "   Vite dev server starting (PID: $($viteProcess.Id))..." -ForegroundColor Gray

# Wait for Vite to be ready
Write-Host "   Waiting for Vite dev server to be ready..." -ForegroundColor Gray
$maxAttempts = 30
$attempt = 0
$viteReady = $false

while ($attempt -lt $maxAttempts -and -not $viteReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $viteReady = $true
            Write-Host "   Vite dev server is ready!" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $viteReady) {
    Write-Host ""
    Write-Host "ERROR: Vite dev server failed to start!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5/6] Compiling Electron TypeScript..." -ForegroundColor Yellow
try {
    $compileOutput = npx tsc electron/main.ts electron/preload.ts --outDir dist-electron --module commonjs --esModuleInterop --resolveJsonModule --skipLibCheck --noEmit false 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   WARNING: TypeScript compilation had warnings (continuing anyway)" -ForegroundColor Yellow
    } else {
        Write-Host "   Electron files compiled successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "   ERROR compiling Electron files: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[6/6] Launching Electron App..." -ForegroundColor Yellow
$env:VITE_DEV_SERVER_URL = "http://localhost:5173"
$env:IS_DEV = "true"
$env:NODE_ENV = "development"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "QuMail Electron is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "KME1 Server:  http://localhost:8010" -ForegroundColor Cyan
Write-Host "KME2 Server:  http://localhost:8020" -ForegroundColor Cyan
Write-Host "Vite Server:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Launch Electron
npx electron dist-electron/main.js --dev

# Cleanup on exit
Write-Host ""
Write-Host "Shutting down services..." -ForegroundColor Yellow
$viteProcess | Stop-Process -Force -ErrorAction SilentlyContinue
$backendJob | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue
$kme1Job | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue
$kme2Job | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue

Write-Host "All services stopped." -ForegroundColor Green
