# Start QuMail in Electron Development Mode
# This script starts backend services and launches Electron app in dev mode

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Electron - Development Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to start process and track it
$global:processes = @()

function Start-TrackedProcess {
    param(
        [string]$Name,
        [string]$Command,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [hashtable]$Environment = @{}
    )
    
    Write-Host "Starting $Name..." -ForegroundColor Yellow
    
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Command
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError = $false
    $psi.CreateNoWindow = $false
    
    foreach ($key in $Environment.Keys) {
        $psi.EnvironmentVariables[$key] = $Environment[$key]
    }
    
    $process = [System.Diagnostics.Process]::Start($psi)
    $global:processes += $process
    
    Write-Host "[OK] $Name started (PID: $($process.Id))" -ForegroundColor Green
    return $process
}

# Cleanup function
function Stop-AllProcesses {
    Write-Host ""
    Write-Host "Shutting down services..." -ForegroundColor Yellow
    
    foreach ($proc in $global:processes) {
        if ($proc -and -not $proc.HasExited) {
            try {
                $proc.Kill()
                Write-Host "Stopped process $($proc.Id)" -ForegroundColor Gray
            } catch {
                Write-Host "Failed to stop process $($proc.Id): $_" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "All services stopped" -ForegroundColor Green
}

# Register cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-AllProcesses
}

# Trap Ctrl+C
$null = Register-EngineEvent -SourceIdentifier ConsoleBreak -Action {
    Stop-AllProcesses
    exit
}

try {
    # Check Python
    Write-Host "Checking Python..." -ForegroundColor Cyan
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Host "[ERROR] Python not found!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Python found: $($pythonCmd.Source)" -ForegroundColor Green
    
    # Check Node.js
    Write-Host "Checking Node.js..." -ForegroundColor Cyan
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Write-Host "[ERROR] Node.js not found!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Node.js found: $($nodeCmd.Source)" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Starting services..." -ForegroundColor Cyan
    Write-Host ""
    
    # Start KME1
    $kme1Env = @{
        "PYTHONUNBUFFERED" = "1"
        "KME_PORT" = "8010"
        "KME_ID" = "KME1"
    }
    Start-TrackedProcess -Name "KME1" `
        -Command "python" `
        -Arguments "app.py" `
        -WorkingDirectory "$PSScriptRoot\next-door-key-simulator" `
        -Environment $kme1Env
    
    Start-Sleep -Seconds 2
    
    # Start KME2
    $kme2Env = @{
        "PYTHONUNBUFFERED" = "1"
        "KME_PORT" = "8020"
        "KME_ID" = "KME2"
    }
    Start-TrackedProcess -Name "KME2" `
        -Command "python" `
        -Arguments "app.py" `
        -WorkingDirectory "$PSScriptRoot\next-door-key-simulator" `
        -Environment $kme2Env
    
    Start-Sleep -Seconds 2
    
    # Start Backend
    $backendEnv = @{
        "PYTHONUNBUFFERED" = "1"
        "QUMAIL_ENV" = "development"
        "BACKEND_PORT" = "8000"
        "KME1_URL" = "http://localhost:8010"
        "KME2_URL" = "http://localhost:8020"
    }
    Start-TrackedProcess -Name "Backend" `
        -Command "python" `
        -Arguments "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" `
        -WorkingDirectory "$PSScriptRoot\qumail-backend" `
        -Environment $backendEnv
    
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "Checking backend health..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "[OK] Backend is healthy!" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Backend health check failed, but continuing..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Starting Electron app..." -ForegroundColor Cyan
    Set-Location "$PSScriptRoot\qumail-frontend"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Start Electron in dev mode
    npm run electron:dev
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
} finally {
    Stop-AllProcesses
}

Write-Host ""
Write-Host "QuMail Electron stopped" -ForegroundColor Cyan
