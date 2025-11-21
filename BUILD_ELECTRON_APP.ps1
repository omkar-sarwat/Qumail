# Build complete Electron application
# This script builds the frontend and packages everything into Electron app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Electron - Build Complete App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    node --version | Out-Null
    Write-Host "[OK] Node.js is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Installing Frontend Dependencies..." -ForegroundColor Cyan
Set-Location "qumail-frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Building Frontend..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "[OK] Frontend built successfully!" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Building Electron Application..." -ForegroundColor Cyan

# Determine platform
$platform = ""
if ($IsWindows -or $env:OS -like "*Windows*") {
    $platform = "win"
    Write-Host "Building for Windows..." -ForegroundColor Yellow
} elseif ($IsMacOS) {
    $platform = "mac"
    Write-Host "Building for macOS..." -ForegroundColor Yellow
} elseif ($IsLinux) {
    $platform = "linux"
    Write-Host "Building for Linux..." -ForegroundColor Yellow
}

if ($platform -eq "win") {
    npm run electron:dist:win
} elseif ($platform -eq "mac") {
    npm run electron:dist:mac
} elseif ($platform -eq "linux") {
    npm run electron:dist:linux
} else {
    npm run electron:dist
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Electron build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Electron app built successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output location: qumail-frontend\release\" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now install and run the application!" -ForegroundColor Green
Write-Host ""
