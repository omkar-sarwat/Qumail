# QuMail Complete System Startup Script
Write-Host "`n================================================================================================================" -ForegroundColor Cyan
Write-Host "QuMail Secure Email - Complete System Startup" -ForegroundColor Cyan
Write-Host "Starting: KME1 (Master) + KME2 (Slave) + Backend + Frontend" -ForegroundColor Cyan
Write-Host "================================================================================================================`n" -ForegroundColor Cyan

# Configuration
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$KME_DIR = Join-Path $SCRIPT_DIR "next-door-key-simulator"
$BACKEND_DIR = Join-Path $SCRIPT_DIR "qumail-backend"
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "qumail-frontend"

# Track PIDs
$PIDS = @{}

# Function to start process in new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkDir,
        [string]$Color = "Green"
    )
    
    Write-Host "[$Title] Starting..." -ForegroundColor $Color
    
    $proc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkDir'; `$host.UI.RawUI.WindowTitle='$Title'; Write-Host '$Title Started' -ForegroundColor $Color; $Command" -PassThru
    
    if ($proc) {
        Write-Host "  [OK] Started (PID: $($proc.Id))" -ForegroundColor Green
        return $proc.Id
    }
    else {
        Write-Host "  [FAIL] Failed to start" -ForegroundColor Red
        return $null
    }
}

# Function to check if service is responding
function Test-ServiceHealth {
    param(
        [string]$Url,
        [int]$MaxRetries = 10,
        [int]$DelaySeconds = 2
    )
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 3 -ErrorAction Stop | Out-Null
            return $true
        }
        catch {
            if ($i -eq $MaxRetries) {
                return $false
            }
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

# Step 1: Kill existing processes
Write-Host "`n[STEP 1/5] Cleaning up existing processes..." -ForegroundColor Yellow
try {
    Get-Process python, node, uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Cleaned up" -ForegroundColor Green
}
catch {
    Write-Host "  [INFO] No processes to clean" -ForegroundColor Gray
}
Start-Sleep -Seconds 2

# Step 2: Start KME1 (Master - Generates Keys)
Write-Host "`n[STEP 2/5] Starting KME1 (Master - Port 8010)..." -ForegroundColor Yellow
$KME1_PID = Start-ServiceWindow -Title "KME1 - Master (Port 8010)" -Command "`$env:KME_ID='1'; python app.py" -WorkDir $KME_DIR -Color "Magenta"

if ($KME1_PID) {
    $PIDS["KME1"] = $KME1_PID
    Write-Host "  Waiting for KME1 to be ready..." -ForegroundColor Gray
    if (Test-ServiceHealth -Url "http://localhost:8010/api/v1/kme/status" -MaxRetries 15) {
        $status = Invoke-RestMethod -Uri "http://localhost:8010/api/v1/kme/status" -TimeoutSec 5
        Write-Host "  [OK] KME1 Ready!" -ForegroundColor Green
        Write-Host "    - Role: $($status.role)" -ForegroundColor Cyan
        Write-Host "    - Pool Size: $($status.shared_pool.pool_size)/$($status.shared_pool.max_capacity)" -ForegroundColor Cyan
    }
    else {
        Write-Host "  [FAIL] KME1 failed to start properly" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Start KME2 (Slave - Retrieves Keys)
Write-Host "`n[STEP 3/5] Starting KME2 (Slave - Port 8020)..." -ForegroundColor Yellow
$KME2_PID = Start-ServiceWindow -Title "KME2 - Slave (Port 8020)" -Command "`$env:KME_ID='2'; python app.py" -WorkDir $KME_DIR -Color "Magenta"

if ($KME2_PID) {
    $PIDS["KME2"] = $KME2_PID
    Write-Host "  Waiting for KME2 to be ready..." -ForegroundColor Gray
    if (Test-ServiceHealth -Url "http://localhost:8020/api/v1/kme/status" -MaxRetries 15) {
        $status = Invoke-RestMethod -Uri "http://localhost:8020/api/v1/kme/status" -TimeoutSec 5
        Write-Host "  [OK] KME2 Ready!" -ForegroundColor Green
        Write-Host "    - Role: $($status.role)" -ForegroundColor Cyan
        Write-Host "    - Pool Size: $($status.shared_pool.pool_size)/$($status.shared_pool.max_capacity)" -ForegroundColor Cyan
    }
    else {
        Write-Host "  [FAIL] KME2 failed to start properly" -ForegroundColor Red
        exit 1
    }
}

# Verify shared pool
Write-Host "`n  Verifying Shared Pool..." -ForegroundColor Cyan
try {
    $kme1_pool = (Invoke-RestMethod -Uri "http://localhost:8010/api/v1/kme/status" -TimeoutSec 5).shared_pool.pool_size
    $kme2_pool = (Invoke-RestMethod -Uri "http://localhost:8020/api/v1/kme/status" -TimeoutSec 5).shared_pool.pool_size
    
    if ($kme1_pool -eq $kme2_pool) {
        Write-Host "  [OK] Shared pool verified: Both report $kme1_pool keys" -ForegroundColor Green
    }
    else {
        Write-Host "  [WARN] Pool mismatch: KME1=$kme1_pool, KME2=$kme2_pool" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  [FAIL] Failed to verify shared pool" -ForegroundColor Red
}

# Step 4: Start Backend (FastAPI)
Write-Host "`n[STEP 4/5] Starting Backend (Port 8000)..." -ForegroundColor Yellow
$BACKEND_PID = Start-ServiceWindow -Title "QuMail Backend (Port 8000)" -Command ".\venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info" -WorkDir $BACKEND_DIR -Color "Blue"

if ($BACKEND_PID) {
    $PIDS["Backend"] = $BACKEND_PID
    Write-Host "  Waiting for backend to be ready..." -ForegroundColor Gray
    if (Test-ServiceHealth -Url "http://localhost:8000/health" -MaxRetries 20) {
        Write-Host "  [OK] Backend Ready!" -ForegroundColor Green
        
        # Check KME connectivity from backend
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/quantum/health" -TimeoutSec 5
            Write-Host "    - KME1 Status: $($health.kme1_status)" -ForegroundColor Cyan
            Write-Host "    - KME2 Status: $($health.kme2_status)" -ForegroundColor Cyan
        }
        catch {
            Write-Host "    [WARN] Could not get KME status from backend" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  [FAIL] Backend failed to start properly" -ForegroundColor Red
        exit 1
    }
}

# Step 5: Start Frontend (Vite)
Write-Host "`n[STEP 5/5] Starting Frontend (Port 5173)..." -ForegroundColor Yellow
$FRONTEND_PID = Start-ServiceWindow -Title "QuMail Frontend (Port 5173)" -Command "npm run dev" -WorkDir $FRONTEND_DIR -Color "Cyan"

if ($FRONTEND_PID) {
    $PIDS["Frontend"] = $FRONTEND_PID
    Write-Host "  Waiting for frontend to be ready..." -ForegroundColor Gray
    if (Test-ServiceHealth -Url "http://localhost:5173" -MaxRetries 20) {
        Write-Host "  [OK] Frontend Ready!" -ForegroundColor Green
    }
    else {
        Write-Host "  [WARN] Frontend may still be starting..." -ForegroundColor Yellow
    }
}

# Display summary
Write-Host "`n================================================================================================================" -ForegroundColor Green
Write-Host "SYSTEM READY - All Services Running" -ForegroundColor Green
Write-Host "================================================================================================================`n" -ForegroundColor Green

Write-Host "Services Running:" -ForegroundColor Cyan
Write-Host "  [1] KME1 (Master)     : http://localhost:8010 (PID: $($PIDS['KME1']))" -ForegroundColor Magenta
Write-Host "  [2] KME2 (Slave)      : http://localhost:8020 (PID: $($PIDS['KME2']))" -ForegroundColor Magenta
Write-Host "  [3] Backend (FastAPI) : http://localhost:8000 (PID: $($PIDS['Backend']))" -ForegroundColor Blue
Write-Host "  [4] Frontend (Vite)   : http://localhost:5173 (PID: $($PIDS['Frontend']))" -ForegroundColor Cyan
Write-Host ""

Write-Host "Key Endpoints:" -ForegroundColor Yellow
Write-Host "  - Frontend App        : http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API         : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Backend Health      : http://localhost:8000/health" -ForegroundColor White
Write-Host "  - KME1 Status         : http://localhost:8010/api/v1/kme/status" -ForegroundColor White
Write-Host "  - KME2 Status         : http://localhost:8020/api/v1/kme/status" -ForegroundColor White
Write-Host ""

Write-Host "Logs:" -ForegroundColor Yellow
Write-Host "  - Backend logs        : qumail-backend\qumail-backend.log" -ForegroundColor White
Write-Host "  - Watch terminals for real-time logs" -ForegroundColor White
Write-Host ""

Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host "  - Check pool status   : .\check_shared_pool.ps1" -ForegroundColor White
Write-Host "  - Test encryption     : python test_complete_real_encryption.py" -ForegroundColor White
Write-Host "  - Stop all services   : Get-Process python,node,uvicorn | Stop-Process -Force" -ForegroundColor White
Write-Host ""

Write-Host "================================================================================================================" -ForegroundColor Green
Write-Host ""

# Save PIDs to file for later cleanup
$PIDS | ConvertTo-Json | Out-File -FilePath (Join-Path $SCRIPT_DIR ".qumail_pids.json")

Write-Host "[SUCCESS] Complete system is ready for use!" -ForegroundColor Green
Write-Host "          Open http://localhost:5173 in your browser" -ForegroundColor Cyan
Write-Host ""
