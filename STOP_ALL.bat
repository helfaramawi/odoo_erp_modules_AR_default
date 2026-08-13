@echo off
setlocal
title STOP ODOO + OLLAMA + AI AGENT

echo ==========================================
echo STOPPING ODOO + AI AGENT ENVIRONMENT
echo ==========================================
echo.

REM === CONFIGURATION ===
set ODOO_APP_CONTAINER=odoo17_app
set ODOO_DB_CONTAINER=odoo17_db
set AGENT_PORT=8000

echo [1/4] Stopping AI Agent running on port %AGENT_PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%AGENT_PORT% ^| findstr LISTENING') do (
    echo Killing process PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.

echo [2/4] Stopping Odoo container: %ODOO_APP_CONTAINER%
docker stop %ODOO_APP_CONTAINER%

echo.

echo [3/4] Stopping PostgreSQL container: %ODOO_DB_CONTAINER%
docker stop %ODOO_DB_CONTAINER%

echo.

echo [4/4] Stopping Ollama server if running...
taskkill /IM ollama.exe /F >nul 2>&1
taskkill /IM "Ollama.exe" /F >nul 2>&1

echo.
echo ==========================================
echo ENVIRONMENT STOPPED
echo ==========================================
echo.
pause
