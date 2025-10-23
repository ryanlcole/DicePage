@echo off
setlocal
cd /d "%~dp0"
cd ..

REM --- Paths
set PORTABLE_DIR=%cd%
set DIST_EXE=%PORTABLE_DIR%\dist\ShaelvienOS.exe
set ICON=%PORTABLE_DIR%\assets\favicon.png
set STAGING=%PORTABLE_DIR%\installer\payload
set SED=%PORTABLE_DIR%\installer\setup_iexpress.sed
set OUT_INSTALLER=%PORTABLE_DIR%\installer\ShaelvienOS_Setup.exe

echo === Building ShaelvienOS one-file EXE ===
pyinstaller --noconfirm --onefile --noconsole --add-data "assets;assets" --add-data "logs;logs" --icon "%ICON%" --name "ShaelvienOS" "%PORTABLE_DIR%\shaelvien_launcher.py"
if ERRORLEVEL 1 goto :fail

if not exist "%DIST_EXE%" (
  echo Build failed: EXE not found.
  goto :fail
)

echo === Staging installer payload ===
rmdir /s /q "%STAGING%" 2>nul
mkdir "%STAGING%\assets"
mkdir "%STAGING%\logs"

copy "%DIST_EXE%" "%STAGING%\ShaelvienOS.exe" >nul
copy "%PORTABLE_DIR%\assets\favicon.png" "%STAGING%\assets\" >nul
if exist "%PORTABLE_DIR%\assets\favicon_bw.png" copy "%PORTABLE_DIR%\assets\favicon_bw.png" "%STAGING%\assets\" >nul

echo. > "%STAGING%\logs\README.txt"

echo === Building IExpress installer ===
pushd "%PORTABLE_DIR%\installer"
if exist "setup_iexpress.sed" (
    echo Running IExpress on "%cd%\setup_iexpress.sed"
    iexpress /N "setup_iexpress.sed"
) else (
    echo [ERROR] setup_iexpress.sed not found in %cd%
)
popd


echo === Creating Start Menu & Desktop shortcuts ===
powershell -ExecutionPolicy Bypass -File "%PORTABLE_DIR%\installer\install_shortcuts.ps1" "%OUT_INSTALLER%"

echo Done.
exit /b 0

:fail
echo FAILED
exit /b 1
