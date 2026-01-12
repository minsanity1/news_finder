@echo off
echo ========================================
echo   News Finder Initial Setup
echo ========================================
cd /d "%~dp0"
echo.
echo [1/4] Creating Backend virtual environment...
cd backend
python -m venv venv
echo.
echo [2/4] Activating venv and installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..
echo.
echo [3/4] Installing Frontend packages...
cd frontend
call npm install
cd ..
echo.
echo [4/4] Setup Complete\!
echo ========================================
echo   Now run start.bat to launch servers
echo ========================================
pause
