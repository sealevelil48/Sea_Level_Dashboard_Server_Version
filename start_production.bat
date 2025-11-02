@echo off
echo ========================================
echo   Sea Level Dashboard - Production Mode
echo ========================================
echo.

echo [1/4] Stopping any existing development servers...
taskkill /f /im node.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Navigating to frontend directory...
cd /d "%~dp0frontend"

echo [3/4] Building production bundle (this may take 2-3 minutes)...
echo   - Disabling source maps for faster loading
echo   - Minifying JavaScript and CSS
echo   - Optimizing assets
echo.
call npm run build-govmap

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed! Check the output above.
    pause
    exit /b 1
)

echo [4/4] Starting production server...
echo.
echo ========================================
echo   PRODUCTION SERVER STARTING
echo ========================================
echo   Frontend: http://localhost:30887
echo   Backend:  http://5.102.231.16:30886
echo   
echo   Expected load time: 1-3 seconds
echo   Bundle size: Optimized production build
echo ========================================
echo.

npx serve -s build -l 30887

pause