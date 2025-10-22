@echo off
echo Restarting Sea Level Dashboard with GovMap fixes...
echo.

REM Kill existing processes
echo Stopping existing services...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

echo Starting backend server...
cd backend
start "Backend Server" cmd /k "python local_server.py"

echo Waiting for backend to start...
timeout /t 5 >nul

echo Starting frontend...
cd ..\frontend
start "Frontend Server" cmd /k "npm start"

echo.
echo Services started! 
echo Backend: http://127.0.0.1:30886
echo Frontend: http://localhost:30887
echo.
echo Test GovMap directly: http://127.0.0.1:30886/mapframe
echo.
pause