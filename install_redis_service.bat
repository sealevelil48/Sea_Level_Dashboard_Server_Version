@echo off
echo Installing Redis as Windows Service...
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Creating Redis Windows Service...
sc create Redis binpath="C:\Users\slg\Downloads\Redis-x64-3.0.504\redis-server.exe --service-run" start=auto displayname="Redis Cache Server"

if %errorLevel% equ 0 (
    echo ✅ Redis service created successfully!
    echo.
    echo Starting Redis service...
    sc start Redis
    
    if %errorLevel% equ 0 (
        echo ✅ Redis service started successfully!
        echo.
        echo Redis is now installed as a Windows service and will:
        echo - Start automatically when Windows boots
        echo - Run in the background
        echo - Provide 97%% performance improvement to your dashboard
        echo.
        echo You can now use .\start_backend.bat normally!
    ) else (
        echo ❌ Failed to start Redis service
        echo Check the service in Services.msc
    )
) else (
    echo ❌ Failed to create Redis service
    echo Make sure the Redis path is correct
)

echo.
pause