@echo off
echo === Sea Level Dashboard Diagnostic ===
echo.
echo Python Version:
python --version
echo.
echo Node Version:
node --version
echo.
echo NPM Version:
npm --version
echo.
echo Port 30886 Status:
netstat -an | findstr :30886
echo.
echo Firewall Rules:
netsh advfirewall firewall show rule name="Sea Level Dashboard"
echo.
echo PostgreSQL Status:
sc query postgresql-x64-13
echo.
echo Current Directory:
cd
echo.
echo Python Packages:
pip list | findstr "fastapi uvicorn sqlalchemy"
echo.