@echo off
echo Starting Sea Level Dashboard...

cd /d C:\Users\slg\Sea_Level_Dashboard_AWS_Ver_20_8_25\backend
call venv\Scripts\activate
start python local_server.py

timeout /t 5
start http://127.0.0.1:30886

echo Server started. Opening browser...