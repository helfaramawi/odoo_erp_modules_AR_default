# ================================================================
# start_odoo.ps1 — اشغّل هذا السكريبت لتشغيل Odoo بشكل صحيح
# Usage: Right-click → Run with PowerShell
# ================================================================

$REPO = "C:\Users\SZ TECH\Downloads\odoo_erp_modules_AR_default"
$ADDONS = "$REPO\odoo_deployment_ar\addons"
$CONF_SRC = "$REPO\odoo_deployment_ar\odoo.conf"
$CONF_DST = "C:\odoo_conf\odoo.conf"
$NETWORK = "odoo_deployment_ar_odoo_net"
$VOLUME = "odoo_deployment_ar_odoo_web_data"

Write-Host "=== 1. سحب أحدث التغييرات من GitHub ===" -ForegroundColor Cyan
Set-Location $REPO
git pull origin claude/fix-module-55-visibility-oZHNF

Write-Host "=== 2. نسخ odoo.conf لمسار بدون مسافات ===" -ForegroundColor Cyan
if (!(Test-Path "C:\odoo_conf")) { New-Item -ItemType Directory -Path "C:\odoo_conf" | Out-Null }
Copy-Item -Path $CONF_SRC -Destination $CONF_DST -Force
Write-Host "تم نسخ odoo.conf إلى C:\odoo_conf\" -ForegroundColor Green

Write-Host "=== 3. إيقاف وحذف الـ container القديم ===" -ForegroundColor Cyan
docker stop odoo17_app 2>$null
docker rm odoo17_app 2>$null
Write-Host "تم حذف الـ container القديم" -ForegroundColor Green

Write-Host "=== 4. تشغيل Odoo container جديد ===" -ForegroundColor Cyan
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
    Write-Host "=== Odoo يعمل الآن! ===" -ForegroundColor Green
    Write-Host "افتح: http://localhost:8069" -ForegroundColor Yellow
} else {
    Write-Host "=== خطأ في التشغيل — السجلات: ===" -ForegroundColor Red
    docker logs odoo17_app --tail 20
}
