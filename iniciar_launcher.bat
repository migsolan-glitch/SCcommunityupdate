@echo off
title Star Citizen Launcher
cd /d "%~dp0"

echo ========================================================
echo   Star Citizen - Launcher & Localization Manager
echo ========================================================
echo.

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Se ha producido un error al ejecutar el launcher.
    pause
)
