@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0portable" 2>nul

title ShaelvienOS Terminal [Menu Mode]
color 0A

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

REM CMD detection
where cmd >nul 2>&1 && set found_cmd=1

REM PowerShell detection (checks modern + legacy)
if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" (
    set "found_powershell=%ProgramFiles%\PowerShell\7\pwsh.exe"
) else if exist "%ProgramFiles(x86)%\PowerShell\7\pwsh.exe" (
    set "found_powershell=%ProgramFiles(x86)%\PowerShell\7\pwsh.exe"
) else (
    for /f "delims=" %%P in ('where powershell.exe 2^>nul') do set "found_powershell=%%P"
)

REM Git Bash detection (checks full Git install + environment)
if exist "%ProgramFiles%\Git\bin\bash.exe" (
    set "found_gitbash=%ProgramFiles%\Git\bin\bash.exe"
) else if exist "%ProgramFiles%\Git\cmd\git.exe" (
    set "found_gitbash=%ProgramFiles%\Git\cmd\git.exe"
) else (
    for /f "delims=" %%G in ('where git.exe 2^>nul') do (
        set "found_gitbash=%%G"
    )
)

REM VSDev tools
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
    set "found_vsdev=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

REM WSL
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

REM --- Main menu loop ---
:menu
cls
color 0A
echo %LINE%
echo %TITLE%
echo %LINE%
echo  Select terminal or action:
echo.
if defined found_vsdev echo   [1] Visual Studio Developer Prompt
if defined found_cmd echo   [2] Command Prompt
if defined found_powershell echo   [3] PowerShell
if defined found_gitbash echo   [4] Git Bash
if defined found_wsl echo   [5] WSL
echo   [6] View build log
echo   [7] Rebuild nucleus
echo   [X] Exit
echo %LINE%
set /p CHOICE=Select an option: 

if /i "%CHOICE%"=="1" goto vsdev
if /i "%CHOICE%"=="2" goto cmd
if /i "%CHOICE%"=="3" goto ps
if /i "%CHOICE%"=="4" goto git
if /i "%CHOICE%"=="5" goto wsl
if /i "%CHOICE%"=="6" goto viewlog
if /i "%CHOICE%"=="7" goto rebuild
if /i "%CHOICE%"=="x" goto exit
goto menu

:vsdev
if not defined found_vsdev echo [!] VS Developer Prompt not found.& pause>nul&goto menu
echo Launching Visual Studio Developer Prompt...
start "Shaelvien VSDev" cmd /k call "%VS_BUILD_TOOLS%" ^&^& cd /d "%CD%"
goto menu

:cmd
if not defined found_cmd echo [!] CMD not found.& pause>nul&goto menu
echo Launching Command Prompt...
start "Shaelvien CMD" cmd /k "cd /d %CD%"
goto menu

:ps
if not defined found_powershell echo [!] PowerShell not found.& pause>nul&goto menu
echo Launching PowerShell...
start "Shaelvien PowerShell" "%found_powershell%" -NoExit -Command "cd '%CD%'"
goto menu

:git
if not defined found_gitbash echo [!] Git Bash not found.& pause>nul&goto menu
echo Launching Git...
if /i "%found_gitbash:~-8%"=="bash.exe" (
    start "Shaelvien Git Bash" "%found_gitbash%" --login -i -c "cd '%CD%'; exec bash"
) else (
    start "Shaelvien Git CLI" cmd /k "cd /d %CD% && \"%found_gitbash%\""
)
goto menu


:wsl
if not defined found_wsl echo [!] WSL not found.& pause>nul&goto menu
echo Launching WSL...
start "Shaelvien WSL" wsl
goto menu

:viewlog
if exist "%~dp0shaelvien_terminal.log" (
    start notepad "%~dp0shaelvien_terminal.log"
) else (
    echo [WARN] No log file found.
    pause
)
goto menu

:rebuild
echo [REBUILD] Compiling ShaelvienOS nucleus...
if exist nucleus.cpp (
    call "%VS_BUILD_TOOLS%" >nul 2>&1
    cl /LD /EHsc /MD ^
       /I "%PYTHON_HOME%\Include" ^
       /I "%PYTHON_HOME%\Lib\site-packages\pybind11\include" ^
       nucleus.cpp "%PYTHON_HOME%\libs\python313.lib" ^
       /Fe:shaelvien_nucleus.pyd >>"%~dp0shaelvien_terminal.log" 2>&1
    echo [OK] nucleus rebuilt successfully.
) else (
    echo [WARN] nucleus.cpp not found.
)
pause
goto menu

:exit
echo %LINE%
echo ShaelvienOS Terminal Menu closed manually.
echo %LINE%
pause
endlocal
exit /b
