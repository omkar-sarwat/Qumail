#!/usr/bin/env pwsh
# Check ports and diagnose startup issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuMail Port Diagnostic Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if ports are in use
Write-Host "Checking required ports..." -ForegroundColor Yellow
Write-Host ""

$ports = @(8010, 8020, 8000, 5173)
$portNames = @{
    8010 = "KME1 Server"
    8020 = "KME2 Server"
    8000 = "Backend API"
    5173 = "Vite Dev Server"
}

foreach ($port in $ports) {
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    
    if ($connections) {
        $pid = ($connections -split '\s+')[-1]
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "Port $port ($($portNames[$port])): " -NoNewline -ForegroundColor Yellow
            Write-Host "IN USE by $($process.ProcessName) (PID: $pid)" -ForegroundColor Red
        } else {
            Write-Host "Port $port ($($portNames[$port])): " -NoNewline -ForegroundColor Yellow
            Write-Host "IN USE (PID: $pid)" -ForegroundColor Red
        }
    } else {
        Write-Host "Port $port ($($portNames[$port])): " -NoNewline -ForegroundColor Yellow
        Write-Host "AVAILABLE" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Process Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python processes
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" }
if ($pythonProcesses) {
    Write-Host "Python processes found:" -ForegroundColor Yellow
    $pythonProcesses | Select-Object Id, ProcessName, StartTime | Format-Table
} else {
    Write-Host "No Python processes running" -ForegroundColor Green
}

# Check for Node processes
$nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*node*" }
if ($nodeProcesses) {
    Write-Host "Node.js processes found:" -ForegroundColor Yellow
    $nodeProcesses | Select-Object Id, ProcessName, StartTime | Format-Table
} else {
    Write-Host "No Node.js processes running" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recommendations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$hasIssues = $false

# Check port conflicts
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    if ($connections) {
        $pid = ($connections -split '\s+')[-1]
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        
        if ($process -and $process.ProcessName -notlike "*python*" -and $process.ProcessName -notlike "*node*") {
            Write-Host "⚠️  Port $port is being used by $($process.ProcessName)" -ForegroundColor Red
            Write-Host "   Run: Stop-Process -Id $pid -Force" -ForegroundColor Yellow
            $hasIssues = $true
        }
    }
}

if (-not $hasIssues) {
    Write-Host "✅ No port conflicts detected!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run: .\START_TERMINALS.ps1" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "After fixing port conflicts, run: .\START_TERMINALS.ps1" -ForegroundColor Cyan
}

Write-Host ""
