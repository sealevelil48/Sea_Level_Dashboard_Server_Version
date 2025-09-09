@echo off
echo Installing all dependencies for Sea Level Dashboard...
echo.

echo 1. Installing Python dependencies...
pip install uvicorn[standard]==0.30.1 scikit-learn==1.4.2 python-dotenv

echo.
echo 2. Installing frontend dependencies...
cd frontend
call npm install

echo.
echo 3. All dependencies installed!
echo.
echo Next steps:
echo - Run: .\start_backend.bat (in one terminal)
echo - Run: .\start_frontend.bat (in another terminal)
echo.
pause