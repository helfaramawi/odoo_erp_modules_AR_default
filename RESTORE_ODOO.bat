@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title ODOO 17 - Full Restore

REM ╔══════════════════════════════════════════════════════════════════╗
REM ║          ODOO 17 FULL RESTORE SCRIPT  v1.0                      ║
REM ║          Covers: Database + Filestore + Custom Addons            ║
REM ╚══════════════════════════════════════════════════════════════════╝

REM ── CONFIGURATION (must match your BACKUP_ODOO.bat settings) ────────
set ODOO_CONTAINER=odoo17_app
set DB_CONTAINER=odoo17_db
set DB_USER=odoo
set DB_NAME=odoo17_db
set BACKUP_ROOT=C:\OdooBackups
set FILESTORE_CONTAINER_PATH=/var/lib/odoo/.local/share/Odoo/filestore
set ADDONS_CONTAINER_PATH=/mnt/extra-addons

REM ── BUILD TIMESTAMP FOR LOG ─────────────────────────────────────────
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TIMESTAMP=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%_%DT:~8,2%-%DT:~10,2%
set RESTORE_WORK_DIR=%TEMP%\odoo_restore_%TIMESTAMP%
set LOG_FILE=%BACKUP_ROOT%\restore_%TIMESTAMP%.log

REM ────────────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         ODOO 17 FULL RESTORE UTILITY            ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  WARNING: This will OVERWRITE the current database and files!
echo.

REM ── CHECK DOCKER RUNNING ────────────────────────────────────────────
docker info >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Docker is not running. Please start Docker Desktop first.
    pause & exit /b 1
)

REM ── CHECK CONTAINERS EXIST ──────────────────────────────────────────
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

REM ── SELECT ZIP FILE ─────────────────────────────────────────────────
if not "%~1"=="" (
    set ZIP_FILE=%~1
) else (
    echo  Available backups in %BACKUP_ROOT%:
    echo.
    set IDX=0
    for %%F in ("%BACKUP_ROOT%\odoo_backup_*.zip") do (
        set /a IDX+=1
        echo    [!IDX!] %%~nxF
        set "FILE_!IDX!=%%F"
    )
    if !IDX!==0 (
        echo  [ERROR] No backup ZIP files found in %BACKUP_ROOT%
        echo          Please place a backup ZIP here or pass the path as an argument.
        pause & exit /b 1
    )
    echo.
    set /p CHOICE=" Enter backup number to restore (1-%IDX%): "
    if "!CHOICE!"=="" (
        echo  [ERROR] No selection made.
        pause & exit /b 1
    )
    set ZIP_FILE=!FILE_%CHOICE%!
)

REM ── VALIDATE ZIP ────────────────────────────────────────────────────
if not exist "%ZIP_FILE%" (
    echo  [ERROR] ZIP file not found: %ZIP_FILE%
    pause & exit /b 1
)

echo.
echo  ─────────────────────────────────────────────────────
echo   Restore source : %ZIP_FILE%
echo   Target DB      : %DB_NAME% in %DB_CONTAINER%
echo   Odoo container : %ODOO_CONTAINER%
echo   Log file       : %LOG_FILE%
echo  ─────────────────────────────────────────────────────
echo.
set /p CONFIRM=" Type YES to confirm and start restore: "
if /i not "%CONFIRM%"=="YES" (
    echo  Restore cancelled.
    pause & exit /b 0
)

REM ── INIT LOG ────────────────────────────────────────────────────────
if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"
echo ════════════════════════════════════════════════ > "%LOG_FILE%"
echo  ODOO 17 RESTORE LOG >> "%LOG_FILE%"
echo  Timestamp : %TIMESTAMP% >> "%LOG_FILE%"
echo  ZIP Source: %ZIP_FILE% >> "%LOG_FILE%"
echo  DB Target : %DB_NAME% >> "%LOG_FILE%"
echo ════════════════════════════════════════════════ >> "%LOG_FILE%"

REM ── STEP 1: EXTRACT ZIP ─────────────────────────────────────────────
echo.
echo  [1/6] Extracting backup ZIP...
if exist "%RESTORE_WORK_DIR%" rd /s /q "%RESTORE_WORK_DIR%"
mkdir "%RESTORE_WORK_DIR%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%RESTORE_WORK_DIR%' -Force" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [ERROR] Failed to extract ZIP. Check log: %LOG_FILE%
    rd /s /q "%RESTORE_WORK_DIR%"
    pause & exit /b 1
)
echo  [OK] ZIP extracted to temp folder.
echo  [OK] ZIP extracted >> "%LOG_FILE%"

REM ── VERIFY DUMP FILE EXISTS ─────────────────────────────────────────
set DUMP_FILE=%RESTORE_WORK_DIR%\database\%DB_NAME%.dump
if not exist "%DUMP_FILE%" (
    echo  [ERROR] Database dump not found inside ZIP: database\%DB_NAME%.dump
    echo  [FAILED] Dump file missing >> "%LOG_FILE%"
    rd /s /q "%RESTORE_WORK_DIR%"
    pause & exit /b 1
)

REM ── STEP 2: STOP ODOO CONTAINER ─────────────────────────────────────
echo  [2/6] Stopping Odoo container...
docker stop %ODOO_CONTAINER% >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [WARNING] Could not stop %ODOO_CONTAINER% — may already be stopped.
    echo  [WARNING] Stop container >> "%LOG_FILE%"
) else (
    echo  [OK] Odoo container stopped.
    echo  [OK] Odoo container stopped >> "%LOG_FILE%"
)

REM ── STEP 3: DROP AND RECREATE DATABASE ──────────────────────────────
echo  [3/6] Dropping existing database "%DB_NAME%"...
docker exec %DB_CONTAINER% psql -U %DB_USER% -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='%DB_NAME%' AND pid <> pg_backend_pid();" >> "%LOG_FILE%" 2>&1
docker exec %DB_CONTAINER% psql -U %DB_USER% -d postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [ERROR] Failed to drop database. Check log: %LOG_FILE%
    echo  [FAILED] Drop database >> "%LOG_FILE%"
    docker start %ODOO_CONTAINER% >nul 2>&1
    rd /s /q "%RESTORE_WORK_DIR%"
    pause & exit /b 1
)
echo  [OK] Old database dropped.

echo  Creating new database "%DB_NAME%"...
docker exec %DB_CONTAINER% psql -U %DB_USER% -d postgres -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [ERROR] Failed to create database. Check log: %LOG_FILE%
    echo  [FAILED] Create database >> "%LOG_FILE%"
    docker start %ODOO_CONTAINER% >nul 2>&1
    rd /s /q "%RESTORE_WORK_DIR%"
    pause & exit /b 1
)
echo  [OK] New empty database created.
echo  [OK] Database drop+create >> "%LOG_FILE%"

REM ── STEP 4: RESTORE DATABASE DUMP ───────────────────────────────────
echo  [4/6] Restoring PostgreSQL database (this may take a while)...
docker cp "%DUMP_FILE%" %DB_CONTAINER%:/tmp/%DB_NAME%.dump >> "%LOG_FILE%" 2>&1
docker exec %DB_CONTAINER% pg_restore -U %DB_USER% -d %DB_NAME% --no-owner --role=%DB_USER% -v /tmp/%DB_NAME%.dump >> "%LOG_FILE%" 2>&1
REM pg_restore returns warnings (exit 1) even on partial success — check for critical failure
docker exec %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME% -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Database restore failed — no tables found. Check log: %LOG_FILE%
    echo  [FAILED] Database restore >> "%LOG_FILE%"
    docker start %ODOO_CONTAINER% >nul 2>&1
    rd /s /q "%RESTORE_WORK_DIR%"
    pause & exit /b 1
)
docker exec %DB_CONTAINER% rm -f /tmp/%DB_NAME%.dump >nul 2>&1
echo  [OK] Database restored successfully.
echo  [OK] Database restore >> "%LOG_FILE%"

REM ── STEP 5: RESTORE FILESTORE ───────────────────────────────────────
echo  [5/6] Restoring filestore...
set FILESTORE_LOCAL=%RESTORE_WORK_DIR%\filestore
if exist "%FILESTORE_LOCAL%" (
    REM Clear existing filestore inside container then copy restored version
    docker start %ODOO_CONTAINER% >nul 2>&1
    timeout /t 3 /nobreak >nul
    docker exec %ODOO_CONTAINER% rm -rf %FILESTORE_CONTAINER_PATH% >> "%LOG_FILE%" 2>&1
    docker stop %ODOO_CONTAINER% >nul 2>&1
    docker cp "%FILESTORE_LOCAL%" %ODOO_CONTAINER%:%FILESTORE_CONTAINER_PATH% >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo  [WARNING] Filestore restore had issues. Check log: %LOG_FILE%
        echo  [WARNING] Filestore restore >> "%LOG_FILE%"
    ) else (
        echo  [OK] Filestore restored.
        echo  [OK] Filestore restore >> "%LOG_FILE%"
    )
) else (
    echo  [WARNING] No filestore folder found in backup — skipping.
    echo  [WARNING] No filestore in backup >> "%LOG_FILE%"
)

REM ── STEP 6: RESTORE CUSTOM ADDONS ───────────────────────────────────
echo  [6/6] Restoring custom addons...
set ADDONS_LOCAL=%RESTORE_WORK_DIR%\addons
if exist "%ADDONS_LOCAL%" (
    docker cp "%ADDONS_LOCAL%" %ODOO_CONTAINER%:%ADDONS_CONTAINER_PATH% >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo  [WARNING] Addons restore had issues. Check log: %LOG_FILE%
        echo  [WARNING] Addons restore >> "%LOG_FILE%"
    ) else (
        echo  [OK] Custom addons restored.
        echo  [OK] Addons restore >> "%LOG_FILE%"
    )
) else (
    echo  [WARNING] No addons folder found in backup — skipping.
    echo  [WARNING] No addons in backup >> "%LOG_FILE%"
)

REM ── RESTART ODOO ────────────────────────────────────────────────────
echo.
echo  Starting Odoo container...
docker start %ODOO_CONTAINER% >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo  [WARNING] Could not start %ODOO_CONTAINER% automatically.
    echo            Please start it manually: docker start %ODOO_CONTAINER%
    echo  [WARNING] Auto-start failed >> "%LOG_FILE%"
) else (
    echo  [OK] Odoo container started.
    echo  [OK] Odoo started >> "%LOG_FILE%"
)

REM ── CLEANUP TEMP ────────────────────────────────────────────────────
rd /s /q "%RESTORE_WORK_DIR%"

REM ── SUMMARY ─────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║             RESTORE COMPLETE                     ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Source ZIP : %ZIP_FILE%
echo  Log File   : %LOG_FILE%
echo.
echo  Odoo should be available shortly at http://localhost:8069
echo.
pause
endlocal
