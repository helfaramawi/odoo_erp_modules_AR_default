@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Demo Edition - start the Odoo + Postgres stack
REM
REM Always rebuilds the Odoo image before starting. This project's
REM Dockerfile COPYs the addons/ folder into the image at build time
REM (it is not a live bind-mount), so a plain "docker compose up -d"
REM or "docker compose restart" would keep serving whatever code was
REM baked in at the last build, silently ignoring any local edits or
REM git pulls since then. --build guarantees the running container
REM always matches what is on disk right now.
REM
REM Usage: run from anywhere; it locates demo_edition itself.
REM This window stays open (press a key to close) so you can always
REM read what happened, success or failure.
REM ============================================================

cd /d "%~dp0..\.."
if not exist docker\docker-compose.demo.yml (
    echo [ERROR] docker\docker-compose.demo.yml not found under %cd%.
    echo         This script must live at demo_edition\scripts\ops\.
    goto :end
)
if not exist .env (
    echo [ERROR] .env not found in %cd%.
    echo         Copy .env.example to .env and fill in DEMO_DB_PASSWORD / DEMO_USERS_PASSWORD first.
    goto :end
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker does not appear to be running. Start Docker Desktop and try again.
    goto :end
)

echo ============================================================
echo  Demo Edition - starting stack (rebuilding Odoo image) ...
echo ============================================================
docker compose --env-file .env -f docker\docker-compose.demo.yml up -d --build
if errorlevel 1 (
    echo [ERROR] docker compose up failed - see output above.
    goto :end
)

echo.
echo ============================================================
echo  Stack is up. Waiting a moment for Odoo to become healthy ...
echo ============================================================
timeout /t 5 /nobreak >nul
docker compose --env-file .env -f docker\docker-compose.demo.yml ps

echo.
echo Done. Open the app in your browser (check DEMO_HTTP_PORT in .env, default 8069).

:end
echo.
pause
endlocal
