# start_odoo.ps1 - Run this script to start Odoo correctly on Windows
# Usage: cd "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default\odoo_deployment_ar"
#        docker-compose up -d

$DEPLOY_DIR = "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default\odoo_deployment_ar"

Write-Host "=== Stopping old containers ===" -ForegroundColor Cyan
Set-Location $DEPLOY_DIR
docker-compose down
Write-Host "Done" -ForegroundColor Green

Write-Host "=== Starting Odoo with docker-compose ===" -ForegroundColor Cyan
docker-compose up -d

Start-Sleep -Seconds 8
$status = docker ps --filter "name=odoo17_app" --format "{{.Status}}"
if ($status) {
    Write-Host "=== Odoo is running! ===" -ForegroundColor Green
    Write-Host "Open: http://localhost:8069" -ForegroundColor Yellow
} else {
    Write-Host "=== Error - Logs: ===" -ForegroundColor Red
    docker logs odoo17_app --tail 30
}
