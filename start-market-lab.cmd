@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-market-lab.ps1"
if errorlevel 1 (
    echo.
    echo Startup failed. See the messages above for details.
    pause
)
