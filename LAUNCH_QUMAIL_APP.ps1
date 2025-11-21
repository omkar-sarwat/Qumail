# QuMail Complete Launcher
# Starts backend, KME servers, and launches the Electron app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Secure Email - Complete Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# Function to start a process in a new window
function Start-ProcessInNewWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )
    
    Write-Host "Starting $Title..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$Host.UI.RawUI.WindowTitle = '$Title'; cd '$WorkingDirectory'; $Command }" -WorkingDirectory $WorkingDirectory
    Start-Sleep -Seconds 2
}

Write-Host "Checking if services are already running..." -ForegroundColor Cyan
Write-Host ""

# Check ports
$backendRunning = Test-Port -Port 8000
$kme1Running = Test-Port -Port 8010
$kme2Running = Test-Port -Port 8020

if ($backendRunning -and $kme1Running -and $kme2Running) {
    Write-Host "All services are already running!" -ForegroundColor Green
    Write-Host "  Backend: Running on port 8000" -ForegroundColor Green
    Write-Host "  KME1: Running on port 8010" -ForegroundColor Green
    Write-Host "  KME2: Running on port 8020" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Starting required services..." -ForegroundColor Yellow
    Write-Host ""
    
    # Start KME1 if not running
    if (-not $kme1Running) {
        $kme1Dir = Join-Path $scriptDir "next-door-key-simulator"
        Start-ProcessInNewWindow -Title "QuMail - KME Server 1 (Port 8010)" -Command "python app.py --port 8010 --cert-path ./certs/kme-1-local-zone --mode kme1" -WorkingDirectory $kme1Dir
        Write-Host "  KME1 started on port 8010" -ForegroundColor Green
    }
    
    # Start KME2 if not running
    if (-not $kme2Running) {
        $kme2Dir = Join-Path $scriptDir "next-door-key-simulator"
        Start-ProcessInNewWindow -Title "QuMail - KME Server 2 (Port 8020)" -Command "python app.py --port 8020 --cert-path ./certs/kme-2-local-zone --mode kme2" -WorkingDirectory $kme2Dir
        Write-Host "  KME2 started on port 8020" -ForegroundColor Green
    }
    
    # Wait for KME servers to start
    Write-Host ""
    Write-Host "Waiting for KME servers to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Start Backend if not running
    if (-not $backendRunning) {
        $backendDir = Join-Path $scriptDir "qumail-backend"
        Start-ProcessInNewWindow -Title "QuMail - Backend Server (Port 8000)" -Command "& '.\venv\Scripts\Activate.ps1'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $backendDir
        Write-Host "  Backend started on port 8000" -ForegroundColor Green
    }
    
    # Wait for backend to start
    Write-Host ""
    Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "Launching QuMail Application..." -ForegroundColor Cyan
Write-Host ""

# Launch the Electron app
$appPath = Join-Path $scriptDir "qumail-frontend\release\QuMail-Portable\QuMail.exe"

if (Test-Path $appPath) {
    Start-Process -FilePath $appPath
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "QuMail Application Launched!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services running:" -ForegroundColor Cyan
    Write-Host "  Backend: http://localhost:8000" -ForegroundColor White
    Write-Host "  KME1: http://localhost:8010" -ForegroundColor White
    Write-Host "  KME2: http://localhost:8020" -ForegroundColor White
    Write-Host ""
    Write-Host "The application window will open shortly..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press any key to exit this launcher (services will keep running)..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Host "[ERROR] QuMail.exe not found at: $appPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please build the application first by running:" -ForegroundColor Yellow
    Write-Host "  .\PACKAGE_ELECTRON_MANUALLY.ps1" -ForegroundColor White
    Write-Host ""
    Pause
}
