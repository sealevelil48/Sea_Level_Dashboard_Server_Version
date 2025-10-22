@echo off
echo Starting Sea Level Dashboard for Client Access...
echo.
echo Backend will run on: http://5.102.231.16:30886
echo Frontend will run on: http://5.102.231.16:30887
echo.

cd frontend
echo Setting up for external access...

echo Starting frontend for clients...
npm run start-external
pause