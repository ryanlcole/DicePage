@echo off
setlocal enabledelayedexpansion
title ShaelvienOS Builder (Phase 7.5)

echo ===========================================
echo   Building ShaelvienOS Executables
echo ===========================================

:: 1️⃣ Detect Python automatically
for /f "tokens=*" %%I in ('where python 2^>nul') do (
    set PYEXE=%%I
    goto FoundPython
)
if exist "C:\Program Files\Python313\python.exe" set PYEXE="C:\Program Files\Python313\python.exe"
if exist "C:\Program Files (x86)\Python313\python.exe" set PYEXE="C:\Program Files (x86)\Python313\python.exe"
if not defined PYEXE (
    echo [FATAL] Could not locate Python. Please install or add to PATH.
    pause
    exit /b 1
)

:FoundPython
echo [INFO] Using Python: %PYEXE%
echo.

:: 2️⃣ Auto-version output filename
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
    set DATECODE=%%c-%%a-%%b
)
set BUILD_NAME=ShaelvienOS_Setup_%DATECODE%_v7.5.exe
echo [INFO] Build name: %BUILD_NAME%
echo.

:: 3️⃣ Run PyInstaller with safe call (handles spaces in paths)
call "%PYEXE%" -m PyInstaller ^
  --noconfirm --onefile --noconsole ^
  --icon "assets\favicon.ico" ^
  --add-data "assets;assets" ^
  --add-data "logs;logs" ^
  --hidden-import psutil ^
  --hidden-import pystray ^
  --hidden-import PIL.Image ^
  --name "ShaelvienOS" ^
  shaelvien_launcher.py

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo [SUCCESS] EXE build completed.
echo.

echo ===========================================
echo   Packaging with NSIS
echo ===========================================

set NSIS_PATH="C:\Program Files (x86)\NSIS\makensis.exe"
if exist %NSIS_PATH% (
    if exist "installer\ShaelvienOS.nsi" (
        echo [INFO] Running NSIS...
        %NSIS_PATH% /DOUTFILE="%BUILD_NAME%" "installer\ShaelvienOS.nsi"
        if %errorlevel% neq 0 (
            echo [ERROR] NSIS packaging failed.
            pause
            exit /b 1
        )
        echo [SUCCESS] NSIS installer built successfully.
    ) else (
        echo [WARN] NSIS script not found. Skipping installer step.
    )
) else (
    echo [WARN] NSIS not found at %NSIS_PATH%.
)

echo.
echo ===========================================
echo   Build & Packaging Complete
echo ===========================================
echo [INFO] Output: portable\%BUILD_NAME%
echo [INFO] Build completed successfully at %DATE% %TIME%
echo ===========================================
pause
exit /b 0
