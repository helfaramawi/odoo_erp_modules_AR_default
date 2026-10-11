@echo off
REM Social Caption Generator - start the demo (Windows). Double-click this file.
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker is not running. Open Docker Desktop, wait until it says "running", then try again.
  pause
  exit /b 1
)
echo Starting Odoo... the first time downloads about 1 GB and takes a few minutes.
docker compose up -d
if errorlevel 1 ( pause & exit /b 1 )
echo Waiting for Odoo to be ready...
:wait
timeout /t 3 /nobreak >nul
curl -s -o nul http://localhost:8069/web/login || goto wait
start http://localhost:8069
echo.
echo Ready: http://localhost:8069   login: admin   password: admin
pause
