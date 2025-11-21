# QuMail Secure Email - Complete Setup from GitHub
# This script sets up everything needed to run QuMail after cloning from GitHub
# Run this ONCE after cloning the repository

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipMongoDB
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Secure Email - Setup from GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will set up all dependencies and create virtual environments." -ForegroundColor Yellow
Write-Host ""

# Get script directory
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    } catch {
        return $false
    }
}

# Function to display section header
function Write-Section {
    param($Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Function to display status
function Write-Status {
    param($Message, $Status)
    if ($Status -eq "OK") {
        Write-Host "  ✅ $Message" -ForegroundColor Green
    } elseif ($Status -eq "WARN") {
        Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
    } elseif ($Status -eq "ERROR") {
        Write-Host "  ❌ $Message" -ForegroundColor Red
    } else {
        Write-Host "  ℹ️  $Message" -ForegroundColor Cyan
    }
}

# ============================================
# Step 1: Check Prerequisites
# ============================================
Write-Section "Step 1: Checking Prerequisites"

$pythonOk = $false
$nodeOk = $false
$mongoOk = $false

# Check Python
if (-not $SkipPython) {
    Write-Host "Checking Python installation..." -ForegroundColor Yellow
    if (Test-Command python) {
        $pythonVersion = python --version 2>&1
        Write-Status "Python installed: $pythonVersion" "OK"
        $pythonOk = $true
    } else {
        Write-Status "Python not found! Please install Python 3.8 or higher from https://python.org" "ERROR"
        Write-Host ""
        Write-Host "Download Python 3.11 from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

# Check Node.js
if (-not $SkipNode) {
    Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
    if (Test-Command node) {
        $nodeVersion = node --version 2>&1
        Write-Status "Node.js installed: $nodeVersion" "OK"
        
        if (Test-Command npm) {
            $npmVersion = npm --version 2>&1
            Write-Status "npm installed: v$npmVersion" "OK"
            $nodeOk = $true
        } else {
            Write-Status "npm not found!" "ERROR"
            exit 1
        }
    } else {
        Write-Status "Node.js not found! Please install Node.js 18+ from https://nodejs.org" "ERROR"
        Write-Host ""
        Write-Host "Download Node.js LTS from: https://nodejs.org/en/download/" -ForegroundColor Yellow
        exit 1
    }
}

# Check MongoDB (optional, just warn)
if (-not $SkipMongoDB) {
    Write-Host "Checking MongoDB installation..." -ForegroundColor Yellow
    if (Test-Command mongod) {
        $mongoVersion = mongod --version 2>&1 | Select-String -Pattern "db version" | Select-Object -First 1
        Write-Status "MongoDB installed: $mongoVersion" "OK"
        $mongoOk = $true
    } else {
        Write-Status "MongoDB not found (optional - will use default connection)" "WARN"
        Write-Host "  MongoDB can be installed from: https://www.mongodb.com/try/download/community" -ForegroundColor Gray
    }
}

# ============================================
# Step 2: Setup Python Virtual Environments
# ============================================
Write-Section "Step 2: Setting up Python Virtual Environments"

# Backend Virtual Environment
Write-Host "Setting up Backend virtual environment..." -ForegroundColor Yellow
Set-Location "$rootDir\qumail-backend"

if (Test-Path "venv") {
    Write-Status "Backend venv already exists, cleaning up..." "WARN"
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
}

Write-Host "  Creating virtual environment..." -ForegroundColor Gray
python -m venv venv

if (-not $?) {
    Write-Status "Failed to create backend virtual environment!" "ERROR"
    exit 1
}

Write-Status "Backend venv created" "OK"

Write-Host "  Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

Write-Host "  Upgrading pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

Write-Host "  Installing backend dependencies..." -ForegroundColor Gray
Write-Host "    This may take 3-5 minutes..." -ForegroundColor DarkGray

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    if ($?) {
        Write-Status "Backend dependencies installed successfully" "OK"
    } else {
        Write-Status "Some backend dependencies failed to install (check logs above)" "WARN"
    }
} else {
    Write-Status "requirements.txt not found!" "ERROR"
    exit 1
}

deactivate

# KME Simulator Virtual Environment
Write-Host ""
Write-Host "Setting up KME Simulator virtual environment..." -ForegroundColor Yellow
Set-Location "$rootDir\next-door-key-simulator"

if (Test-Path "venv") {
    Write-Status "KME venv already exists, cleaning up..." "WARN"
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
}

Write-Host "  Creating virtual environment..." -ForegroundColor Gray
python -m venv venv

if (-not $?) {
    Write-Status "Failed to create KME virtual environment!" "ERROR"
    exit 1
}

Write-Status "KME venv created" "OK"

Write-Host "  Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

Write-Host "  Upgrading pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

Write-Host "  Installing KME dependencies..." -ForegroundColor Gray

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    if ($?) {
        Write-Status "KME dependencies installed successfully" "OK"
    } else {
        Write-Status "Some KME dependencies failed to install (check logs above)" "WARN"
    }
} else {
    Write-Status "requirements.txt not found!" "ERROR"
    exit 1
}

deactivate

# ============================================
# Step 3: Setup Node.js Dependencies
# ============================================
Write-Section "Step 3: Setting up Node.js Dependencies"

Write-Host "Installing Frontend dependencies..." -ForegroundColor Yellow
Set-Location "$rootDir\qumail-frontend"

if (Test-Path "node_modules") {
    Write-Status "node_modules exists, cleaning up..." "WARN"
    Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
}

if (Test-Path "package-lock.json") {
    Write-Status "Found package-lock.json (using exact versions)" "OK"
} else {
    Write-Status "No package-lock.json (will install latest compatible versions)" "WARN"
}

Write-Host "  Installing npm packages..." -ForegroundColor Gray
Write-Host "    This may take 5-10 minutes..." -ForegroundColor DarkGray

npm install

if ($?) {
    Write-Status "Frontend dependencies installed successfully" "OK"
} else {
    Write-Status "Some frontend dependencies failed to install (check logs above)" "WARN"
}

# ============================================
# Step 4: Setup Configuration Files
# ============================================
Write-Section "Step 4: Setting up Configuration Files"

Set-Location $rootDir

# Backend .env file
Write-Host "Checking backend configuration..." -ForegroundColor Yellow
$backendEnvPath = "$rootDir\qumail-backend\.env"

if (Test-Path $backendEnvPath) {
    Write-Status "Backend .env file found (keeping existing configuration)" "OK"
} else {
    Write-Status "Backend .env file not found - please ensure it exists with your credentials" "WARN"
}

# Frontend .env file
Write-Host ""
Write-Host "Checking frontend configuration..." -ForegroundColor Yellow
$frontendEnvPath = "$rootDir\qumail-frontend\.env"

if (Test-Path $frontendEnvPath) {
    Write-Status "Frontend .env file found (keeping existing configuration)" "OK"
} else {
    Write-Status "Frontend .env file not found - please ensure it exists with your credentials" "WARN"
}

# ============================================
# Step 5: Setup Database (Optional)
# ============================================
Write-Section "Step 5: Database Setup"

if ($mongoOk) {
    Write-Host "MongoDB is installed. Do you want to initialize the database? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host "Press Y to initialize, or any other key to skip"
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "  Starting MongoDB service..." -ForegroundColor Gray
        
        # Try to start MongoDB service if it exists
        $mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
        if ($mongoService) {
            if ($mongoService.Status -ne "Running") {
                Start-Service MongoDB
                Write-Status "MongoDB service started" "OK"
            } else {
                Write-Status "MongoDB service already running" "OK"
            }
        } else {
            Write-Status "MongoDB service not found (may need manual start)" "WARN"
        }
        
        # Initialize database schema (if script exists)
        $dbScriptPath = "$rootDir\database\qumail_mysql_setup.sql"
        if (Test-Path $dbScriptPath) {
            Write-Status "Database schema script found (manual import may be needed)" "WARN"
        }
    } else {
        Write-Status "Database initialization skipped" "WARN"
    }
} else {
    Write-Status "MongoDB not detected - database will need manual setup" "WARN"
    Write-Host "  MongoDB can be downloaded from: https://www.mongodb.com/try/download/community" -ForegroundColor Gray
}

# ============================================
# Step 6: Verify Installation
# ============================================
Write-Section "Step 6: Verifying Installation"

$allGood = $true

# Check Backend venv
if (Test-Path "$rootDir\qumail-backend\venv\Scripts\python.exe") {
    Write-Status "Backend virtual environment: OK" "OK"
} else {
    Write-Status "Backend virtual environment: FAILED" "ERROR"
    $allGood = $false
}

# Check KME venv
if (Test-Path "$rootDir\next-door-key-simulator\venv\Scripts\python.exe") {
    Write-Status "KME virtual environment: OK" "OK"
} else {
    Write-Status "KME virtual environment: FAILED" "ERROR"
    $allGood = $false
}

# Check Frontend node_modules
if (Test-Path "$rootDir\qumail-frontend\node_modules") {
    Write-Status "Frontend dependencies: OK" "OK"
} else {
    Write-Status "Frontend dependencies: FAILED" "ERROR"
    $allGood = $false
}

# Check config files
if (Test-Path "$rootDir\qumail-backend\.env") {
    Write-Status "Backend configuration: OK (using your existing credentials)" "OK"
} else {
    Write-Status "Backend configuration: MISSING (please add your .env file)" "WARN"
}

if (Test-Path "$rootDir\qumail-frontend\.env") {
    Write-Status "Frontend configuration: OK (using your existing credentials)" "OK"
} else {
    Write-Status "Frontend configuration: MISSING (please add your .env file)" "WARN"
}

# ============================================
# Final Summary
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✅ Setup Completed Successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Setup Completed with Warnings" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next Steps" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Ensure MongoDB is running:" -ForegroundColor Cyan
    Write-Host "   - Start MongoDB service or run: mongod" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Build the Electron app (optional):" -ForegroundColor Cyan
    Write-Host "   - Run: .\PACKAGE_ELECTRON_MANUALLY.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Start the application:" -ForegroundColor Cyan
    Write-Host "   - Run: .\LAUNCH_QUMAIL_APP.ps1" -ForegroundColor White
    Write-Host "   - Or use the desktop shortcut" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Setup completed but some components failed." -ForegroundColor Yellow
    Write-Host "Please review the errors above and fix them before running the app." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "  • APPLICATION_READY.md - How to run the app" -ForegroundColor White
Write-Host "  • PORTABLE_APP_README.md - App features and usage" -ForegroundColor White
Write-Host "  • INSTALLATION_AND_STARTUP.md - Detailed setup guide" -ForegroundColor White
Write-Host ""

Set-Location $rootDir

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
