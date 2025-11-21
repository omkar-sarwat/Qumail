#!/usr/bin/env pwsh
# QuMail Complete Startup and Test Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Complete System Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Clean up any existing processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*node*" -or 
    $_.ProcessName -like "*electron*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Cleanup complete" -ForegroundColor Green
Write-Host ""

# Start KME1
Write-Host "Starting KME1 Server (port 8010)..." -ForegroundColor Cyan
$KME1 = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'KME1 Server' -ForegroundColor Green; cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8010'; `$env:KME_ID='1'; python app.py" -PassThru
Start-Sleep -Seconds 2

# Start KME2
Write-Host "Starting KME2 Server (port 8020)..." -ForegroundColor Cyan
$KME2 = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'KME2 Server' -ForegroundColor Green; cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8020'; `$env:KME_ID='2'; python app.py" -PassThru
Start-Sleep -Seconds 3

# Start Backend
Write-Host "Starting Backend Server (port 8000)..." -ForegroundColor Cyan
$Backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Backend Server' -ForegroundColor Green; cd '$SCRIPT_DIR\qumail-backend'; & 'venv\Scripts\Activate.ps1'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru
Start-Sleep -Seconds 5

# Start Frontend
Write-Host "Starting Vite Dev Server (port 5173)..." -ForegroundColor Cyan
$Frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Vite Dev Server' -ForegroundColor Green; cd '$SCRIPT_DIR\qumail-frontend'; npm run dev" -PassThru
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Wait for services to be fully ready
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test KME1
Write-Host "Testing KME1 (http://localhost:8010)..." -ForegroundColor Cyan
try {
    $kme1Response = Invoke-WebRequest -Uri "http://localhost:8010/api/v1/kme/status" -Method GET -TimeoutSec 5
    if ($kme1Response.StatusCode -eq 200) {
        Write-Host "KME1 is running" -ForegroundColor Green
    }
} catch {
    Write-Host "KME1 not responding" -ForegroundColor Red
}

# Test KME2
Write-Host "Testing KME2 (http://localhost:8020)..." -ForegroundColor Cyan
try {
    $kme2Response = Invoke-WebRequest -Uri "http://localhost:8020/api/v1/kme/status" -Method GET -TimeoutSec 5
    if ($kme2Response.StatusCode -eq 200) {
        Write-Host "KME2 is running" -ForegroundColor Green
    }
} catch {
    Write-Host "KME2 not responding" -ForegroundColor Red
}

# Test Backend
Write-Host "Testing Backend (http://localhost:8000)..." -ForegroundColor Cyan
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 5
    if ($backendResponse.StatusCode -eq 200) {
        Write-Host "Backend is running" -ForegroundColor Green
    }
} catch {
    Write-Host "Backend not responding" -ForegroundColor Red
}

# Test Frontend
Write-Host "Testing Vite Dev Server (http://localhost:5173)..." -ForegroundColor Cyan
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -TimeoutSec 5
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "Vite Dev Server is running" -ForegroundColor Green
    }
} catch {
    Write-Host "Vite Dev Server not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "System Status Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KME1:     http://localhost:8010" -ForegroundColor White
Write-Host "KME2:     http://localhost:8020" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. All services are running in separate terminals" -ForegroundColor White
Write-Host "2. Wait for Backend to show 'KME servers are ready!'" -ForegroundColor White
Write-Host "3. Then run: cd qumail-frontend; npm run electron:start" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to open Electron app..." -ForegroundColor Yellow
Read-Host

# Compile and start Electron
Write-Host "Compiling Electron..." -ForegroundColor Cyan
cd "$SCRIPT_DIR\qumail-frontend"
npm run electron:compile

Write-Host "Starting Electron app..." -ForegroundColor Cyan
npm run electron:start
