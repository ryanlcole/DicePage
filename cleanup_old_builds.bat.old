@echo off
title ShaelvienOS Cleanup Utility
color 0a
echo ============================================================
echo      ShaelvienOS Portable - Cleanup Utility
echo ============================================================
echo.
echo This will remove old build files, temp folders, and caches.
echo Core project files and assets WILL be preserved.
echo.
pause

REM === Navigate to current script directory ===
cd /d "%~dp0"

echo.
echo [1/7] Removing PyInstaller build folders...
rmdir /s /q build 2>nul
rmdir /s /q __pycache__ 2>nul

echo [2/7] Removing PyInstaller spec files...
del /f /q *.spec 2>nul

echo [3/7] Removing old dist folder contents except latest EXE...
for %%F in (dist\*.exe) do (
    echo Keeping %%~nxF
)
for /f "skip=1 delims=" %%A in ('dir /b /o-d dist\*.exe 2^>nul') do (
    del /f /q "dist\%%A"
)

echo [4/7] Removing installer payload (it will be rebuilt later)...
rmdir /s /q installer\payload 2>nul

echo [5/7] Cleaning logs directory (keeping folder structure)...
del /f /q logs\*.* 2>nul

echo [6/7] Deleting temporary cache and hidden files...
del /f /q *.log 2>nul
del /f /q *.tmp 2>nul
del /f /q desktop.ini 2>nul

echo [7/7] Done!
echo ============================================================
echo ✅ ShaelvienOS environment is clean and ready for rebuild.
echo ============================================================
pause
exit
