@echo off
cd /d "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default\odoo_deployment_ar"
echo === Stopping old containers ===
docker-compose down
echo === Starting Odoo ===
docker-compose up -d
timeout /t 8
docker ps --filter "name=odoo17_app"
echo.
echo === Open: http://localhost:8069 ===
pause
