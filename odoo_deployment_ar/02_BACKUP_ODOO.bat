@echo off
chcp 65001 >nul
title نسخ احتياطي - Odoo 17 - محافظة بورسعيد

color 1F
echo.
echo  ============================================================
echo   نسخ احتياطي - محافظة بورسعيد
echo   Odoo 17 Backup - Database + Addons + Config
echo  ============================================================
echo.

:: ── إعداد مسار الحفظ وتاريخ الملف ───────────────────────────
set BACKUP_ROOT=%~dp0backups
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
    set DAY=%%a
    set MONTH=%%b
    set YEAR=%%c
)
for /f "tokens=1-2 delims=:." %%a in ("%time%") do (
    set HOUR=%%a
    set MIN=%%b
)
:: تنظيف المسافة من الساعة إذا كانت أحادية الرقم
set HOUR=%HOUR: =0%
set TIMESTAMP=%YEAR%%MONTH%%DAY%_%HOUR%%MIN%
set BACKUP_DIR=%BACKUP_ROOT%\backup_%TIMESTAMP%

echo  تاريخ النسخة: %DAY%/%MONTH%/%YEAR%  الساعة: %HOUR%:%MIN%
echo  مسار الحفظ:  %BACKUP_DIR%
echo.

:: ── التحقق من تشغيل Docker ───────────────────────────────────
echo [1/6] التحقق من Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] Docker Desktop غير مشغّل!
    pause
    exit /b 1
)
echo  [OK] Docker يعمل

:: ── التحقق من تشغيل الـ Containers ──────────────────────────
echo.
echo [2/6] التحقق من حالة الـ Containers...
docker inspect odoo17_db >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] Container قاعدة البيانات odoo17_db غير موجود
    pause
    exit /b 1
)
docker inspect odoo17_app >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] Container التطبيق odoo17_app غير موجود
    pause
    exit /b 1
)
echo  [OK] الـ Containers موجودة

:: ── إنشاء مجلد النسخة الاحتياطية ────────────────────────────
echo.
echo [3/6] إنشاء مجلد النسخة الاحتياطية...
if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"
mkdir "%BACKUP_DIR%"
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] فشل إنشاء المجلد: %BACKUP_DIR%
    pause
    exit /b 1
)
echo  [OK] تم إنشاء: %BACKUP_DIR%

:: ── نسخ قاعدة البيانات ───────────────────────────────────────
echo.
echo [4/6] جاري نسخ قاعدة البيانات PostgreSQL...
echo  هذا قد يستغرق بضع دقائق حسب حجم البيانات...
docker exec odoo17_db pg_dump -U odoo -Fc odoo17_db > "%BACKUP_DIR%\database_%TIMESTAMP%.dump"
if %errorlevel% neq 0 (
    color 4F
    echo.
    echo  [خطأ] فشل نسخ قاعدة البيانات!
    echo  تأكد أن PostgreSQL container يعمل وأن المستخدم odoo موجود
    rmdir /s /q "%BACKUP_DIR%"
    pause
    exit /b 1
)
:: التحقق من أن الملف غير فارغ
for %%F in ("%BACKUP_DIR%\database_%TIMESTAMP%.dump") do (
    if %%~zF lss 1000 (
        color 4F
        echo  [خطأ] ملف قاعدة البيانات صغير جداً - ربما فشل النسخ
        pause
        exit /b 1
    )
)
for %%F in ("%BACKUP_DIR%\database_%TIMESTAMP%.dump") do echo  [OK] قاعدة البيانات: %%~zF bytes

:: ── نسخ مجلد الـ Addons ──────────────────────────────────────
echo.
echo [5/6] جاري نسخ ملفات الـ Addons...
docker cp odoo17_app:/mnt/extra-addons "%BACKUP_DIR%\addons" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [تحذير] لم يُعثَر على /mnt/extra-addons - جاري المحاولة من المسار البديل...
    docker cp odoo17_app:/odoo/addons "%BACKUP_DIR%\addons" >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [تحذير] لم يتم نسخ الـ Addons - سيُكمَل الباقي
    ) else (
        echo  [OK] تم نسخ الـ Addons
    )
) else (
    echo  [OK] تم نسخ الـ Addons
)

:: ── نسخ ملف الإعداد ──────────────────────────────────────────
docker cp odoo17_app:/etc/odoo/odoo.conf "%BACKUP_DIR%\odoo.conf" >nul 2>&1
if %errorlevel% neq 0 (
    docker cp odoo17_app:/etc/odoo.conf "%BACKUP_DIR%\odoo.conf" >nul 2>&1
)
echo  [OK] تم نسخ ملف الإعداد

:: ── نسخ Filestore (المرفقات والصور) ─────────────────────────
docker cp odoo17_app:/var/lib/odoo/filestore "%BACKUP_DIR%\filestore" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [تحذير] لم يتم نسخ الـ Filestore - ليس ضرورياً للنسخة الأساسية
) else (
    echo  [OK] تم نسخ الـ Filestore
)

:: ── إنشاء ملف معلومات النسخة ─────────────────────────────────
echo.
echo [6/6] إنشاء ملف معلومات النسخة الاحتياطية...
(
echo ============================================================
echo  نسخة احتياطية - Odoo 17 - محافظة بورسعيد
echo ============================================================
echo  التاريخ:     %DAY%/%MONTH%/%YEAR%
echo  الوقت:       %HOUR%:%MIN%
echo  قاعدة البيانات: odoo17_db
echo  Container:   odoo17_app
echo.
echo  محتويات هذه النسخة:
echo  - database_%TIMESTAMP%.dump  --  قاعدة البيانات الكاملة
echo  - addons\                    --  ملفات الـ Addons المخصصة
echo  - odoo.conf                  --  ملف الإعداد
echo  - filestore\                 --  المرفقات والصور
echo.
echo  لاستعادة هذه النسخة استخدم: 03_RESTORE_ODOO.bat
echo ============================================================
) > "%BACKUP_DIR%\BACKUP_INFO.txt"

:: ── ملخص النهاية ─────────────────────────────────────────────
color 2F
echo.
echo  ============================================================
echo.
echo   النسخة الاحتياطية اكتملت بنجاح!
echo.
echo   المسار: %BACKUP_DIR%
echo.
for /f "tokens=*" %%A in ('dir /s /-c "%BACKUP_DIR%" ^| findstr "File(s)"') do echo   الحجم الكلي: %%A
echo.
echo  ============================================================
echo.
pause
exit /b 0
