# AuraLyrics Setup Script (Windows PowerShell)
# Creates virtual environment, installs dependencies, and sets up directories.

Write-Host ""
Write-Host "  AuraLyrics Setup" -ForegroundColor Cyan
Write-Host "  ================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
Set-Location $projectRoot

# 1. Create virtual environment
if (-Not (Test-Path "venv")) {
    Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[1/5] Virtual environment already exists" -ForegroundColor Green
}

# 2. Activate and install dependencies
Write-Host "[2/5] Installing Python dependencies..." -ForegroundColor Yellow
& "$projectRoot\venv\Scripts\pip.exe" install -r requirements.txt --quiet

# 3. Create directories
Write-Host "[3/5] Creating directory structure..." -ForegroundColor Yellow
$dirs = @("data", "raw_assets", "metadata", "renders", "logs", "backgrounds", "fonts")
foreach ($dir in $dirs) {
    $path = Join-Path $projectRoot $dir
    if (-Not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  Created: $dir/" -ForegroundColor Gray
    }
}

# 4. Initialize empty files
Write-Host "[4/5] Initializing data files..." -ForegroundColor Yellow
$hitsPath = Join-Path $projectRoot "data\hits.json"
if (-Not (Test-Path $hitsPath)) {
    "[]" | Out-File -FilePath $hitsPath -Encoding utf8
    Write-Host "  Created: data/hits.json" -ForegroundColor Gray
}

$healthPath = Join-Path $projectRoot "logs\system_health.json"
if (-Not (Test-Path $healthPath)) {
    "[]" | Out-File -FilePath $healthPath -Encoding utf8
}

$uploadPath = Join-Path $projectRoot "logs\upload_history.json"
if (-Not (Test-Path $uploadPath)) {
    "[]" | Out-File -FilePath $uploadPath -Encoding utf8
}

# 5. Check for ffmpeg
Write-Host "[5/5] Checking ffmpeg..." -ForegroundColor Yellow
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    Write-Host "  ffmpeg found: $($ffmpeg.Source)" -ForegroundColor Green
} else {
    Write-Host "  ffmpeg NOT found!" -ForegroundColor Red
    Write-Host "  Install it with: winget install Gyan.FFmpeg" -ForegroundColor Yellow
    Write-Host "  Or download from: https://ffmpeg.org/download.html" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "  To activate: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  To run:      python main.py --agent scraper --limit 5" -ForegroundColor Cyan
Write-Host ""
