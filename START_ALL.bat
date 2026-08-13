@echo off
setlocal
title START ODOO + OLLAMA + AI AGENT

echo ==========================================
echo STARTING ODOO + AI AGENT ENVIRONMENT
echo ==========================================
echo.

REM === CONFIGURATION ===
set ODOO_APP_CONTAINER=odoo17_app
set ODOO_DB_CONTAINER=odoo17_db
set AGENT_DIR=C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default\odoo_ai_agent
set AGENT_PORT=8000
set ODOO_PORT=8069
set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe

echo [1/5] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker Desktop to start...
    timeout /t 25 /nobreak >nul
)

docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is still not running. Please start Docker Desktop manually.
    pause
    exit /b 1
)

echo Docker is running.
echo.

echo [2/5] Starting PostgreSQL container: %ODOO_DB_CONTAINER%
docker start %ODOO_DB_CONTAINER%
if errorlevel 1 (
    echo ERROR: Could not start %ODOO_DB_CONTAINER%
    pause
    exit /b 1
)

echo Waiting for PostgreSQL health...
timeout /t 5 /nobreak >nul

echo [3/5] Starting Odoo container: %ODOO_APP_CONTAINER%
docker start %ODOO_APP_CONTAINER%
if errorlevel 1 (
    echo ERROR: Could not start %ODOO_APP_CONTAINER%
    pause
    exit /b 1
)

echo Waiting for Odoo...
timeout /t 8 /nobreak >nul

echo [4/5] Starting Ollama...
where ollama >nul 2>&1
if not errorlevel 1 (
    start "Ollama Server" /min cmd /c "ollama serve"
) else (
    if exist "%OLLAMA_EXE%" (
        start "Ollama Server" /min cmd /c ""%OLLAMA_EXE%" serve"
    ) else (
        echo WARNING: Ollama executable not found. If Ollama is already running, ignore this.
    )
)

timeout /t 5 /nobreak >nul

echo [5/5] Starting AI Agent on port %AGENT_PORT%...
if not exist "%AGENT_DIR%\venv\Scripts\activate.bat" (
    echo ERROR: Agent virtual environment not found:
    echo %AGENT_DIR%\venv\Scripts\activate.bat
    pause
    exit /b 1
)

start "Odoo AI Agent" cmd /k "cd /d "%AGENT_DIR%" && call venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port %AGENT_PORT%"

echo.
echo ==========================================
echo ENVIRONMENT STARTED
echo ==========================================
echo Odoo:        http://localhost:%ODOO_PORT%
echo AI Agent:    http://localhost:%AGENT_PORT%
echo Swagger:     http://localhost:%AGENT_PORT%/docs
echo ==========================================
echo.
pause
