@echo off
echo Starting Sea Level Dashboard Backend with GovMap support...
echo.

REM Check domain configuration
findstr "sea-level-dash-local" C:\Windows\System32\drivers\etc\hosts >nul
if %errorLevel% neq 0 (
    echo ERROR: Domain not configured!
    echo Please run setup_govmap_domain.bat as Administrator first
    pause
    exit /b 1
)

echo Starting backend server on sea-level-dash-local:8001...
cd backend
python local_server.py --host 0.0.0.0 --port 8001
pause