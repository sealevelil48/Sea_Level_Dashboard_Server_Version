@echo off
echo Fixing domain configuration for GovMap support...
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

echo Updating hosts file with correct domain format...

REM Backup hosts file
copy C:\Windows\System32\drivers\etc\hosts C:\Windows\System32\drivers\etc\hosts.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%

REM Remove old entry and add correct one
powershell -Command "(Get-Content C:\Windows\System32\drivers\etc\hosts) | Where-Object { $_ -notmatch 'Sea-Level-Dash-Local' } | Set-Content C:\Windows\System32\drivers\etc\hosts"
echo 127.0.0.1    sea-level-dash-local >> C:\Windows\System32\drivers\etc\hosts

echo Domain configuration fixed!
echo You can now run start_backend.bat and start_frontend.bat
echo.
pause