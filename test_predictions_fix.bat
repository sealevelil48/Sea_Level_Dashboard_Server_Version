@echo off
echo Testing Predictions Fix...
echo.

echo 1. Testing backend /api/predictions endpoint...
curl "http://5.102.231.16:30886/api/predictions?stations=Ashdod&model=kalman&steps=24"
echo.
echo.

echo 2. If you see JSON data above (not HTML), the backend is working!
echo 3. Now test in browser:
echo    - Open http://5.102.231.16:30887
echo    - Select a station (e.g., Ashdod)
echo    - Check "Kalman Filter" model
echo    - Change forecast period dropdown
echo    - Look for forecast line on graph
echo.

echo 4. Check browser console for:
echo    ✅ "Predictions received successfully: ['Ashdod', 'global_metadata']"
echo    ❌ NO "SyntaxError: Unexpected token"
echo.

pause