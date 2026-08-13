@echo off
setlocal
title RESTART ODOO + AI AGENT

cd /d "%~dp0"

echo Restarting full environment...
call STOP_ALL.bat

timeout /t 5 /nobreak >nul

call START_ALL.bat
