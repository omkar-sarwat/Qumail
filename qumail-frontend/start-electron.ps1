# QuMail Electron Desktop App Launcher
# This script starts the Vite dev server and Electron app

Write-Host "🚀 Starting QuMail Electron Desktop App..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Compile TypeScript
Write-Host "[1/3] Compiling TypeScript files..." -ForegroundColor Yellow
try {
    npx tsc electron/main.ts electron/preload.ts --outDir dist-electron --module commonjs --esModuleInterop --resolveJsonModule --skipLibCheck --noEmit false
    if ($LASTEXITCODE -ne 0) {
        throw "TypeScript compilation failed"
    }
    Write-Host "✅ TypeScript compilation successful!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ ERROR: TypeScript compilation failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 2: Check if Vite is already running
Write-Host "[2/3] Checking Vite dev server..." -ForegroundColor Yellow
$viteRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
    $viteRunning = $true
    Write-Host "✅ Vite dev server is already running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Vite dev server not running, starting it..." -ForegroundColor Yellow
    
    # Start Vite in a new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
    
    # Wait for Vite to start
    Write-Host "Waiting for Vite dev server to start..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 1 -ErrorAction SilentlyContinue
            $viteRunning = $true
            Write-Host "✅ Vite dev server started successfully!" -ForegroundColor Green
            break
        } catch {
            $attempt++
            Write-Host "." -NoNewline
        }
    }
    
    if (-not $viteRunning) {
        Write-Host ""
        Write-Host "❌ ERROR: Vite dev server failed to start!" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 3: Start Electron
Write-Host "[3/3] Starting Electron app..." -ForegroundColor Yellow
$env:IS_DEV = "true"
$env:NODE_ENV = "development"
$env:VITE_DEV_SERVER_URL = "http://localhost:5173"

try {
    npx electron dist-electron/main.js --dev
    Write-Host ""
    Write-Host "✅ Electron app closed." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: Electron app failed to start!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
