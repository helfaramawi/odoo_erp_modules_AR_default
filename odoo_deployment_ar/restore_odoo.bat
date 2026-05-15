@echo off
setlocal

echo === Pulling latest code ===
cd /d "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default"
git pull origin claude/fix-module-55-visibility-oZHNF
cd odoo_deployment_ar

set DB_NAME=odoo17_db
set DB_USER=odoo
set DB_PASS=odoo_secure_pass

echo.
echo === ODOO RESTORE SCRIPT ===
echo This will OVERWRITE the current database and filestore!
echo.
set /p BACKUP_PATH=Enter full path to backup folder (e.g. C:\Users\SZ TECH\Downloads\odoo_backups\backup_20260515_084800):

if not exist "%BACKUP_PATH%\odoo_db.dump" (
    echo ERROR: odoo_db.dump not found in %BACKUP_PATH%
    pause
    exit /b 1
)
if not exist "%BACKUP_PATH%\filestore.tar.gz" (
    echo ERROR: filestore.tar.gz not found in %BACKUP_PATH%
    pause
    exit /b 1
)

echo.
set /p CONFIRM=Are you sure? This deletes current data! Type YES to continue:
if /i not "%CONFIRM%"=="YES" (
    echo Cancelled.
    pause
    exit /b 0
)

echo === Stopping Odoo app ===
docker stop odoo17_app

echo === Dropping and recreating database ===
docker exec odoo17_db psql -U %DB_USER% -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='%DB_NAME%';"
docker exec odoo17_db psql -U %DB_USER% -d postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"
docker exec odoo17_db psql -U %DB_USER% -d postgres -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"

echo === Restoring database ===
docker cp "%BACKUP_PATH%\odoo_db.dump" odoo17_db:/tmp/odoo_backup.dump
docker exec odoo17_db pg_restore -U %DB_USER% -d %DB_NAME% --no-owner -F c /tmp/odoo_backup.dump
docker exec odoo17_db rm /tmp/odoo_backup.dump

echo === Restoring filestore ===
docker run --rm -v odoo_deployment_ar_odoo_web_data:/data -v "%BACKUP_PATH%":/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/filestore.tar.gz -C /data"

echo === Starting Odoo app ===
docker start odoo17_app

echo.
echo === Restore complete! ===
echo Open: http://localhost:8069
pause
