@echo off
echo Starting Sea Level Dashboard for Production Access...
echo.

echo Starting backend server...
start "Backend" cmd /k "cd backend && python local_server.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting frontend for external access...
cd frontend
set REACT_APP_API_URL=http://5.102.231.16:30886
set HOST=0.0.0.0
set PORT=3000
set DANGEROUSLY_DISABLE_HOST_CHECK=true
call npm start

pause