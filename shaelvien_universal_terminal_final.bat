@echo off
REM ================================================================
REM   SHAELVIENOS UNIVERSAL TERMINAL  —  Phase 20.0 Final Build
REM ================================================================
REM Includes:
REM  • Retro blinking cursor
REM  • Icon (shael_term.ico)
REM  • PowerShell-safe menu
REM  • VSDev + CMD + PowerShell + GitBash + WSL launcher
REM ================================================================

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0portable" 2>nul

title ShaelvienOS Terminal [Final]
color 0A

REM --- Apply the terminal icon (requires Windows 10+ shortcut support) ---
if exist "%~dp0assets\shael_term.ico" (
    powershell -NoProfile -Command ^
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%~dp0\shaelvien_universal_terminal_final.lnk');" ^
        "$s.TargetPath='%~f0';$s.IconLocation='%~dp0assets\\shael_term.ico';$s.Save()" >nul 2>&1
)

REM --- Retro cursor blink control ---
for /f "delims=" %%C in ('echo prompt $H ^| cmd') do set "BS=%%C"
echo %BS%|set /p=""

set "LINE=------------------------------------------------------------"
set "TITLE= S H A E L V I E N O S   T E R M I N A L"

echo %LINE%
echo %TITLE%
echo %LINE%
echo [INFO] Initializing environment...
echo %DATE% %TIME% > "%~dp0shaelvien_terminal.log"

REM --- Detect shells safely ---
set found_cmd=
set found_powershell=
set found_gitbash=
set found_vsdev=
set found_wsl=

where cmd >nul 2>&1 && set found_cmd=1
where powershell >nul 2>&1 && set found_powershell=1
where "C:\Program Files\Git\bin\bash.exe" >nul 2>&1 && set found_gitbash=1
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
    set "found_vsdev=1"
)
where wsl >nul 2>&1 && set found_wsl=1

REM --- Environment injection ---
set "PYTHON_HOME=C:\Program Files\Python313"
set "RUST_HOME=%USERPROFILE%\.cargo\bin"
set "VS_BUILD_TOOLS=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%RUST_HOME%"

echo Detected environment:
python --version 2>>"%~dp0shaelvien_terminal.log"
rustup --version 2>>"%~dp0shaelvien_terminal.log"
echo %LINE%

REM --- Auto build nucleus ---
if exist nucleus.cpp (
    echo [BUILD] Compiling ShaelvienOS nucleus...
    call "%VS_BUILD_TOOLS%" >nul 2>&1
    cl /LD /EHsc /MD ^
       /I "%PYTHON_HOME%\Include" ^
       /I "%PYTHON_HOME%\Lib\site-packages\pybind11\include" ^
       nucleus.cpp "%PYTHON_HOME%\libs\python313.lib" ^
       /Fe:shaelvien_nucleus.pyd >>"%~dp0shaelvien_terminal.log" 2>&1
    echo [OK] nucleus built.
) else (
    echo [WARN] nucleus.cpp not found.
)
echo %LINE%

REM --- Launch sequence ---
:mainloop
echo Launching environment shells...
if defined found_vsdev (
    echo [+] VS Developer Prompt
    start "Shaelvien VSDev" cmd /k call "%VS_BUILD_TOOLS%" ^&^& cd /d "%CD%"
)
if defined found_cmd (
    echo [+] CMD
    start "Shaelvien CMD" cmd /k "cd /d %CD%"
)
if defined found_powershell (
    echo [+] PowerShell
    start "Shaelvien PowerShell" powershell -NoExit -Command "cd '%CD%'"
)
if defined found_gitbash (
    echo [+] Git Bash
    start "Shaelvien Git Bash" "C:\Program Files\Git\bin\bash.exe" --login -i -c "cd '%CD%'; exec bash"
)
if defined found_wsl (
    echo [+] WSL
    start "Shaelvien WSL" wsl
)

echo %LINE%
echo All terminals launched successfully.
echo Log: "%~dp0shaelvien_terminal.log"
echo %LINE%
echo.

REM === PowerShell-safe input loop ===
set /p MENU=[R] Relaunch  [V] View log  [X] Exit  ^> 
if /i "%MENU%"=="R" goto mainloop
if /i "%MENU%"=="V" start notepad "%~dp0shaelvien_terminal.log" & goto mainloop
if /i "%MENU%"=="X" goto exit
goto mainloop

:exit
echo %LINE%
echo ShaelvienOS Terminal Final session closed manually.
echo %LINE%
pause
endlocal
exit /b
