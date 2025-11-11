@echo off
echo ========================================
echo   Restarting Sea Level Dashboard Backend
echo ========================================

echo [1/3] Stopping existing backend processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1

echo [2/3] Waiting for cleanup...
timeout /t 3 /nobreak >nul

echo [3/3] Starting optimized backend...
cd /d "%~dp0backend"
python local_server.py

pause