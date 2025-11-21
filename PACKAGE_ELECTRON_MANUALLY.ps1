# Manual Electron Packaging Script
# Packages the Electron app without electron-builder to avoid signing issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail - Manual Electron Packaging" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Step 1: Build the frontend
Write-Host "Step 1: Building Frontend..." -ForegroundColor Cyan
Set-Location "qumail-frontend"

Write-Host "Running TypeScript compilation..." -ForegroundColor Yellow
npx tsc --noEmit false

Write-Host "Running Vite build..." -ForegroundColor Yellow
npx vite build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Step 2: Compile Electron files
Write-Host ""
Write-Host "Step 2: Compiling Electron files..." -ForegroundColor Cyan
npx tsc electron/main.ts electron/preload.ts --outDir dist-electron --module commonjs --esModuleInterop --resolveJsonModule --skipLibCheck --noEmit false

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Electron compilation failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Step 3: Create release directory
Write-Host ""
Write-Host "Step 3: Creating portable package..." -ForegroundColor Cyan

$releaseDir = "release\QuMail-Portable"
if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

# Step 4: Download Electron if needed
Write-Host ""
Write-Host "Step 4: Preparing Electron runtime..." -ForegroundColor Cyan

$electronVersion = "27.3.11"
$electronCachePath = "$env:LOCALAPPDATA\electron\Cache\electron-v$electronVersion-win32-x64.zip"
$electronExtractPath = "$env:TEMP\electron-v$electronVersion-win32-x64"

if (-not (Test-Path $electronCachePath)) {
    Write-Host "Downloading Electron $electronVersion..." -ForegroundColor Yellow
    $electronUrl = "https://github.com/electron/electron/releases/download/v$electronVersion/electron-v$electronVersion-win32-x64.zip"
    $cacheDirelectron = Split-Path $electronCachePath
    if (-not (Test-Path $cacheDir)) {
        New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
    }
    Invoke-WebRequest -Uri $electronUrl -OutFile $electronCachePath
}

# Step 5: Extract Electron
if (-not (Test-Path $electronExtractPath)) {
    Write-Host "Extracting Electron..." -ForegroundColor Yellow
    Expand-Archive -Path $electronCachePath -DestinationPath $electronExtractPath -Force
}

# Step 6: Copy Electron files
Write-Host "Copying Electron runtime..." -ForegroundColor Yellow
Copy-Item -Path "$electronExtractPath\*" -Destination $releaseDir -Recurse -Force

# Step 7: Create app.asar structure
Write-Host ""
Write-Host "Step 5: Packaging application..." -ForegroundColor Cyan

$appDir = "$releaseDir\resources\app"
New-Item -ItemType Directory -Path $appDir -Force | Out-Null

# Copy package.json
Copy-Item -Path "package.json" -Destination $appDir -Force

# Copy dist folder (frontend build)
Write-Host "Copying frontend build..." -ForegroundColor Yellow
Copy-Item -Path "dist" -Destination "$appDir\dist" -Recurse -Force

# Copy dist-electron folder (electron main/preload)
Write-Host "Copying Electron files..." -ForegroundColor Yellow
Copy-Item -Path "dist-electron" -Destination "$appDir\dist-electron" -Recurse -Force

# Copy node_modules (only production dependencies)
Write-Host "Copying dependencies..." -ForegroundColor Yellow
$nodeModulesSource = "node_modules"
$nodeModulesDest = "$appDir\node_modules"

# Only copy essential electron dependencies
$essentialModules = @("electron")
foreach ($module in $essentialModules) {
    $modulePath = "$nodeModulesSource\$module"
    if (Test-Path $modulePath) {
        $destPath = "$nodeModulesDest\$module"
        Copy-Item -Path $modulePath -Destination $destPath -Recurse -Force
    }
}

# Step 8: Rename electron.exe to QuMail.exe
Write-Host ""
Write-Host "Step 6: Finalizing..." -ForegroundColor Cyan
if (Test-Path "$releaseDir\electron.exe") {
    Rename-Item -Path "$releaseDir\electron.exe" -NewName "QuMail.exe" -Force
}

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Packaging Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Location: qumail-frontend\$releaseDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the app:" -ForegroundColor Yellow
Write-Host "  cd qumail-frontend\$releaseDir" -ForegroundColor White
Write-Host "  .\QuMail.exe" -ForegroundColor White
Write-Host ""
Write-Host "Note: This is a portable version. The backend and KME servers" -ForegroundColor Gray
Write-Host "need to be started separately before running the app." -ForegroundColor Gray
Write-Host ""
