@echo off
setlocal

set BACKUP_DIR=C:\Users\SZ TECH\Downloads\odoo_backups
set DB_NAME=odoo17_db
set DB_USER=odoo
set DB_PASS=odoo_secure_pass
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_PATH=%BACKUP_DIR%\backup_%TIMESTAMP%

echo === Creating backup folder ===
mkdir "%BACKUP_PATH%"

echo === Stopping Odoo app ===
docker stop odoo17_app

echo === Dumping database ===
docker exec odoo17_db pg_dump -U %DB_USER% -d %DB_NAME% -F c -f /tmp/odoo_backup.dump
docker cp odoo17_db:/tmp/odoo_backup.dump "%BACKUP_PATH%\odoo_db.dump"
docker exec odoo17_db rm /tmp/odoo_backup.dump

echo === Backing up filestore ===
docker run --rm -v odoo_deployment_ar_odoo_web_data:/data -v "%BACKUP_PATH%":/backup alpine tar czf /backup/filestore.tar.gz -C /data .

echo === Starting Odoo app ===
docker start odoo17_app

echo.
echo === Backup complete! ===
echo Location: %BACKUP_PATH%
echo Files: odoo_db.dump + filestore.tar.gz
pause
