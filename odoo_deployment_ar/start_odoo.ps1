# start_odoo.ps1 - Run this script to start Odoo correctly on Windows
# Usage: .\odoo_deployment_ar\start_odoo.ps1

$REPO    = "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default"
$ADDONS  = "$REPO\odoo_deployment_ar\addons"
$CONF_SRC= "$REPO\odoo_deployment_ar\odoo.conf"
$CONF_DIR= "C:\odoo_conf"
$NETWORK = "odoo_deployment_ar_odoo_net"
$VOLUME  = "odoo_deployment_ar_odoo_web_data"

Write-Host "=== Step 1: Copy odoo.conf to C:\odoo_conf\ ===" -ForegroundColor Cyan
if (!(Test-Path $CONF_DIR)) { New-Item -ItemType Directory -Path $CONF_DIR | Out-Null }
Copy-Item -Path $CONF_SRC -Destination "$CONF_DIR\odoo.conf" -Force
Write-Host "Done" -ForegroundColor Green

Write-Host "=== Step 2: Remove old container ===" -ForegroundColor Cyan
docker stop odoo17_app 2>$null
docker rm   odoo17_app 2>$null
Write-Host "Done" -ForegroundColor Green

Write-Host "=== Step 3: Start new Odoo container ===" -ForegroundColor Cyan
docker run -d `
  --name odoo17_app `
  --network $NETWORK `
  -e HOST=odoo17_db `
  -p 8069:8069 `
  -v "${CONF_DIR}:/etc/odoo" `
  -v "${ADDONS}:/mnt/extra-addons" `
  -v "${VOLUME}:/var/lib/odoo" `
  odoo:17.0

Start-Sleep -Seconds 5
$status = docker ps --filter "name=odoo17_app" --format "{{.Status}}"
if ($status) {
    Write-Host "=== Odoo is running! ===" -ForegroundColor Green
    Write-Host "Open: http://localhost:8069" -ForegroundColor Yellow
} else {
    Write-Host "=== Error - Logs: ===" -ForegroundColor Red
    docker logs odoo17_app --tail 20
}
