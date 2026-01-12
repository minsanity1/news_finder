@echo off
chcp 65001 > nul
echo ========================================
echo   News Finder 업데이트 및 시작
echo ========================================

cd /d "%~dp0"

echo.
echo [1/4] 원격 저장소에서 변경사항 가져오기...
git fetch origin

echo.
echo [2/4] 최신 코드로 업데이트...
git pull origin claude/korean-news-ai-filter-8JpiG

echo.
echo ========================================
git log -1 --oneline
echo ========================================

echo.
echo [3/4] Backend 서버 시작 중... (새 창)
start "Backend Server" cmd /k "cd /d "%~dp0backend" && uvicorn app.main:app --reload --port 8000"

echo 백엔드 초기화 대기 중 (3초)...
timeout /t 3 /nobreak > nul

echo.
echo [4/4] Frontend 서버 시작 중... (새 창)
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo   서버가 시작되었습니다!
echo   - Backend:  http://localhost:8000
echo   - Frontend: http://localhost:5173
echo ========================================
echo.
pause
