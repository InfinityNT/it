@echo off
echo Stopping DMP server...

:: Find and kill Python processes running Django
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo DMP server stopped.
timeout /t 2 /nobreak >nul
