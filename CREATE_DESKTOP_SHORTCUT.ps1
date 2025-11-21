# Create Desktop Shortcut for QuMail

Write-Host "Creating QuMail Desktop Shortcut..." -ForegroundColor Cyan

$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = "$DesktopPath\QuMail Secure Email.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $scriptDir "LAUNCH_QUMAIL_APP.ps1"

# Set shortcut properties
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$launcherPath`""
$Shortcut.WorkingDirectory = $scriptDir
$Shortcut.Description = "QuMail Secure Email - Quantum-encrypted email client"
$Shortcut.IconLocation = "$scriptDir\qumail-frontend\release\QuMail-Portable\QuMail.exe,0"
$Shortcut.Save()

Write-Host ""
Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now launch QuMail from your desktop!" -ForegroundColor Green
Write-Host ""
Write-Host "Shortcut location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
