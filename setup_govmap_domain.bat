@echo off
echo Setting up GovMap domain configuration...
echo This script must be run as Administrator!
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Adding sea-level-dash-local to hosts file...

REM Backup hosts file
copy C:\Windows\System32\drivers\etc\hosts C:\Windows\System32\drivers\etc\hosts.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%

REM Check if entry already exists
findstr "sea-level-dash-local" C:\Windows\System32\drivers\etc\hosts >nul
if %errorLevel% equ 0 (
    echo Domain already configured in hosts file.
) else (
    echo 127.0.0.1    sea-level-dash-local >> C:\Windows\System32\drivers\etc\hosts
    echo Domain added to hosts file successfully!
)

echo.
echo GovMap domain configuration complete!
echo You can now run start_backend.bat and start_frontend.bat
echo.
pause