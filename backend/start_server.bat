@echo off
:: Ensure we are in the backend directory
cd /d "%~dp0"

:: Activate virtual environment and run the server
call venv\Scripts\activate && python local_server.py