# Quick Deploy Script for Next Door Key Simulator to Render.com
# This script helps you prepare and deploy the KME servers

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Next Door Key Simulator - Render.com Deployment Helper" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if we're in the right directory
$expectedPath = "next-door-key-simulator"
$currentPath = Get-Location
if ($currentPath.Path -notlike "*$expectedPath*") {
    Write-Host "[!] Please run this script from the next-door-key-simulator directory" -ForegroundColor Red
    Write-Host "    Current: $currentPath" -ForegroundColor Yellow
    Write-Host "    Expected: *\next-door-key-simulator" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/6] Checking Prerequisites..." -ForegroundColor Green
Write-Host ""

# Check Git
try {
    $gitVersion = git --version
    Write-Host "  ✓ Git installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Git not found. Please install Git first." -ForegroundColor Red
    Write-Host "    Download: https://git-scm.com/downloads" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if this is a git repository
$isGitRepo = Test-Path ".git"
if (-not $isGitRepo) {
    Write-Host "  ! Not a Git repository" -ForegroundColor Yellow
    $initGit = Read-Host "  Do you want to initialize Git here? (y/n)"
    if ($initGit -eq "y") {
        git init
        Write-Host "  ✓ Git repository initialized" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[2/6] Checking Required Files..." -ForegroundColor Green
Write-Host ""

$requiredFiles = @(
    "Dockerfile",
    "app.py",
    "requirements.txt",
    "render-kme1.yaml",
    "render-kme2.yaml",
    "RENDER_DEPLOYMENT_GUIDE.md"
)

$allFilesPresent = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (MISSING)" -ForegroundColor Red
        $allFilesPresent = $false
    }
}

if (-not $allFilesPresent) {
    Write-Host ""
    Write-Host "  Some required files are missing. Please check the directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/6] GitHub Repository Setup" -ForegroundColor Green
Write-Host ""
Write-Host "  You need to push this code to GitHub for Render to deploy it." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Option 1: Use existing GitHub repository" -ForegroundColor Cyan
Write-Host "    - Go to your GitHub repo" -ForegroundColor Gray
Write-Host "    - Ensure this code is pushed" -ForegroundColor Gray
Write-Host ""
Write-Host "  Option 2: Create new GitHub repository" -ForegroundColor Cyan
Write-Host "    - Go to: https://github.com/new" -ForegroundColor Gray
Write-Host "    - Repository name: next-door-key-simulator" -ForegroundColor Gray
Write-Host "    - Set as Public or Private" -ForegroundColor Gray
Write-Host "    - Don't initialize with README (we already have files)" -ForegroundColor Gray
Write-Host ""

$hasGitHub = Read-Host "  Is your code already on GitHub? (y/n)"

if ($hasGitHub -ne "y") {
    Write-Host ""
    Write-Host "  Please follow these steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Create a new repository on GitHub" -ForegroundColor White
    Write-Host "  2. Copy the repository URL (e.g., https://github.com/username/next-door-key-simulator.git)" -ForegroundColor White
    Write-Host ""
    $repoUrl = Read-Host "  Enter your GitHub repository URL"
    
    if ($repoUrl) {
        try {
            git remote remove origin 2>$null
            git remote add origin $repoUrl
            git add .
            git commit -m "Prepare Next Door Key Simulator for Render deployment"
            git push -u origin master
            Write-Host ""
            Write-Host "  ✓ Code pushed to GitHub!" -ForegroundColor Green
        } catch {
            Write-Host ""
            Write-Host "  ! Error pushing to GitHub: $_" -ForegroundColor Yellow
            Write-Host "  Please push manually using:" -ForegroundColor Yellow
            Write-Host "    git remote add origin $repoUrl" -ForegroundColor Gray
            Write-Host "    git add ." -ForegroundColor Gray
            Write-Host "    git commit -m 'Deploy to Render'" -ForegroundColor Gray
            Write-Host "    git push -u origin master" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "[4/6] Render.com Account Setup" -ForegroundColor Green
Write-Host ""
Write-Host "  1. Go to: https://dashboard.render.com/register" -ForegroundColor White
Write-Host "  2. Sign up with your GitHub account (recommended)" -ForegroundColor White
Write-Host "  3. Authorize Render to access your GitHub repositories" -ForegroundColor White
Write-Host ""
$hasRenderAccount = Read-Host "  Do you have a Render.com account? (y/n)"

if ($hasRenderAccount -ne "y") {
    Write-Host ""
    Write-Host "  Please create a Render.com account and press Enter when ready..." -ForegroundColor Yellow
    Read-Host
}

Write-Host ""
Write-Host "[5/6] Deploy KME Services to Render" -ForegroundColor Green
Write-Host ""
Write-Host "  You'll deploy TWO web services:" -ForegroundColor Yellow
Write-Host "    1. qumail-kme-sender (KME 1)" -ForegroundColor Cyan
Write-Host "    2. qumail-kme-receiver (KME 2)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  For each service:" -ForegroundColor White
Write-Host "    • Name: qumail-kme-sender (or receiver)" -ForegroundColor Gray
Write-Host "    • Runtime: Docker" -ForegroundColor Gray
Write-Host "    • Plan: Free" -ForegroundColor Gray
Write-Host "    • Health Check: /api/v1/kme/status" -ForegroundColor Gray
Write-Host ""
Write-Host "  See RENDER_DEPLOYMENT_GUIDE.md for detailed environment variables." -ForegroundColor White
Write-Host ""
Write-Host "  Opening deployment guide..." -ForegroundColor Cyan
Start-Process "RENDER_DEPLOYMENT_GUIDE.md"
Write-Host ""
Write-Host "  Press Enter when both KME services are deployed on Render..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "[6/6] Update Backend Configuration" -ForegroundColor Green
Write-Host ""
Write-Host "  Enter the Render URLs for your deployed KME services:" -ForegroundColor White
Write-Host ""
$kme1Url = Read-Host "  KME 1 (Sender) URL (e.g., https://qumail-kme-sender.onrender.com)"
$kme2Url = Read-Host "  KME 2 (Receiver) URL (e.g., https://qumail-kme-receiver.onrender.com)"

if ($kme1Url -and $kme2Url) {
    Write-Host ""
    Write-Host "  Updating backend .env file..." -ForegroundColor Cyan
    
    $backendEnvPath = "..\qumail-backend\.env"
    if (Test-Path $backendEnvPath) {
        # Update .env file
        $envContent = Get-Content $backendEnvPath
        $envContent = $envContent -replace "KM1_BASE_URL=.*", "KM1_BASE_URL=$kme1Url"
        $envContent = $envContent -replace "KM2_BASE_URL=.*", "KM2_BASE_URL=$kme2Url"
        $envContent | Set-Content $backendEnvPath
        
        Write-Host "  ✓ Backend .env updated!" -ForegroundColor Green
        Write-Host "    KM1_BASE_URL=$kme1Url" -ForegroundColor Gray
        Write-Host "    KM2_BASE_URL=$kme2Url" -ForegroundColor Gray
    } else {
        Write-Host "  ! Backend .env not found at: $backendEnvPath" -ForegroundColor Yellow
        Write-Host "  Please manually update your backend .env with:" -ForegroundColor Yellow
        Write-Host "    KM1_BASE_URL=$kme1Url" -ForegroundColor Gray
        Write-Host "    KM2_BASE_URL=$kme2Url" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  ✓ Deployment Setup Complete!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test KME connectivity:" -ForegroundColor White
Write-Host "   cd ..\qumail-backend" -ForegroundColor Gray
Write-Host "   python test_cloud_kme.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start your backend server:" -ForegroundColor White
Write-Host "   cd ..\qumail-backend" -ForegroundColor Gray
Write-Host "   python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test full encryption flow:" -ForegroundColor White
Write-Host "   Send an encrypted email through QuMail" -ForegroundColor Gray
Write-Host ""
Write-Host "Important Notes:" -ForegroundColor Yellow
Write-Host "  • Free tier services sleep after 15 min of inactivity" -ForegroundColor Gray
Write-Host "  • First request after sleep takes 30-60 seconds" -ForegroundColor Gray
Write-Host "  • Consider upgrading to Starter plan ($7/month) for production" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed instructions, see: RENDER_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
