@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - restart the Odoo + Postgres stack
REM
REM This is NOT "docker compose restart" (that only restarts the
REM existing containers with whatever code was baked into the image
REM at the last build - it will NOT pick up a git pull). It rebuilds
REM the image first, exactly like start.bat, so code changes on disk
REM always take effect. Data (database + filestore, both in named
REM volumes) is untouched either way.
REM
REM Usage: run from anywhere; it locates demo_edition itself.
REM ============================================================

cd /d "%~dp0..\.."
if not exist docker\docker-compose.demo.yml (
    echo [ERROR] docker\docker-compose.demo.yml not found under %cd%.
    exit /b 1
)
if not exist .env (
    echo [ERROR] .env not found in %cd%.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker does not appear to be running. Start Docker Desktop and try again.
    exit /b 1
)

echo ============================================================
echo  Demo Edition - rebuilding and restarting stack ...
echo ============================================================
docker compose --env-file .env -f docker\docker-compose.demo.yml up -d --build
if errorlevel 1 (
    echo [ERROR] docker compose up failed - see output above.
    exit /b 1
)

echo.
docker compose --env-file .env -f docker\docker-compose.demo.yml ps
echo.
echo Done. Remember: an Odoo module Upgrade (Apps menu) is still needed
echo separately whenever a module's views/security/data files changed -
echo this restart only refreshes the code, not the database records.
endlocal
