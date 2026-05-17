@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title ODOO 17 - Full Backup

REM ╔══════════════════════════════════════════════════════════════════╗
REM ║          ODOO 17 FULL BACKUP SCRIPT  v1.0                       ║
REM ║          Covers: Database + Filestore + Custom Addons            ║
REM ╚══════════════════════════════════════════════════════════════════╝

REM ── CONFIGURATION (edit these if needed) ────────────────────────────
set ODOO_CONTAINER=odoo17_app
set DB_CONTAINER=odoo17_db
set DB_USER=odoo
set DB_NAME=odoo17_db
set BACKUP_ROOT=C:\OdooBackups
set FILESTORE_CONTAINER_PATH=/var/lib/odoo/.local/share/Odoo/filestore
set ADDONS_CONTAINER_PATH=/mnt/extra-addons

REM ── BUILD TIMESTAMP ─────────────────────────────────────────────────
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TIMESTAMP=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%_%DT:~8,2%-%DT:~10,2%
set BACKUP_DIR=%BACKUP_ROOT%\backup_%TIMESTAMP%
set LOG_FILE=%BACKUP_DIR%\backup.log
set ZIP_FILE=%BACKUP_ROOT%\odoo_backup_%TIMESTAMP%.zip

REM ────────────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         ODOO 17 FULL BACKUP STARTING            ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ── CHECK DOCKER RUNNING ────────────────────────────────────────────
docker info >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Docker is not running. Please start Docker Desktop first.
    pause & exit /b 1
)

REM ── CHECK CONTAINERS ────────────────────────────────────────────────
docker inspect %ODOO_CONTAINER% >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Container "%ODOO_CONTAINER%" not found.
    pause & exit /b 1
)
docker inspect %DB_CONTAINER% >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Container "%DB_CONTAINER%" not found.
    pause & exit /b 1
)

REM ── CREATE BACKUP DIRECTORY ─────────────────────────────────────────
if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"
mkdir "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%\database"
mkdir "%BACKUP_DIR%\filestore"
mkdir "%BACKUP_DIR%\addons"

REM ── START LOG ───────────────────────────────────────────────────────
echo ════════════════════════════════════════════════ > "%LOG_FILE%"
echo  ODOO 17 BACKUP LOG >> "%LOG_FILE%"
echo  Timestamp : %TIMESTAMP% >> "%LOG_FILE%"
echo  DB        : %DB_NAME% >> "%LOG_FILE%"
echo  Container : %ODOO_CONTAINER% >> "%LOG_FILE%"
echo ════════════════════════════════════════════════ >> "%LOG_FILE%"

REM ── STEP 1: DATABASE DUMP ───────────────────────────────────────────
echo  [1/4] Backing up PostgreSQL database...
docker exec %DB_CONTAINER% pg_dump -U %DB_USER% -Fc %DB_NAME% > "%BACKUP_DIR%\database\%DB_NAME%.dump" 2>> "%LOG_FILE%"
if errorlevel 1 (
    echo  [ERROR] Database backup failed. Check log: %LOG_FILE%
    echo  [FAILED] Database backup >> "%LOG_FILE%"
    pause & exit /b 1
)
echo  [OK] Database backup complete.
echo  [OK] Database backup >> "%LOG_FILE%"

REM ── STEP 2: FILESTORE ───────────────────────────────────────────────
echo  [2/4] Backing up filestore (attachments)...
docker cp %ODOO_CONTAINER%:%FILESTORE_CONTAINER_PATH% "%BACKUP_DIR%\filestore\" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [WARNING] Filestore backup had issues. Check log.
    echo  [WARNING] Filestore backup >> "%LOG_FILE%"
) else (
    echo  [OK] Filestore backup complete.
    echo  [OK] Filestore backup >> "%LOG_FILE%"
)

REM ── STEP 3: CUSTOM ADDONS ───────────────────────────────────────────
echo  [3/4] Backing up custom addons...
docker cp %ODOO_CONTAINER%:%ADDONS_CONTAINER_PATH% "%BACKUP_DIR%\addons\" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [WARNING] Addons backup had issues. Check log.
    echo  [WARNING] Addons backup >> "%LOG_FILE%"
) else (
    echo  [OK] Addons backup complete.
    echo  [OK] Addons backup >> "%LOG_FILE%"
)

REM ── STEP 4: COMPRESS TO ZIP ─────────────────────────────────────────
echo  [4/4] Compressing backup to ZIP...
powershell -Command "Compress-Archive -Path '%BACKUP_DIR%\*' -DestinationPath '%ZIP_FILE%' -Force" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [WARNING] Compression failed. Raw backup still available at:
    echo            %BACKUP_DIR%
    echo  [WARNING] Compression failed >> "%LOG_FILE%"
) else (
    echo  [OK] ZIP created: %ZIP_FILE%
    echo  [OK] ZIP: %ZIP_FILE% >> "%LOG_FILE%"
    REM Remove uncompressed folder to save space
    rd /s /q "%BACKUP_DIR%"
)

REM ── SUMMARY ─────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║              BACKUP COMPLETE                     ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  ZIP File : %ZIP_FILE%
echo  Log File : %LOG_FILE%
echo.
pause
endlocal
