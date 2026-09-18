@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - stop the Odoo + Postgres stack
REM
REM Stops the containers but does NOT remove them, the images, or
REM the named volumes (database + filestore survive). Use start.bat
REM or restart.bat to bring it back up.
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

echo ============================================================
echo  Demo Edition - stopping stack ...
echo ============================================================
docker compose --env-file .env -f docker\docker-compose.demo.yml stop
if errorlevel 1 (
    echo [ERROR] docker compose stop failed - see output above.
    exit /b 1
)

echo.
echo Stopped. Data is untouched - run start.bat to bring it back up.
endlocal
