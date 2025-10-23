@echo off
REM ==============================================================
REM SHAELVIENOS TERMINAL (failsafe version – never auto-closes)
REM ==============================================================

title ShaelvienOS Terminal [Failsafe]

REM --- Move into this directory ---
cd /d "%~dp0portable"
if errorlevel 1 (
    echo [ERROR] Could not change directory to portable.
    echo Current path: %CD%
    pause
    goto end
)

REM --- Setup paths ---
set "PYTHON_HOME=C:\Program Files\Python313"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

REM --- Load MSVC environment if present ---
if exist "%VS_BUILD_TOOLS%" (
    echo [INFO] Loading Visual Studio environment...
    call "%VS_BUILD_TOOLS%"
) else (
    echo [WARN] Visual Studio Build Tools not found at:
    echo        %VS_BUILD_TOOLS%
    echo        You can still run Python, but not recompile.
)

REM --- Add Python 3.13 to PATH ---
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%"

cls
echo --------------------------------------------------
echo     SHAELVIENOS UNIFIED TERMINAL [SAFE MODE]
echo --------------------------------------------------
echo  Folder : %CD%
echo  Python : %PYTHON_HOME%
echo --------------------------------------------------
echo  Type one of the following:
echo    build  - rebuild nucleus DLL
echo    run    - start daemon
echo    check  - show current Python and compiler
echo    exit   - close safely
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
