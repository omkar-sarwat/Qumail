<#
.SYNOPSIS
Installs dependencies for QuMail projects (backend, qumail-kms, next-door-key-simulator, frontend).

.DESCRIPTION
This script locates the Python requirements files for the backend, KMS, and the next-door
key simulator and installs them using the available Python interpreter. It also runs
`npm install` inside the `qumail-frontend` folder to install Node dependencies.

By default this performs system/global installs. Use `-UseVenv` to create a per-project
virtual environment (`.venv`) for each Python project and install into that venv instead.

Examples:
    .\install_all_requirements.ps1
    .\install_all_requirements.ps1 -UseVenv
#>

param(
    [switch]$UseVenv
)

Set-StrictMode -Version Latest

function Write-Info($msg){ Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Warn($msg){ Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Test-CommandExists($exe){
    return $null -ne (Get-Command $exe -ErrorAction SilentlyContinue)
}

$root = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $root

Write-Info "Repository root: $root"

# Detect Python
$pyCmd = $null
if (Test-CommandExists python) { $pyCmd = 'python' }
elseif (Test-CommandExists python3) { $pyCmd = 'python3' }

if (-not $pyCmd) {
    Write-Err "Python executable not found. Please install Python 3.8+ and make sure 'python' is on PATH."
    exit 2
}

Write-Info "Using Python: $pyCmd"

$projects = @(
    @{ Name = 'Backend'; Path = 'qumail-backend'; Req = 'qumail-backend\requirements.txt' },
    @{ Name = 'QuMail-KMS'; Path = 'qumail-kms'; Req = 'qumail-kms\requirements.txt' },
    @{ Name = 'NextDoorKeySimulator'; Path = 'next-door-key-simulator'; Req = 'next-door-key-simulator\requirements.txt' }
)

$installResults = @()

foreach ($p in $projects) {
    $projName = $p.Name
    $projPath = Join-Path $root $p.Path
    $reqPath = Join-Path $root $p.Req

    if (-not (Test-Path $projPath)) {
        Write-Warn "Project folder not found: $projPath - skipping $projName"
        $installResults += @{project=$projName; status='skipped'; reason='missing folder'}
        continue
    }

    if (-not (Test-Path $reqPath)) {
        Write-Warn "Requirements file not found for $projName`: $reqPath - skipping"
        $installResults += @{project=$projName; status='skipped'; reason='missing requirements.txt'}
        continue
    }

    Write-Info "Installing requirements for $projName from $reqPath"

    if ($UseVenv) {
        $venvDir = Join-Path $projPath '.venv'
        if (-not (Test-Path $venvDir)) {
            Write-Info "Creating virtual environment for $projName at $venvDir"
            & $pyCmd -m venv $venvDir
            if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create venv for $projName"; $installResults += @{project=$projName; status='failed'; reason='venv creation'}; continue }
        }

        $pipExe = Join-Path $venvDir 'Scripts\python.exe'
        if (-not (Test-Path $pipExe)) { Write-Err "Virtualenv python not found: $pipExe"; $installResults += @{project=$projName; status='failed'; reason='venv missing python'}; continue }

        Write-Info "Upgrading pip inside venv for $projName"
        & $pipExe -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) { Write-Warn "pip upgrade failed in venv for $projName" }

        Write-Info "Installing from requirements into venv..."
        & $pipExe -m pip install -r $reqPath
        $code = $LASTEXITCODE
    }
    else {
        Write-Info "Installing using system python: $pyCmd -m pip install -r $reqPath --upgrade"
        & $pyCmd -m pip install --upgrade -r $reqPath
        $code = $LASTEXITCODE
    }

    if ($code -eq 0) {
        Write-Info "Installed requirements for $projName"
        $installResults += @{project=$projName; status='ok'}
    } else {
        Write-Err "Failed to install requirements for $projName (exit $code)"
        $installResults += @{project=$projName; status='failed'; code=$code}
    }
}

# Frontend (Node)
$frontendPath = Join-Path $root 'qumail-frontend'
if (Test-Path $frontendPath) {
    Write-Info "Installing frontend node modules in $frontendPath"
    if (-not (Test-CommandExists npm)) {
        Write-Warn "npm not found on PATH. Skipping frontend install. Install Node.js/npm and re-run."
        $installResults += @{project='Frontend'; status='skipped'; reason='npm missing'}
    }
    else {
        Push-Location $frontendPath
        # prefer npm ci if lockfile exists
        if (Test-Path (Join-Path $frontendPath 'package-lock.json')) {
            Write-Info "Found package-lock.json - running 'npm ci'"
            npm ci
            $code = $LASTEXITCODE
        } else {
            Write-Info "Running 'npm install'"
            npm install
            $code = $LASTEXITCODE
        }
        Pop-Location

        if ($code -eq 0) {
            Write-Info "Frontend dependencies installed"
            $installResults += @{project='Frontend'; status='ok'}
        } else {
            Write-Err "Frontend install failed (exit $code)"
            $installResults += @{project='Frontend'; status='failed'; code=$code}
        }
    }
}
else {
    Write-Warn "Frontend folder not found at $frontendPath - skipping frontend"
    $installResults += @{project='Frontend'; status='skipped'; reason='missing folder'}
}

Write-Host "`n=== Install Summary ===" -ForegroundColor Green
foreach ($r in $installResults) {
    $status = $r['status']
    if ($status -eq 'ok') { Write-Host " - $($r['project'])``: OK" -ForegroundColor Green }
    elseif ($status -eq 'skipped') { Write-Host " - $($r['project'])``: SKIPPED ($($r['reason']))" -ForegroundColor Yellow }
    else { Write-Host " - $($r['project'])``: FAILED ($($r['reason']) $($r['code']))" -ForegroundColor Red }
}

Write-Info "Done."
