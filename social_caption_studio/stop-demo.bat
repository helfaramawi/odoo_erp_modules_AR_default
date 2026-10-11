@echo off
REM Social Caption Generator - stop the demo (Windows). Data is kept for next time.
cd /d "%~dp0"
docker compose down
pause
