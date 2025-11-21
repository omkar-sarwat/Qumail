#!/usr/bin/env pwsh
# Manual QuMail Startup - Opens separate terminals for each service

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Opening QuMail Service Terminals" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Clean up
Write-Host "Cleaning up old processes..." -ForegroundColor Yellow
Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*node*" -or 
    $_.ProcessName -like "*electron*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Opening terminals..." -ForegroundColor Green
Write-Host ""

# KME1
Write-Host "1. KME1 Server (port 8010)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'KME1 Server' -ForegroundColor Green; cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8010'; `$env:KME_ID='1'; python app.py"

# KME2
Write-Host "2. KME2 Server (port 8020)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'KME2 Server' -ForegroundColor Green; cd '$SCRIPT_DIR\next-door-key-simulator'; `$env:KME_PORT='8020'; `$env:KME_ID='2'; python app.py"

# Backend
Write-Host "3. Backend Server (port 8000)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Backend Server' -ForegroundColor Green; cd '$SCRIPT_DIR\qumail-backend'; & 'venv\Scripts\Activate.ps1'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Electron App
Write-Host "4. Starting Electron App..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Electron App' -ForegroundColor Green; cd '$SCRIPT_DIR\qumail-frontend'; npm run electron:dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  KME1:     port 8010" -ForegroundColor White
Write-Host "  KME2:     port 8020" -ForegroundColor White
Write-Host "  Backend:  port 8000" -ForegroundColor White
Write-Host "  Electron: Launching..." -ForegroundColor White
Write-Host ""
