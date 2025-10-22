@echo off
echo Starting Sea Level Dashboard...

echo 1. Stop any running frontend (Ctrl+C if needed)
echo 2. Starting backend...
start "Backend" cmd /k "cd backend && python local_server.py"

echo 3. Waiting for backend...
timeout /t 3 /nobreak >nul

echo 4. Starting frontend...
cd frontend
call npm start

pause