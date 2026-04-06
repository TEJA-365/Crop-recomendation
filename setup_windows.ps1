# Setup script for Windows PowerShell
# This script automates the initial setup of the Crop Recommendation System

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Crop Recommendation System - Windows Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10 or higher from python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check if pip is installed
try {
    $pipVersion = pip --version 2>&1
    Write-Host "[OK] pip found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] pip is not installed. Please install pip first." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "[WARNING] Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to activate virtual environment." -ForegroundColor Red
    Write-Host "[INFO] If you get an execution policy error, run:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Failed to upgrade pip, but continuing..." -ForegroundColor Yellow
} else {
    Write-Host "[OK] pip upgraded" -ForegroundColor Green
}
Write-Host ""

# Install dependencies
Write-Host "[INFO] Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies. Please check the error messages above." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Run migrations
Write-Host "[INFO] Setting up database..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Database setup failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Database setup complete" -ForegroundColor Green
Write-Host ""

# Collect static files
Write-Host "[INFO] Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Static files collection had issues, but continuing..." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Static files collected" -ForegroundColor Green
}
Write-Host ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "[OK] Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Activate the virtual environment: venv\Scripts\Activate.ps1"
Write-Host "2. Create a superuser: python manage.py createsuperuser"
Write-Host "3. Run the server: python manage.py runserver"
Write-Host "4. Open http://127.0.0.1:8000/ in your browser"
Write-Host ""
Write-Host "For more information, see QUICK_START.md" -ForegroundColor Cyan
Write-Host ""

