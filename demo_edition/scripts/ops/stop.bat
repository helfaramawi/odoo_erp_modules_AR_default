@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - stop the Odoo + Postgres stack
REM
REM Stops the containers but does NOT remove them, the images, or
REM the named volumes (database + filestore survive). Use start.bat
REM or restart.bat to bring it back up.
REM
REM This window stays open (press a key to close) so you can always
REM read what happened, success or failure.
REM ============================================================

cd /d "%~dp0..\.."
if not exist docker\docker-compose.demo.yml (
    echo [ERROR] docker\docker-compose.demo.yml not found under %cd%.
    goto :end
)
if not exist .env (
    echo [ERROR] .env not found in %cd%.
    goto :end
)

echo ============================================================
echo  Demo Edition - stopping stack ...
echo ============================================================
docker compose --env-file .env -f docker\docker-compose.demo.yml stop
if errorlevel 1 (
    echo [ERROR] docker compose stop failed - see output above.
    goto :end
)

echo.
echo Stopped. Data is untouched - run start.bat to bring it back up.

:end
echo.
pause
endlocal
