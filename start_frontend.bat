@echo off
echo Starting Sea Level Dashboard Frontend with GovMap support...
echo.

REM Check domain configuration
findstr "sea-level-dash-local" C:\Windows\System32\drivers\etc\hosts >nul
if %errorLevel% neq 0 (
    echo ERROR: Domain not configured!
    echo Please run setup_govmap_domain.bat as Administrator first
    pause
    exit /b 1
)

cd frontend
echo Installing dependencies if needed...
call npm install

echo Installing cross-env for Windows compatibility...
call npm install cross-env

echo Starting frontend on sea-level-dash-local:3000...
call npm run start-govmap
pause