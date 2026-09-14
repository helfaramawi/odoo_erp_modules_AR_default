@echo off

:: Generate timestamp
set datetime=%date:~-4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%
set datetime=%datetime: =0%

:: Create backup folder
mkdir backups 2>nul

:: Database backup
docker exec -t odoo17_db pg_dump -U odoo -d odoo17_db -Fc > backups\odoo_db_%datetime%.dump

:: Filestore backup
docker cp odoo17_app:/var/lib/odoo/.local/share/Odoo/filestore backups\filestore_%datetime%

echo Backup completed: %datetime%
pause