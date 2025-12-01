@echo off
echo Starting QuMail Electron Desktop App...
echo.

REM Step 1: Compile TypeScript
echo [1/3] Compiling TypeScript files...
call npx tsc electron/main.ts electron/preload.ts --outDir dist-electron --module commonjs --esModuleInterop --resolveJsonModule --skipLibCheck --noEmit false
if errorlevel 1 (
    echo ERROR: TypeScript compilation failed!
    pause
    exit /b 1
)
echo TypeScript compilation successful!
echo.

REM Step 2: Start Vite dev server in background
echo [2/3] Starting Vite dev server...
start /B cmd /c "npm run dev"

REM Wait for Vite to start (give it 5 seconds)
echo Waiting for Vite dev server to start...
timeout /t 5 /nobreak > nul

REM Step 3: Start Electron
echo [3/3] Starting Electron app...
set IS_DEV=true
set NODE_ENV=development
set VITE_DEV_SERVER_URL=http://localhost:5173
npx electron dist-electron/main.js --dev

echo.
echo Electron app closed.
pause
