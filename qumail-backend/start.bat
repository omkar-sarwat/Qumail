@echo off
REM QuMail Secure Email Backend - Windows Startup Script
REM This script sets up and starts the QuMail backend on Windows without Docker

echo ================================
echo QuMail Secure Email Backend
echo Windows Local Development Setup
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Found Python %python_version%

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Creating environment configuration...
    copy .env.example .env
    echo.
    echo ================================
    echo IMPORTANT: Configure .env file!
    echo ================================
    echo 1. Edit .env file with your settings
    echo 2. Add Google OAuth credentials
    echo 3. Verify KM server paths
    echo 4. Run this script again
    echo.
    pause
    exit /b 0
)

REM Upgrade pip
python -m pip install --upgrade pip

REM Install/upgrade requirements
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Validate configuration
echo Validating backend configuration...
python validate_backend.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Configuration validation failed
    echo Please fix the issues above before starting the backend
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Initialize database (if SQLite or if tables don't exist)
echo Initializing database...
alembic upgrade head
if %errorlevel% neq 0 (
    echo WARNING: Database migration failed. Attempting to create initial schema...
    alembic revision --autogenerate -m "Initial schema"
    alembic upgrade head
)

REM Show startup information
echo.
echo ================================
echo Starting QuMail Backend Server
echo ================================
echo Backend will be available at:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo - Health: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ================================

REM Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

REM If we get here, the server was stopped
echo.
echo Backend server stopped.
pause