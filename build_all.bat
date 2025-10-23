@echo off
title ShaelvienOS Portable - Unified Build
color 0b

echo ============================================
echo     SHAELVIENOS PORTABLE - BUILD SYSTEM
echo ============================================
echo.

:: --- Check Python + PyInstaller ---
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not found. Please install it:
    echo     pip install pyinstaller
    pause
    exit /b
)

set BASE_DIR=%~dp0
cd /d "%BASE_DIR%"
set ASSETS="assets;assets"
set LOGS="logs;logs"

echo [INFO] Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
mkdir dist
mkdir build

echo.
echo [STEP 1/3] Building Shaelvien Daemon...
pyinstaller --noconfirm --onefile --noconsole ^
  --add-data %ASSETS% ^
  --add-data %LOGS% ^
  --hidden-import psutil ^
  --hidden-import shaelvien_ai_adapter ^
  --hidden-import glyph_core ^
  --name "shaelvien_daemon" shaelvien_daemon.py

echo.
echo [STEP 2/3] Building Shaelvien Tray...
pyinstaller --noconfirm --onefile --noconsole ^
  --add-data %ASSETS% ^
  --add-data %LOGS% ^
  --hidden-import psutil ^
  --hidden-import glyph_core ^
  --name "shaelvien_tray" shaelvien_tray.py

echo.
echo [STEP 3/3] Building Shaelvien Launcher...
pyinstaller --noconfirm --onefile ^
  --icon "assets\favicon.ico" ^
  --add-data %ASSETS% ^
  --add-data %LOGS% ^
  --hidden-import psutil ^
  --hidden-import pystray ^
  --hidden-import PIL.Image ^
  --hidden-import glyph_core ^
  --hidden-import shaelvien_ai_adapter ^
  --name "ShaelvienOS" shaelvien_launcher.py

echo.
echo ============================================
echo        BUILD COMPLETE! CHECK DIST/
echo ============================================

:: Optional: auto-copy EXEs into root dist
if exist dist\ShaelvienOS.exe echo [OK] Launcher built successfully.
if exist dist\shaelvien_daemon.exe echo [OK] Daemon built successfully.
if exist dist\shaelvien_tray.exe echo [OK] Tray built successfully.

echo.
pause
