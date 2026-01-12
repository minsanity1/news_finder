@echo off
chcp 65001 > nul
echo ========================================
echo   코드 업데이트 시작
echo ========================================

cd /d "%~dp0"

echo.
echo [1/3] 원격 저장소에서 변경사항 가져오기...
git fetch origin

echo.
echo [2/3] 최신 코드로 업데이트...
git pull origin claude/korean-news-ai-filter-8JpiG

echo.
echo [3/3] 업데이트 완료!
echo ========================================
git log -1 --oneline
echo ========================================

echo.
pause
