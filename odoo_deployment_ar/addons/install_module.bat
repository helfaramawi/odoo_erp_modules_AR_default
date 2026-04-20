@echo off
REM ================================
REM FIXED CONFIGURATION
REM ================================

set ODOO_PATH=C:\Program Files\Odoo 19.0.20251220\server
set PYTHON=C:\Program Files\Odoo 19.0.20251220\python\python.exe
set DB_NAME=odoo
set MODULE_NAME=x_warroom_d365_reverse_engineering
set CUSTOM_ADDONS=C:\custom_addons

echo ================================
echo Starting Odoo Module Installation
echo ================================

echo Python path: %PYTHON%
"%PYTHON%" -c "import passlib; print('passlib OK')"
if errorlevel 1 (
    echo ERROR: passlib not found in Odoo Python
    pause
    exit /b 1
)

REM الانتقال لمسار Odoo
cd /d "%ODOO_PATH%"

echo Current Directory:
cd

echo.
echo Running Odoo...

if exist odoo-bin.py (
    "%PYTHON%" odoo-bin.py ^
        -d %DB_NAME% ^
        -i %MODULE_NAME% ^
        --addons-path="%ODOO_PATH%\addons,%CUSTOM_ADDONS%" ^
        --log-level=debug
) else (
    "%PYTHON%" odoo-bin ^
        -d %DB_NAME% ^
        -i %MODULE_NAME% ^
        --addons-path="%ODOO_PATH%\addons,%CUSTOM_ADDONS%" ^
        --log-level=debug
)

echo.
echo ================================
echo DONE
echo ================================

pause