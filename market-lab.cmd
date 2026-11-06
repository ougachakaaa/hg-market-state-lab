@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\market-lab.ps1" %*
if errorlevel 1 (
    echo.
    echo Market Lab command failed. See the messages above.
    pause
)
