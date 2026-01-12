@echo off
echo ========================================
echo   News Finder Update and Start
echo ========================================
cd /d "%~dp0"
echo.
echo [1/4] Fetching from remote...
git fetch origin
echo.
echo [2/4] Pulling latest code...
git pull origin claude/korean-news-ai-filter-8JpiG
echo.
git log -1 --oneline
echo.
echo [3/4] Starting Backend Server...
start "Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"
echo Waiting 3 seconds...
ping 127.0.0.1 -n 4 > nul
echo.
echo [4/4] Starting Frontend Server...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo ========================================
echo   Servers Started\!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
echo.
pause
