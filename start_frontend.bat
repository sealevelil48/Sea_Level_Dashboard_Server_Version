@echo off
echo Starting Sea Level Dashboard Frontend...
echo.
echo This will start the frontend that connects to backend at http://127.0.0.1:30886
echo Frontend will be available at http://localhost:3000
echo.

cd frontend
echo Installing dependencies if needed...
call npm install

echo Installing cross-env for Windows compatibility...
call npm install cross-env

echo Starting frontend...
set REACT_APP_API_URL=http://127.0.0.1:30886
call npm start
pause