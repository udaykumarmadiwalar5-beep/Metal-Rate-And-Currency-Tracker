@echo off
title Styles Metal and Currency Tracker Server
echo ===================================================
echo  STARTING PRODUCTION-GRADE WAITRESS SERVER (PORT 5001)
echo ===================================================

:: Activate your local python virtual environment if you use one
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Run the script using the multi-threaded production gateway
python -c "from waitress import serve; from app import app; print('Server live at http://127.0.0.1:5001'); serve(app, host='127.0.0.1', port=5001, threads=4)"

pause
