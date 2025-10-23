@echo on
REM ^ enables full command echoing so we can see where it fails

echo -------------- SHAELVIEN DEBUG --------------
echo Current folder: %~dp0
cd /d "%~dp0" || (
    echo [ERROR] Portable folder not found!
    pause
    exit /b
)
echo Now in %CD%

set "PYTHON_HOME=C:\Program Files\Python313"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if exist "%VS_BUILD_TOOLS%" (
    echo Calling VS environment: %VS_BUILD_TOOLS%
    call "%VS_BUILD_TOOLS%"
) else (
    echo [WARN] Visual Studio Build Tools not found at expected path.
    echo [WARN] Compiler commands (cl) may not be available.
)

set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%"
echo PATH set to:
echo %PATH%
echo --------------------------------------------------

pause
echo Launching PowerShell session...
powershell -NoExit -Command "Write-Host 'ShaelvienOS terminal ready' -ForegroundColor Cyan; Write-Host 'Run: python shaelvien_daemon.py' -ForegroundColor Yellow"
pause
