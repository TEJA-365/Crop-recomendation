@echo off
REM Setup script for Windows
REM This script automates the initial setup of the Crop Recommendation System

echo =========================================
echo Crop Recommendation System - Windows Setup
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [WARNING] Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, but continuing...
)
echo [OK] pip upgraded
echo.

REM Install dependencies
echo [INFO] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Please check the error messages above.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully
echo.

REM Run migrations
echo [INFO] Setting up database...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Database setup failed. Please check the error messages above.
    pause
    exit /b 1
)
echo [OK] Database setup complete
echo.

REM Collect static files
echo [INFO] Collecting static files...
python manage.py collectstatic --noinput
if errorlevel 1 (
    echo [WARNING] Static files collection had issues, but continuing...
) else (
    echo [OK] Static files collected
)
echo.

echo =========================================
echo [OK] Setup Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Create a superuser: python manage.py createsuperuser
echo 3. Run the server: python manage.py runserver
echo 4. Open http://127.0.0.1:8000/ in your browser
echo.
echo For more information, see QUICK_START.md
echo.
pause

