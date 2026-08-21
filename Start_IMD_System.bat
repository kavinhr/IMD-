@echo off
echo Starting Weather Data Management System...
start "IMD System Server" cmd /k "call venv\Scripts\activate.bat && python run.py"
timeout /t 3 /nobreak > nul
start http://127.0.0.1:5000
echo System started! Check the black server window if page does not load.
exit
