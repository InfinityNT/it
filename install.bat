@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    DMP - Device Management Platform
echo    Windows Installation Script
echo ============================================
echo.

:: Check for Python
echo [1/6] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.12 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Found Python %PYVER%

:: Create virtual environment
echo.
echo [2/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

:: Activate and install dependencies
echo.
echo [3/6] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.

:: Create .env file if it doesn't exist
echo.
echo [4/6] Configuring environment...
if not exist .env (
    :: Generate a random secret key
    for /f "delims=" %%a in ('python -c "import secrets; print(secrets.token_urlsafe(50))"') do set SECRET_KEY=%%a

    :: Create simplified .env file
    (
        echo # DMP Configuration
        echo DEBUG=True
        echo SECRET_KEY=!SECRET_KEY!
        echo DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo # Security - set to False for local development
        echo SECURE_SSL_REDIRECT=False
        echo SESSION_COOKIE_SECURE=False
        echo CSRF_COOKIE_SECURE=False
    ) > .env
    echo Environment file created with secure secret key.
) else (
    echo Environment file already exists, skipping...
)

:: Run migrations
echo.
echo [5/6] Setting up database...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Database migration failed.
    pause
    exit /b 1
)
echo Database setup complete.

:: Create superuser
echo.
echo [6/6] Create admin account
echo.
set /p CREATE_ADMIN="Do you want to create an admin account now? (y/n): "
if /i "%CREATE_ADMIN%"=="y" (
    python manage.py createsuperuser
)

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo To start the application:
echo   - Double-click 'start.bat'
echo   - Or run 'start.bat' from command prompt
echo.
echo The application will open in your browser at:
echo   http://localhost:8000
echo.
pause
