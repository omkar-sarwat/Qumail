#!/usr/bin/env pwsh
# Simple QuMail Startup Script - Starts all services in separate terminals

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting QuMail Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Kill any existing processes
Write-Host "[1/5] Cleaning up old processes..." -ForegroundColor Yellow
Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*node*" -or 
    $_.ProcessName -like "*electron*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start KME1
Write-Host "[2/5] Starting KME1 Server (port 8010)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8010'; `$env:KME_ID='KME1'; python app.py"
) -WindowStyle Normal
Start-Sleep -Seconds 2

# Start KME2
Write-Host "[3/5] Starting KME2 Server (port 8020)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8020'; `$env:KME_ID='KME2'; python app.py"
) -WindowStyle Normal
Start-Sleep -Seconds 2

# Start Backend
Write-Host "[4/5] Starting Backend Server (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$SCRIPT_DIR\qumail-backend'; & 'venv\Scripts\Activate.ps1'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
) -WindowStyle Normal
Start-Sleep -Seconds 5

# Start Frontend + Electron
Write-Host "[5/5] Starting Frontend and Electron..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$SCRIPT_DIR\qumail-frontend'; npm run dev"
) -WindowStyle Normal
Start-Sleep -Seconds 3

# Wait for Vite to be ready
Write-Host ""
Write-Host "Waiting for Vite dev server..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$viteReady = $false

while ($attempt -lt $maxAttempts -and -not $viteReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $viteReady = $true
        }
    } catch {
        $attempt++
        Start-Sleep -Seconds 1
    }
}

if ($viteReady) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "QuMail Services Started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "KME1 Server:  http://localhost:8010" -ForegroundColor Cyan
    Write-Host "KME2 Server:  http://localhost:8020" -ForegroundColor Cyan
    Write-Host "Vite Server:  http://localhost:5173" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now compiling and starting Electron..." -ForegroundColor Yellow
    
    # Compile and start Electron
    cd "$SCRIPT_DIR\qumail-frontend"
    npx tsc electron/main.ts electron/preload.ts --outDir dist-electron --module commonjs --esModuleInterop --resolveJsonModule --skipLibCheck --noEmit false
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Starting Electron app..." -ForegroundColor Green
        $env:VITE_DEV_SERVER_URL = "http://localhost:5173"
        $env:IS_DEV = "true"
        npx electron dist-electron/main.js --dev
    } else {
        Write-Host "Failed to compile Electron files!" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "ERROR: Vite dev server failed to start!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to close all windows and exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
