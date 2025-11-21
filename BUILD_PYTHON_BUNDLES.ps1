# Build Python executables for Electron app
# This script creates standalone executables for the backend and KME servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Electron - Build Python Bundles" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
try {
    python -m PyInstaller --version | Out-Null
    Write-Host "[OK] PyInstaller is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] PyInstaller not found. Installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

Write-Host ""
Write-Host "Step 1: Building Backend Executable..." -ForegroundColor Cyan
Set-Location "qumail-backend"

if (Test-Path "dist") {
    Write-Host "Cleaning old build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
}

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller qumail-backend.spec --clean

if (Test-Path "dist\qumail-backend") {
    Write-Host "[OK] Backend executable created successfully!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "Step 2: Building KME Server Executable..." -ForegroundColor Cyan
Set-Location "next-door-key-simulator"

if (Test-Path "dist") {
    Write-Host "Cleaning old build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
}

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller kme-server.spec --clean

if (Test-Path "dist\kme-server") {
    Write-Host "[OK] KME executable created successfully!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] KME build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "Step 3: Creating Python Bundle for Electron..." -ForegroundColor Cyan
$pythonBundleDir = "qumail-frontend\resources\python"

if (Test-Path $pythonBundleDir) {
    Remove-Item -Recurse -Force $pythonBundleDir
}

New-Item -ItemType Directory -Force -Path $pythonBundleDir | Out-Null

# Copy executables
Write-Host "Copying backend executable..." -ForegroundColor Yellow
Copy-Item -Recurse "qumail-backend\dist\qumail-backend\*" "$pythonBundleDir\backend\"

Write-Host "Copying KME executable..." -ForegroundColor Yellow
Copy-Item -Recurse "next-door-key-simulator\dist\kme-server\*" "$pythonBundleDir\kme\"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Python bundles built successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. cd qumail-frontend" -ForegroundColor White
Write-Host "2. npm run electron:build" -ForegroundColor White
Write-Host ""
