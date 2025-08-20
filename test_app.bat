@echo off
echo Testing Sea Level Dashboard...
echo.

echo 1. Testing backend API...
curl -s http://localhost:8000/health > nul
if %errorlevel% == 0 (
    echo ✅ Backend is running
) else (
    echo ❌ Backend not running - start with: .\start_backend.bat
)

echo.
echo 2. Testing frontend...
curl -s http://localhost:3000 > nul
if %errorlevel% == 0 (
    echo ✅ Frontend is running
) else (
    echo ❌ Frontend not running - start with: .\start_frontend.bat
)

echo.
echo 3. Opening dashboard in browser...
start http://localhost:3000

pause