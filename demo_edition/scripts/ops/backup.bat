@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - complete backup (database + filestore + config/addons)
REM
REM Creates demo_edition\backups\<timestamp>\ containing:
REM   - database.dump           (pg_dump, custom format, from the db container)
REM   - filestore.tar.gz        (Odoo attachments/filestore, from the odoo container)
REM   - config_and_addons.zip   (.env + docker\ + addons\ - a full code/config
REM                              snapshot; addons is already in git, but this
REM                              gives you one self-contained archive that
REM                              restores everything, git or no git)
REM
REM Usage: run from anywhere; it locates demo_edition itself.
REM This window stays open (press a key to close) so you can always
REM read what happened, success or failure.
REM ============================================================

cd /d "%~dp0..\.."
if not exist docker\docker-compose.demo.yml (
    echo [ERROR] docker\docker-compose.demo.yml not found under %cd%.
    echo         This script must live at demo_edition\scripts\ops\.
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

REM ---- read DEMO_DB_NAME / DEMO_DB_USER from .env (with safe fallbacks) ----
set "DB_NAME="
set "DB_USER="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if "%%A"=="DEMO_DB_NAME" set "DB_NAME=%%B"
    if "%%A"=="DEMO_DB_USER" set "DB_USER=%%B"
)
if not defined DB_NAME set "DB_NAME=demo_gov_erp"
if not defined DB_USER set "DB_USER=demo_odoo"

REM ---- timestamp (locale-independent, via PowerShell) ----
set "TS="
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
if not defined TS (
    echo [ERROR] Could not generate a timestamp.
    goto :end
)

set "OUTDIR=backups\%TS%"
mkdir "%OUTDIR%" 2>nul

echo ============================================================
echo  Demo Edition - full backup - %TS%
echo  Database: %DB_NAME%  (user: %DB_USER%)
echo  Output:   %OUTDIR%\
echo ============================================================
echo.
echo If the next step fails with a connection/container error, the
echo stack probably isn't running yet - run start.bat first.
echo.

echo [1/3] Dumping database ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T db ^
    pg_dump -U %DB_USER% -Fc %DB_NAME% > "%OUTDIR%\database.dump"
if errorlevel 1 (
    echo [ERROR] pg_dump failed - see output above. Is the stack running? ^(start.bat^)
    goto :end
)

echo [2/3] Archiving filestore ...
docker compose --env-file .env -f docker\docker-compose.demo.yml exec -T odoo ^
    tar czf - -C /var/lib/odoo . > "%OUTDIR%\filestore.tar.gz"
if errorlevel 1 (
    echo [ERROR] filestore archive failed - see output above.
    goto :end
)

echo [3/3] Archiving config + addons (.env, docker\, addons\) ...
powershell -NoProfile -Command ^
    "Compress-Archive -Path '.env','docker','addons' -DestinationPath '%OUTDIR%\config_and_addons.zip' -Force"
if errorlevel 1 (
    echo [ERROR] config/addons archive failed - see output above.
    goto :end
)

echo.
echo ============================================================
echo  Backup complete: %OUTDIR%\
dir /-c "%OUTDIR%"
echo ============================================================
echo  To restore this backup later, run:
echo    restore.bat %TS%
echo ============================================================

:end
echo.
pause
endlocal
