# QuMail Electron - Quick Setup
# Installs all dependencies and prepares for development

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Electron - Quick Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Cyan

try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.9-3.11" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

try {
    $nodeVersion = node --version
    Write-Host "[OK] Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

try {
    $npmVersion = npm --version
    Write-Host "[OK] npm $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] npm not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Installing Python dependencies..." -ForegroundColor Cyan

# Backend
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\qumail-backend"
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend dependency installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Backend dependencies installed" -ForegroundColor Green

# KME
Write-Host "Installing KME dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\next-door-key-simulator"
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] KME dependency installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] KME dependencies installed" -ForegroundColor Green

# PyInstaller for building
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller
Write-Host "[OK] PyInstaller installed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Installing Node.js dependencies..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\qumail-frontend"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Node.js dependency installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Node.js dependencies installed" -ForegroundColor Green

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Development Mode:" -ForegroundColor White
Write-Host "  .\START_ELECTRON_DEV.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Build Production App:" -ForegroundColor White
Write-Host "  .\BUILD_PYTHON_BUNDLES.ps1" -ForegroundColor Yellow
Write-Host "  .\BUILD_ELECTRON_APP.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation:" -ForegroundColor White
Write-Host "  See ELECTRON_APP_GUIDE.md for complete guide" -ForegroundColor Yellow
Write-Host ""
