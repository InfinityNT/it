@echo off
echo ============================================
echo    DMP - Device Management Platform
echo ============================================
echo.

:: Check if virtual environment exists
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if database exists
if not exist db.sqlite3 (
    echo Database not found. Running migrations...
    python manage.py migrate
)

echo Starting DMP server...
echo.
echo Access the application at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server.
echo ============================================
echo.

:: Open browser after a short delay (in background)
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start Django development server
python manage.py runserver 0.0.0.0:8000
