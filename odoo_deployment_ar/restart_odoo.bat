@echo off
title Odoo Restart Script

echo Restarting Odoo...
cd /d %~dp0

docker compose restart odoo

echo.
echo Odoo restarted.
start http://localhost:8069

pause