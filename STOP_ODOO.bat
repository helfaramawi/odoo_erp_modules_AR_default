@echo off
title Odoo Stop Script

echo =====================================
echo Stopping Odoo Environment...
echo =====================================

cd /d %~dp0

echo.
echo [1/2] Stopping containers...
docker compose down

echo.
echo [2/2] Verifying shutdown...
docker ps

echo.
echo =====================================
echo Odoo stopped successfully
echo =====================================

echo.
echo Notes:
echo - Database is preserved (volumes not deleted)
echo - To remove DB: docker compose down -v
echo.
pause