@echo off
chcp 65001 >nul
title تشغيل نظام Odoo 17 - محافظة بورسعيد

color 1F
echo.
echo  ============================================================
echo   محافظة بورسعيد - نظام الادارة الحكومية
echo   Odoo 17 - Port Said Governorate ERP
echo  ============================================================
echo.

:: ── التحقق من تشغيل Docker ───────────────────────────────────
echo [1/5] جاري التحقق من Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo.
    echo  [خطأ] Docker Desktop غير مشغّل!
    echo  الرجاء تشغيل Docker Desktop أولاً ثم أعِد تشغيل هذا الملف.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker يعمل بشكل طبيعي

:: ── تشغيل قاعدة البيانات أولاً ──────────────────────────────
echo.
echo [2/5] جاري تشغيل قاعدة البيانات PostgreSQL...
docker start odoo17_db >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] فشل تشغيل قاعدة البيانات odoo17_db
    echo  تأكد أن الـ container موجود بالاسم: odoo17_db
    echo.
    pause
    exit /b 1
)
echo  [OK] PostgreSQL يعمل

:: ── انتظار استعداد PostgreSQL ────────────────────────────────
echo.
echo [3/5] انتظار استعداد قاعدة البيانات...
set /a wait=0
:wait_db
timeout /t 2 /nobreak >nul
set /a wait+=2
docker exec odoo17_db pg_isready -U odoo >nul 2>&1
if %errorlevel% neq 0 (
    if %wait% lss 30 (
        echo  انتظار... %wait% ثانية
        goto wait_db
    ) else (
        color 4F
        echo  [خطأ] قاعدة البيانات لم تستجب خلال 30 ثانية
        pause
        exit /b 1
    )
)
echo  [OK] PostgreSQL جاهز للاتصال

:: ── تشغيل تطبيق Odoo ─────────────────────────────────────────
echo.
echo [4/5] جاري تشغيل تطبيق Odoo...
docker start odoo17_app >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] فشل تشغيل Odoo
    echo  تأكد أن الـ container موجود بالاسم: odoo17_app
    echo.
    pause
    exit /b 1
)
echo  [OK] Odoo App بدأ التشغيل

:: ── انتظار استعداد Odoo ───────────────────────────────────────
echo.
echo [5/5] انتظار استعداد واجهة Odoo (قد يستغرق 30-60 ثانية)...
set /a wait=0
:wait_odoo
timeout /t 3 /nobreak >nul
set /a wait+=3
curl -s -o nul -w "%%{http_code}" http://localhost:8069/web/health 2>nul | findstr /C:"200" >nul 2>&1
if %errorlevel% neq 0 (
    if %wait% lss 120 (
        set /a dots=%wait%/3
        <nul set /p "=."
        goto wait_odoo
    ) else (
        echo.
        echo  [تحذير] لم يُستلَم رد من Odoo خلال 120 ثانية
        echo  سيُفتَح المتصفح على أي حال...
        goto open_browser
    )
)

echo.
echo  [OK] Odoo جاهز تماماً!

:open_browser
:: ── فتح المتصفح ──────────────────────────────────────────────
echo.
echo ============================================================
echo.
echo   النظام يعمل بنجاح!
echo.
echo   الرابط:      http://localhost:8069
echo   المستخدم:    admin
echo.
echo ============================================================
echo.
echo  جاري فتح المتصفح...
timeout /t 2 /nobreak >nul
start "" http://localhost:8069

echo.
echo  اضغط أي مفتاح لإغلاق هذه النافذة (النظام سيبقى يعمل)
pause >nul
exit /b 0
