# Video Downloader Environment Setup Script
# PowerShell version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Video Downloader Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Step 1: Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
if (Test-Command "python") {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check pip installation
Write-Host ""
Write-Host "[2/5] Checking pip installation..." -ForegroundColor Yellow
if (Test-Command "pip") {
    $pipVersion = pip --version 2>&1
    Write-Host "✓ pip is available: $pipVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR: pip is not available" -ForegroundColor Red
    Write-Host "Please ensure pip is installed with Python" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Upgrade pip
Write-Host ""
Write-Host "[3/5] Upgrading pip to latest version..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    Write-Host "✓ pip upgraded successfully" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Failed to upgrade pip, continuing..." -ForegroundColor Yellow
}

# Step 4: Install dependencies
Write-Host ""
Write-Host "[4/5] Installing project dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 5: Create downloads directory
Write-Host ""
Write-Host "[5/5] Creating downloads directory..." -ForegroundColor Yellow
if (!(Test-Path "downloads")) {
    New-Item -ItemType Directory -Path "downloads" | Out-Null
}
Write-Host "✓ Downloads directory created" -ForegroundColor Green

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run the video downloader:" -ForegroundColor White
Write-Host "  • GUI mode: python src/main_downloader.py --gui" -ForegroundColor Cyan
Write-Host "  • CLI mode: python src/main_downloader.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, see README.md" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"