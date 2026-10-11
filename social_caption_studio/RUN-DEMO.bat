@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Social Caption Generator - Odoo demo
cd /d "%~dp0"

echo ==========================================================
echo    Social Caption Generator  -  Odoo 17 demo
echo ==========================================================
echo.

rem ---------------------------------------------------------------
rem 0. Make sure we run from an extracted folder, not inside the zip
rem ---------------------------------------------------------------
if not exist "docker-compose.yml" goto :not_extracted
echo "%~dp0" | find /i "\AppData\Local\Temp\" >nul && goto :not_extracted

rem ---------------------------------------------------------------
rem 1. Menu (starts the demo automatically after 10 seconds)
rem ---------------------------------------------------------------
echo   [1] Start the demo          (default)
echo   [2] Stop the demo
echo   [3] Reset: delete demo data and start fresh
echo   [4] Show recent Odoo logs
echo.
choice /c 1234 /n /t 10 /d 1 /m "Choose 1, 2, 3 or 4 (starting in 10 seconds): "
set "ACTION=%errorlevel%"
echo.

rem ---------------------------------------------------------------
rem 2. Docker installed?
rem ---------------------------------------------------------------
where docker >nul 2>&1 && goto :docker_installed
echo [ERROR] Docker Desktop is not installed on this PC.
where winget >nul 2>&1 || goto :manual_install
choice /c YN /m "Install Docker Desktop now? It needs internet and admin approval"
if errorlevel 2 goto :manual_install
winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
echo.
echo When the installation finishes:
echo   1. Restart the PC.
echo   2. Open Docker Desktop once and accept its terms.
echo   3. Double-click RUN-DEMO.bat again.
goto :end_pause

:manual_install
start "" "https://www.docker.com/products/docker-desktop/"
echo Download and install Docker Desktop from the page that just opened,
echo restart the PC, then double-click RUN-DEMO.bat again.
goto :end_pause

:docker_installed
set "DC=docker compose"
docker compose version >nul 2>&1 || set "DC=docker-compose"

rem ---------------------------------------------------------------
rem 3. Docker running? Start Docker Desktop and wait up to 3 minutes
rem ---------------------------------------------------------------
docker info >nul 2>&1 && goto :engine_ok
echo Starting Docker Desktop, please wait...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if exist "%LOCALAPPDATA%\Docker\Docker Desktop.exe" start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe"
set /a TRIES=0
:wait_engine
timeout /t 5 /nobreak >nul
docker info >nul 2>&1 && goto :engine_ok
set /a TRIES+=1
<nul set /p "=."
if !TRIES! lss 36 goto :wait_engine
echo.
echo.
echo [ERROR] Docker Desktop did not finish starting.
echo     Look at the Docker Desktop window for a message. The usual causes are:
echo       - WSL is missing or outdated. This file can install or update it now.
echo       - Virtualization is turned off in the BIOS. Ask IT to enable "Intel VT-x" or "AMD-V".
echo       - Docker Desktop is waiting for you to accept its terms.
echo.
choice /c YN /m "Install or update WSL now? It needs admin approval and then a restart"
if errorlevel 2 goto :end_pause
powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c wsl --install --no-distribution & wsl --update & pause' -Verb RunAs"
echo After WSL finishes, restart the PC and double-click RUN-DEMO.bat again.
goto :end_pause

:engine_ok
echo [ok] Docker is running.
if "%ACTION%"=="2" goto :stop
if "%ACTION%"=="3" goto :reset
if "%ACTION%"=="4" goto :logs
goto :start

rem ---------------------------------------------------------------
rem Stop / Reset / Logs
rem ---------------------------------------------------------------
:stop
%DC% down
echo.
echo [ok] Demo stopped. Your data is kept for next time.
goto :end_pause

:reset
echo Deleting the demo database and starting fresh...
%DC% down -v
goto :start

:logs
%DC% logs --tail 80 odoo
goto :end_pause

rem ---------------------------------------------------------------
rem 4. Start: reuse the running port, or pick a free one (8069-8099)
rem ---------------------------------------------------------------
:start
set "PORT="
for /f "delims=" %%a in ('%DC% port odoo 8069 2^>nul') do if not defined PORT set "MAPPED=%%a" & set "PORT=!MAPPED:*:=!"
if defined PORT (
  echo [ok] The demo is already running on port !PORT!.
  goto :wait
)

set /a PORT=8069
:find_port
powershell -NoProfile -Command "try { $l = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Any, %PORT%); $l.Start(); $l.Stop(); exit 0 } catch { exit 1 }" >nul 2>&1 && goto :port_ok
echo [i] Port %PORT% is busy, trying the next one...
set /a PORT+=1
if %PORT% gtr 8099 goto :no_port
goto :find_port

:port_ok
> ".env" echo PORT=%PORT%
echo [ok] Using port %PORT%.
echo.
echo Starting Odoo. The first time downloads about 1 GB and can take several minutes...

:compose_up
%DC% up -d
if not errorlevel 1 goto :wait
echo.
echo [ERROR] Docker could not start the demo.
echo     The first start needs internet to download Odoo. Check the connection
echo     and free disk space - about 3 GB - then retry.
choice /c RQ /m "R = retry, Q = quit"
if errorlevel 2 goto :end_pause
goto :compose_up

rem ---------------------------------------------------------------
rem 5. Wait until Odoo answers, up to 5 minutes
rem ---------------------------------------------------------------
:wait
echo Waiting for Odoo to be ready
set /a TRIES=0
:wait_odoo
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 'http://localhost:%PORT%/web/login'; exit 0 } catch { exit 1 }" >nul 2>&1 && goto :ready
set /a TRIES+=1
<nul set /p "=."
if !TRIES! geq 60 goto :slow
timeout /t 5 /nobreak >nul
goto :wait_odoo

:slow
echo.
echo.
echo [ERROR] Odoo is taking longer than expected. Last log lines:
echo ----------------------------------------------------------
%DC% logs --tail 25 odoo
echo ----------------------------------------------------------
echo   W = wait 5 more minutes
echo   R = reset: delete demo data and start fresh - fixes most problems
echo   Q = quit
choice /c WRQ /m "Choose"
if errorlevel 3 goto :end_pause
if errorlevel 2 goto :reset
goto :wait

:ready
echo.
echo.
echo ==========================================================
echo    READY:   http://localhost:%PORT%
echo    Login:   admin
echo    Password: admin
echo    Open the "Social Captions" app.
echo ==========================================================
start "" "http://localhost:%PORT%"
echo.
echo To stop later: run RUN-DEMO.bat again and choose 2.
goto :end_pause

rem ---------------------------------------------------------------
rem Errors
rem ---------------------------------------------------------------
:not_extracted
echo [ERROR] Please extract the zip first:
echo     right-click social_caption_studio.zip, choose "Extract All",
echo     then open the extracted folder and double-click RUN-DEMO.bat.
goto :end_pause

:no_port
echo [ERROR] Ports 8069 to 8099 are all busy. Close other Odoo or web servers and try again.
goto :end_pause

:end_pause
echo.
pause
endlocal
