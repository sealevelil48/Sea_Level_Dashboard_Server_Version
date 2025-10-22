@echo off
echo Starting Sea Level Dashboard Frontend (Simple Mode)...
cd frontend
set REACT_APP_API_URL=http://localhost:30886
npm start
pause