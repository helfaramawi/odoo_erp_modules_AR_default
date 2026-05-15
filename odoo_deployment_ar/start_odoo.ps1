# start_odoo.ps1 - Run this script to start Odoo correctly on Windows
# Usage: .\odoo_deployment_ar\start_odoo.ps1

$REPO    = "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default"
$ADDONS  = "$REPO\odoo_deployment_ar\addons"
$CONF_SRC= "$REPO\odoo_deployment_ar\odoo.conf"
$CONF_DST= "C:\odoo_conf\odoo.conf"
$NETWORK = "odoo_deployment_ar_odoo_net"
$VOLUME  = "odoo_deployment_ar_odoo_web_data"

Write-Host "=== Step 1: Copy odoo.conf to path without spaces ===" -ForegroundColor Cyan
if (!(Test-Path "C:\odoo_conf")) { New-Item -ItemType Directory -Path "C:\odoo_conf" | Out-Null }
Copy-Item -Path $CONF_SRC -Destination $CONF_DST -Force
Write-Host "Done: odoo.conf copied to C:\odoo_conf\" -ForegroundColor Green

Write-Host "=== Step 2: Remove old container ===" -ForegroundColor Cyan
docker stop odoo17_app 2>$null
docker rm   odoo17_app 2>$null
Write-Host "Done: old container removed" -ForegroundColor Green

Write-Host "=== Step 3: Start new Odoo container ===" -ForegroundColor Cyan
docker run -d `
  --name odoo17_app `
  --network $NETWORK `
  -e HOST=odoo17_db `
  -p 8069:8069 `
  -v "${CONF_DST}:/etc/odoo/odoo.conf" `
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
