@echo off
echo Stopping any running React processes...
taskkill /f /im node.exe 2>nul
echo.
echo The infinite loop has been fixed in the React app.
echo.
echo Key fixes applied:
echo - Removed predictions dependency from fetchData useCallback
echo - Made fetchPredictions a useCallback to prevent recreation
echo - Simplified prediction display in table
echo - Fixed tidal data handling
echo.
echo You can now restart the frontend with:
echo .\start_frontend.bat
echo.
pause