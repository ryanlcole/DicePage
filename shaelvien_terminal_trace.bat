@echo on
echo ===== SHAELVIEN TERMINAL TRACE =====
echo Batch file path: %~f0
echo Current directory before cd: %CD%

REM --- Try to move into this folder (the one the BAT file is in) ---
cd /d "%~dp0"
echo After cd: %CD%

set "PYTHON_HOME=C:\Program Files\Python313"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo VS tools path: %VS_BUILD_TOOLS%

if exist "%VS_BUILD_TOOLS%" (
  echo Calling VS environment...
  call "%VS_BUILD_TOOLS%"
) else (
  echo [WARN] Build tools not found. Will continue without them.
)

set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%"
echo PATH begins with:
echo %PATH%

echo.
echo READY.  Type these commands manually:
echo     "python shaelvien_daemon.py"
echo     "cl"   (to verify compiler visible)
echo.
pause
cmd /k
