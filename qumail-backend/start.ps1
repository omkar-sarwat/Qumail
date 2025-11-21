# QuMail Secure Email Backend - PowerShell Startup Script
# This script sets up and starts the QuMail backend on Windows without Docker

Write-Host "================================" -ForegroundColor Cyan
Write-Host "QuMail Secure Email Backend" -ForegroundColor Cyan
Write-Host "Windows Local Development Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating environment configuration..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host "IMPORTANT: Configure .env file!" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host "1. Edit .env file with your settings" -ForegroundColor Yellow
    Write-Host "2. Add Google OAuth credentials" -ForegroundColor Yellow
    Write-Host "3. Verify KM server paths" -ForegroundColor Yellow
    Write-Host "4. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install/upgrade requirements
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Validate configuration
Write-Host "Validating backend configuration..." -ForegroundColor Yellow
python validate_backend.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Configuration validation failed" -ForegroundColor Red
    Write-Host "Please fix the issues above before starting the backend" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Database migration failed. Attempting to create initial schema..." -ForegroundColor Yellow
    alembic revision --autogenerate -m "Initial schema"
    alembic upgrade head
}

# Show startup information
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Starting QuMail Backend Server" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Backend will be available at:" -ForegroundColor White
Write-Host "- API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Green

# Start the FastAPI server
try {
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
} catch {
    Write-Host "Server startup failed: $_" -ForegroundColor Red
}

# If we get here, the server was stopped
Write-Host ""
Write-Host "Backend server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"