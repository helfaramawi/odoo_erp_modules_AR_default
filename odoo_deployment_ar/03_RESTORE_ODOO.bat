@echo off
chcp 65001 >nul
title استعادة النسخة الاحتياطية - Odoo 17 - محافظة بورسعيد

color 1F
echo.
echo  ============================================================
echo   استعادة النسخة الاحتياطية - محافظة بورسعيد
echo   Odoo 17 Restore - Database + Addons + Config
echo  ============================================================
echo.

:: ── تحذير مهم ────────────────────────────────────────────────
color 4F
echo  ============================================================
echo   تحذير هام
echo  ============================================================
echo.
echo   هذه العملية ستحذف قاعدة البيانات الحالية
echo   وتستبدلها بالنسخة الاحتياطية المختارة.
echo.
echo   لا يمكن التراجع عن هذه العملية بعد البدء!
echo.
echo  ============================================================
echo.
color 1F
set /p CONFIRM=هل أنت متأكد؟ اكتب YES للمتابعة أو أي شيء آخر للإلغاء: 
if /i not "%CONFIRM%"=="YES" (
    echo.
    echo  تم الإلغاء. لم يتغير شيء.
    pause
    exit /b 0
)

:: ── اختيار مجلد النسخة ───────────────────────────────────────
echo.
echo  ============================================================
echo   النسخ الاحتياطية المتاحة في مجلد backups:
echo  ============================================================
echo.
set BACKUP_ROOT=%~dp0backups
if not exist "%BACKUP_ROOT%" (
    color 4F
    echo  [خطأ] مجلد backups غير موجود في نفس مسار هذا الملف!
    echo  المسار المتوقع: %BACKUP_ROOT%
    echo.
    pause
    exit /b 1
)

:: عرض النسخ المتاحة
set /a COUNT=0
for /d %%D in ("%BACKUP_ROOT%\backup_*") do (
    set /a COUNT+=1
    echo   [!COUNT!] %%~nD
)

if %COUNT%==0 (
    color 4F
    echo  [خطأ] لا توجد نسخ احتياطية في المجلد: %BACKUP_ROOT%
    echo  شغّل 02_BACKUP_ODOO.bat أولاً لإنشاء نسخة.
    pause
    exit /b 1
)

echo.
echo  ملاحظة: النسخة الأحدث هي الأعلى في القائمة.
echo.
set /p CHOICE=اكتب رقم النسخة المطلوبة: 

:: الحصول على مسار النسخة المختارة
set /a IDX=0
set SELECTED_DIR=
for /d %%D in ("%BACKUP_ROOT%\backup_*") do (
    set /a IDX+=1
    if !IDX!==%CHOICE% set SELECTED_DIR=%%D
)

if "%SELECTED_DIR%"=="" (
    color 4F
    echo  [خطأ] رقم غير صحيح. يجب أن يكون بين 1 و%COUNT%
    pause
    exit /b 1
)

echo.
echo  النسخة المختارة: %SELECTED_DIR%
echo.

:: التحقق من وجود ملف قاعدة البيانات
set DB_FILE=
for %%F in ("%SELECTED_DIR%\database_*.dump") do set DB_FILE=%%F
if "%DB_FILE%"=="" (
    color 4F
    echo  [خطأ] لم يُعثَر على ملف قاعدة البيانات في هذه النسخة!
    pause
    exit /b 1
)
echo  ملف قاعدة البيانات: %DB_FILE%
echo.

:: ── التحقق من Docker ──────────────────────────────────────────
echo [1/7] التحقق من Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] Docker Desktop غير مشغّل!
    pause
    exit /b 1
)
echo  [OK] Docker يعمل

:: ── تشغيل قاعدة البيانات ─────────────────────────────────────
echo.
echo [2/7] تشغيل قاعدة البيانات...
docker start odoo17_db >nul 2>&1
timeout /t 5 /nobreak >nul
docker exec odoo17_db pg_isready -U odoo >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] قاعدة البيانات لم تستجب
    pause
    exit /b 1
)
echo  [OK] PostgreSQL يعمل

:: ── إيقاف تطبيق Odoo مؤقتاً ─────────────────────────────────
echo.
echo [3/7] إيقاف تطبيق Odoo مؤقتاً...
docker stop odoo17_app >nul 2>&1
echo  [OK] تم إيقاف Odoo

:: ── حذف قاعدة البيانات القديمة ──────────────────────────────
echo.
echo [4/7] حذف قاعدة البيانات القديمة...
docker exec odoo17_db psql -U odoo -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='odoo17_db';" >nul 2>&1
docker exec odoo17_db dropdb -U odoo --if-exists odoo17_db >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] فشل حذف قاعدة البيانات القديمة
    echo  سيتم إعادة تشغيل Odoo...
    docker start odoo17_app >nul 2>&1
    pause
    exit /b 1
)
echo  [OK] تم حذف قاعدة البيانات القديمة

:: ── إنشاء قاعدة بيانات جديدة ────────────────────────────────
echo.
echo [5/7] إنشاء قاعدة بيانات جديدة...
docker exec odoo17_db createdb -U odoo odoo17_db >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo  [خطأ] فشل إنشاء قاعدة البيانات الجديدة
    pause
    exit /b 1
)
echo  [OK] تم إنشاء قاعدة بيانات فارغة

:: ── استعادة قاعدة البيانات ───────────────────────────────────
echo.
echo [6/7] جاري استعادة قاعدة البيانات...
echo  هذا قد يستغرق عدة دقائق حسب حجم البيانات...
docker exec -i odoo17_db pg_restore -U odoo -d odoo17_db < "%DB_FILE%"
if %errorlevel% neq 0 (
    echo  [تحذير] pg_restore أعطى تحذيرات - هذا طبيعي في بعض الأحيان
    echo  جاري التحقق من قاعدة البيانات...
    docker exec odoo17_db psql -U odoo -d odoo17_db -c "SELECT COUNT(*) FROM ir_module_module;" >nul 2>&1
    if %errorlevel% neq 0 (
        color 4F
        echo  [خطأ] قاعدة البيانات تالفة بعد الاستعادة!
        pause
        exit /b 1
    )
)
echo  [OK] تم استعادة قاعدة البيانات

:: ── استعادة الـ Addons ────────────────────────────────────────
echo.
echo [7/7] استعادة ملفات الـ Addons والإعداد...
if exist "%SELECTED_DIR%\addons" (
    docker cp "%SELECTED_DIR%\addons" odoo17_app:/mnt/extra-addons >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [تحذير] لم يتم استعادة الـ Addons تلقائياً
        echo  يمكنك نسخها يدوياً من: %SELECTED_DIR%\addons
    ) else (
        echo  [OK] تم استعادة الـ Addons
    )
) else (
    echo  [تحذير] مجلد الـ Addons غير موجود في هذه النسخة
)

:: استعادة ملف الإعداد
if exist "%SELECTED_DIR%\odoo.conf" (
    docker cp "%SELECTED_DIR%\odoo.conf" odoo17_app:/etc/odoo/odoo.conf >nul 2>&1
    echo  [OK] تم استعادة ملف الإعداد
)

:: استعادة الـ Filestore
if exist "%SELECTED_DIR%\filestore" (
    docker cp "%SELECTED_DIR%\filestore" odoo17_app:/var/lib/odoo/filestore >nul 2>&1
    echo  [OK] تم استعادة الـ Filestore
)

:: ── إعادة تشغيل Odoo ─────────────────────────────────────────
echo.
echo  إعادة تشغيل تطبيق Odoo...
docker start odoo17_app >nul 2>&1
echo  [OK] تم تشغيل Odoo

:: ── انتظار جاهزية Odoo ───────────────────────────────────────
echo.
echo  انتظار جاهزية النظام (قد يستغرق 60 ثانية)...
set /a wait=0
:wait_odoo
timeout /t 3 /nobreak >nul
set /a wait+=3
curl -s -o nul -w "%%{http_code}" http://localhost:8069/web/health 2>nul | findstr /C:"200" >nul 2>&1
if %errorlevel% neq 0 (
    if %wait% lss 120 (
        <nul set /p "=."
        goto wait_odoo
    )
)
echo.

:: ── ملخص النهاية ─────────────────────────────────────────────
color 2F
echo.
echo  ============================================================
echo.
echo   تمت الاستعادة بنجاح!
echo.
echo   النسخة المُستعادة: %SELECTED_DIR%
echo   الرابط: http://localhost:8069
echo.
echo  ============================================================
echo.
echo  جاري فتح المتصفح...
timeout /t 2 /nobreak >nul
start "" http://localhost:8069

pause
exit /b 0
