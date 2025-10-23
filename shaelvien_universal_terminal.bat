@echo off
REM ================================================================
REM SHAELVIENOS UNIVERSAL TERMINAL (Phase 20.0)
REM Auto-detects and loads all available shells on Windows
REM ================================================================

title ShaelvienOS Universal Terminal
color 0A
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0portable" 2>nul

echo ------------------------------------------------------------
echo          S H A E L V I E N O S   T E R M I N A L
echo ------------------------------------------------------------

REM --- Detect system shells ---
set found_cmd=
set found_powershell=
set found_gitbash=
set found_vsdev=
set found_wsl=

where cmd >nul 2>&1 && set found_cmd=1
where powershell >nul 2>&1 && set found_powershell=1
where "C:\Program Files\Git\bin\bash.exe" >nul 2>&1 && set found_gitbash=1
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" set found_vsdev=1
where wsl >nul 2>&1 && set found_wsl=1

echo Available shells detected:
if defined found_cmd echo   [1] Command Prompt (cmd.exe)
if defined found_powershell echo   [2] PowerShell
if defined found_gitbash echo   [3] Git Bash
if defined found_vsdev echo   [4] Visual Studio Developer Prompt
if defined found_wsl echo   [5] WSL (Linux Subsystem)
echo   [X] Exit
echo ------------------------------------------------------------

REM --- Set up environment paths common to all ---
set "PYTHON_HOME=C:\Program Files\Python313"
set "RUST_HOME=%USERPROFILE%\.cargo\bin"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%RUST_HOME%"

echo Environment prepared:
python --version 2>nul
rustup --version 2>nul
echo ------------------------------------------------------------

:menu
set /p choice=Select terminal to launch (1-5 or X): 
if /i "%choice%"=="1" goto launch_cmd
if /i "%choice%"=="2" goto launch_powershell
if /i "%choice%"=="3" goto launch_gitbash
if /i "%choice%"=="4" goto launch_vsdev
if /i "%choice%"=="5" goto launch_wsl
if /i "%choice%"=="x" goto end
echo Invalid choice.
goto menu

:launch_cmd
if not defined found_cmd (
  echo [!] Command Prompt not found.
  goto menu
)
echo Launching Command Prompt...
start "Shaelvien CMD" cmd /k "cd /d %CD%"
goto menu

:launch_powershell
if not defined found_powershell (
  echo [!] PowerShell not found.
  goto menu
)
echo Launching PowerShell...
start "Shaelvien PowerShell" powershell -NoExit -Command "cd '%CD%'"
goto menu

:launch_gitbash
if not defined found_gitbash (
  echo [!] Git Bash not installed.
  goto menu
)
echo Launching Git Bash...
start "Shaelvien Git Bash" "C:\Program Files\Git\bin\bash.exe" --login -i -c "cd '%CD%'; exec bash"
goto menu

:launch_vsdev
if not defined found_vsdev (
  echo [!] Visual Studio Developer Tools not installed.
  goto menu
)
echo Launching Visual Studio Dev Prompt...
start "Shaelvien VSDev" cmd /k "call \"%VS_BUILD_TOOLS%\" && cd /d %CD%"
goto menu

:launch_wsl
if not defined found_wsl (
  echo [!] WSL not detected.
  goto menu
)
echo Launching WSL (Linux Subsystem)...
start "Shaelvien WSL" wsl
goto menu

:end
echo ------------------------------------------------------------
echo  Exiting Shaelvien Universal Terminal...
echo ------------------------------------------------------------
pause
endlocal
exit /b
