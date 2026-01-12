@echo off
echo ========================================
echo   Code Update
echo ========================================
cd /d "%~dp0"
echo.
echo [1/2] Fetching from remote...
git fetch origin
echo.
echo [2/2] Pulling latest code...
git pull origin claude/korean-news-ai-filter-8JpiG
echo.
echo ========================================
echo   Update Complete\!
echo ========================================
git log -1 --oneline
echo.
pause
