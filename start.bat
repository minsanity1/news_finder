@echo off
echo ========================================
echo   News Finder Start
echo ========================================

cd /d "%~dp0"

echo.
echo [1/2] Starting Backend Server...
start "Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"

echo Waiting 3 seconds...
ping 127.0.0.1 -n 4 > nul

echo.
echo [2/2] Starting Frontend Server...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Servers Started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
echo.
pause
