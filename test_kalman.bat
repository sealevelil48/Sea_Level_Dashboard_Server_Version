@echo off
echo Testing Kalman Filter Fix...
echo.

echo Waiting for backend to start...
timeout /t 10 >nul

echo Testing predictions endpoint...
curl "http://5.102.231.16:30886/api/predictions?stations=Ashdod&model=kalman&steps=24"

echo.
echo.
echo If you see forecast data above, Kalman filter is working!
echo If you see empty kalman array, check the backend logs.
pause