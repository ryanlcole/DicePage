@echo off
REM ==============================================================
REM  SHAELVIENOS TERMINAL (Clean / Non-Admin / Defender-Safe)
REM ==============================================================

title ShaelvienOS Terminal
color 0A

REM --- Move to this directory ---
cd /d "%~dp0"
echo [INFO] Working directory: %CD%

REM --- Core environment paths ---
set "PYTHON_HOME=C:\Program Files\Python313"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

REM --- Load Visual Studio environment if available ---
if exist "%VS_BUILD_TOOLS%" (
    echo [INFO] Loading Visual Studio compiler environment...
    call "%VS_BUILD_TOOLS%" >nul
) else (
    echo [WARN] Build Tools not found at: %VS_BUILD_TOOLS%
)

REM --- Add Python 3.13 to PATH ---
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%"

cls
echo --------------------------------------------------
echo        SHAELVIENOS UNIFIED TERMINAL (CLEAN)
echo --------------------------------------------------
echo  Folder : %CD%
echo  Python : %PYTHON_HOME%
echo --------------------------------------------------
echo  Commands:
echo    build  - Rebuild shaelvien_nucleus.pyd
echo    run    - Launch shaelvien_daemon.py
echo    check  - Show current Python + compiler
echo    exit   - Close safely
echo --------------------------------------------------
echo.

:loop
set /p cmd=shaelvienOS^>
if /i "%cmd%"=="build" goto build
if /i "%cmd%"=="run" goto run
if /i "%cmd%"=="check" goto check
if /i "%cmd%"=="exit" goto end
echo Unknown command: %cmd%
goto loop

:build
echo [Building nucleus...]
cl /LD /EHsc /MD ^
   /I "%PYTHON_HOME%\Include" ^
   /I "%PYTHON_HOME%\Lib\site-packages\pybind11\include" ^
   nucleus.cpp "%PYTHON_HOME%\libs\python313.lib" ^
   /Fe:shaelvien_nucleus.pyd
echo [Build complete.]
goto loop

:run
echo [Launching daemon...]
"%PYTHON_HOME%\python.exe" shaelvien_daemon.py
echo [Daemon stopped.]
goto loop

:check
echo.
python --version
where cl
echo.
goto loop

:end
echo Exiting Shaelvien Terminal...
pause
exit /b
