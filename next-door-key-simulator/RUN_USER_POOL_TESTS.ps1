# Start KME Server and Test User Key Pools
# This script starts the Next Door Key Simulator and runs the test suite

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Door Key Simulator - Test Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`nPython: $($pythonCmd.Source)" -ForegroundColor Green

# Check for required packages
Write-Host "`nChecking required packages..." -ForegroundColor Yellow
python -c "import flask; import requests; print('Required packages available')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    pip install flask requests python-dotenv
}

# Start KME server in background
Write-Host "`nStarting KME Server on port 8010..." -ForegroundColor Cyan

$env:KME_ID = "1"
$env:HOST = "127.0.0.1"
$env:PORT = "8010"
$env:USE_HTTPS = "false"

$serverProcess = Start-Process python -ArgumentList "app.py" -PassThru -NoNewWindow

# Wait for server to start
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$serverReady = $false

while ($attempt -lt $maxAttempts -and -not $serverReady) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8010/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $serverReady = $true
            Write-Host "Server is ready!" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "." -NoNewline
    }
}

if (-not $serverReady) {
    Write-Host "`nError: Server failed to start within timeout" -ForegroundColor Red
    if ($serverProcess) {
        Stop-Process $serverProcess -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

# Run tests
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Running User Key Pool Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

python test_simple_key_pools.py
$testResult = $LASTEXITCODE

# Stop server
Write-Host "`nStopping KME Server..." -ForegroundColor Yellow
if ($serverProcess) {
    Stop-Process $serverProcess -Force -ErrorAction SilentlyContinue
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($testResult -eq 0) {
    Write-Host "  All tests passed!" -ForegroundColor Green
} else {
    Write-Host "  Some tests failed" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

exit $testResult
