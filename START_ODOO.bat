@echo off
title Odoo Start Script

echo =====================================
echo Starting Odoo Environment...
echo =====================================

cd /d %~dp0

echo.
echo [1/4] Starting PostgreSQL and Odoo containers...
docker compose up -d

echo.
echo [2/4] Waiting for services to stabilize...
timeout /t 5 >nul

echo.
echo [3/4] Checking container status...
docker ps

echo.
echo [4/4] Opening Odoo in browser...
start http://localhost:8069

echo.
echo =====================================
echo Odoo should now be running
echo =====================================

echo.
echo Useful commands:
echo - View logs: docker logs -f odoo17_app
echo - Check DB: docker exec -it odoo17_db psql -U odoo -d odoo17
echo.
pause