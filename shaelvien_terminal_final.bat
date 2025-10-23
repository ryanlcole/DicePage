@echo off
REM ==============================================================
REM  SHAELVIENOS TERMINAL (Final – auto-detect path, never closes)
REM ==============================================================

title ShaelvienOS Terminal [Final]

REM --- Determine working folder ---
cd /d "%~dp0"
echo [INFO] Current directory: %CD%

REM --- Environment paths ---
set "PYTHON_HOME=C:\Program Files\Python313"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

REM --- Load MSVC environment if available ---
if exist "%VS_BUILD_TOOLS%" (
    echo [INFO] Loading Visual Studio compiler environment...
    call "%VS_BUILD_TOOLS%" >nul
) else (
    echo [WARN] Build Tools not found at: %VS_BUILD_TOOLS%
    echo [WARN] You can still run Python, but cannot compile.
)

REM --- Add Python 3.13 to PATH ---
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%"

cls
echo --------------------------------------------------
echo        SHAELVIENOS UNIFIED TERMINAL
echo --------------------------------------------------
echo  Working directory : %CD%
echo  Python home       : %PYTHON_HOME%
echo --------------------------------------------------
echo  Commands:
echo    build  - Rebuild shaelvien_nucleus.pyd
echo    run    - Launch shaelvien_daemon.py
echo    check  - Show current Python and compiler
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
