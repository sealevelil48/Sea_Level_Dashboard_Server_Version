@echo off
echo Testing outliers endpoint directly...
echo.

echo Making direct API call to outliers endpoint:
curl -s "http://5.102.231.16:30886/api/outliers?start_date=2025-11-03&end_date=2025-11-10&station=All Stations" | jq ".outliers_detected, .total_records"

echo.
echo If you see numbers above, outliers are being detected.
echo Check browser console for mapping debug info.
pause