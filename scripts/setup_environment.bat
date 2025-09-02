@echo off
chcp 65001 >nul
echo ========================================
echo Video Downloader Environment Setup
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo ✓ Python is installed

echo.
echo [2/5] Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)
echo ✓ pip is available

echo.
echo [3/5] Upgrading pip to latest version...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo WARNING: Failed to upgrade pip, continuing...
)

echo.
echo [4/5] Installing project dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo ✓ Dependencies installed successfully

echo.
echo [5/5] Creating downloads directory...
if not exist "downloads" mkdir downloads
echo ✓ Downloads directory created

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo You can now run the video downloader:
echo   • GUI mode: python src/main_downloader.py --gui
echo   • CLI mode: python src/main_downloader.py
echo.
echo For more information, see README.md
echo.
pause