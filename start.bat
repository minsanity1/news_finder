@echo off
chcp 65001 > nul
echo ========================================
echo   News Finder 시작
echo ========================================

cd /d "%~dp0"

echo.
echo [1/2] Backend 서버 시작 중... (새 창)
start "Backend Server" cmd /k "cd /d "%~dp0backend" && uvicorn app.main:app --reload --port 8000"

echo 백엔드 초기화 대기 중 (3초)...
timeout /t 3 /nobreak > nul

echo.
echo [2/2] Frontend 서버 시작 중... (새 창)
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo   서버가 시작되었습니다!
echo   - Backend:  http://localhost:8000
echo   - Frontend: http://localhost:5173
echo ========================================
echo.
echo 이 창은 닫아도 됩니다.
pause
