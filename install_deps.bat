@echo off
echo Installing missing Python packages...
pip install uvicorn[standard]==0.30.1
pip install scikit-learn==1.4.2
pip install python-dotenv
echo.
echo Python packages installed!
pause