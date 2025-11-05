@echo off
echo Fixing port conflict issue...
echo.

echo [1/3] Stopping existing backend processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Checking if port 30886 is free...
netstat -an | findstr :30886 >nul
if %errorLevel% equ 0 (
    echo Port 30886 still in use. Finding process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :30886') do (
        echo Killing process %%a
        taskkill /f /pid %%a 2>nul
    )
)

echo [3/3] Port should now be free. Starting backend...
cd backend
python local_server.py --host 0.0.0.0 --port 30886
pause