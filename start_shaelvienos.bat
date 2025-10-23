@echo off
setlocal
title ShaelvienOS Portable Runtime
cd /d "%~dp0"

echo ==================================================
echo   Launching ShaelvienOS Portable Runtime
echo ==================================================

rem Activate the embedded environment
call ".\python\Scripts\activate.bat"

rem Start the launcher
python app_launcher.py

endlocal
pause
