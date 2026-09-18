@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - restore from a backup made by backup.bat
REM
REM Usage:
REM   restore.bat <timestamp>      e.g. restore.bat 20260918_143000
REM   restore.bat                  (lists available backups and asks)
REM
REM Restores the DATABASE and FILESTORE from
REM   demo_edition\backups\<timestamp>\database.dump
REM   demo_edition\backups\<timestamp>\filestore.tar.gz
REM This REPLACES the current database and filestore - irreversible.
REM
REM config_and_addons.zip from that backup is NOT auto-applied over
REM your live code (that could silently clobber newer local edits) -
REM it is only extracted alongside for you to review/copy from by hand,
REM at backups\<timestamp>\_extracted_config\.
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

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker does not appear to be running. Start Docker Desktop and try again.
    goto :end
)

set "TS=%~1"
if not defined TS (
    echo Available backups in backups\:
    echo ------------------------------------------------------------
    dir /b /ad backups 2>nul
    echo ------------------------------------------------------------
    set /p "TS=Enter the timestamp to restore (e.g. 20260918_143000): "
)
if not defined TS (
    echo [ERROR] No timestamp given.
    goto :end
)

set "SRC=backups\%TS%"
if not exist "%SRC%\database.dump" (
    echo [ERROR] %SRC%\database.dump not found.
    goto :end
)
if not exist "%SRC%\filestore.tar.gz" (
    echo [ERROR] %SRC%\filestore.tar.gz not found.
    goto :end
)

REM ---- read DEMO_DB_NAME / DEMO_DB_USER from .env (with safe fallbacks) ----
set "DB_NAME="
set "DB_USER="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if "%%A"=="DEMO_DB_NAME" set "DB_NAME=%%B"
    if "%%A"=="DEMO_DB_USER" set "DB_USER=%%B"
)
if not defined DB_NAME set "DB_NAME=demo_gov_erp"
if not defined DB_USER set "DB_USER=demo_odoo"

echo ============================================================
echo  WARNING - DESTRUCTIVE OPERATION
echo  This will DROP and REPLACE the current database "%DB_NAME%"
echo  and OVERWRITE the current Odoo filestore with the contents of:
echo    %SRC%
echo  Anything created since that backup will be LOST.
echo ============================================================
set /p "CONFIRM=Type YES (all caps) to continue: "
if not "%CONFIRM%"=="YES" (
    echo Aborted - nothing was changed.
    goto :end
)

echo.
echo [1/6] Stopping Odoo (keeping the database service up) ...
docker compose --env-file .env -f docker\docker-compose.demo.yml stop odoo
if errorlevel 1 (
    echo [ERROR] Could not stop the odoo service.
    goto :end
)

echo [2/6] Dropping and recreating database "%DB_NAME%" ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T db ^
    dropdb -U %DB_USER% --if-exists %DB_NAME%
if errorlevel 1 (
    echo [ERROR] dropdb failed.
    goto :end
)
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T db ^
    createdb -U %DB_USER% -O %DB_USER% %DB_NAME%
if errorlevel 1 (
    echo [ERROR] createdb failed.
    goto :end
)

echo [3/6] Restoring database from %SRC%\database.dump ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T db ^
    pg_restore -U %DB_USER% -d %DB_NAME% --no-owner < "%SRC%\database.dump"
if errorlevel 1 (
    echo [WARN] pg_restore reported errors - this is sometimes just harmless
    echo        "role/extension already exists" notices. Check the output above.
)

echo [4/6] Clearing current filestore ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T odoo ^
    sh -c "find /var/lib/odoo -mindepth 1 -delete"
if errorlevel 1 (
    echo [ERROR] Could not clear the existing filestore.
    goto :end
)

echo [5/6] Restoring filestore from %SRC%\filestore.tar.gz ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T odoo ^
    tar xzf - -C /var/lib/odoo < "%SRC%\filestore.tar.gz"
if errorlevel 1 (
    echo [ERROR] Filestore restore failed.
    goto :end
)

echo [6/6] Rebuilding and starting Odoo back up ...
docker compose --env-file .env -f docker\docker-compose.demo.yml up -d --build odoo
if errorlevel 1 (
    echo [ERROR] Could not start odoo back up.
    goto :end
)

if exist "%SRC%\config_and_addons.zip" (
    echo.
    echo Extracting config_and_addons.zip for review (NOT applied automatically) ...
    powershell -NoProfile -Command ^
        "Expand-Archive -Path '%SRC%\config_and_addons.zip' -DestinationPath '%SRC%\_extracted_config' -Force"
    echo   -^> %SRC%\_extracted_config\
    echo   Compare/copy from there by hand if you also need old .env/addons/docker files.
)

echo.
echo ============================================================
echo  Restore complete from backup: %TS%
echo ============================================================

:end
echo.
pause
endlocal
