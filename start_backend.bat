@echo off
echo Starting Sea Level Dashboard Backend...
cd backend
python local_server.py --host 0.0.0.0 --port 8000
pause