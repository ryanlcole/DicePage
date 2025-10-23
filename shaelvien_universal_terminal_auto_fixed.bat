@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0portable" 2>nul

title ShaelvienOS Terminal [Stable Build]
color 0A

set "LINE=------------------------------------------------------------"
set "TITLE= S H A E L V I E N O S   T E R M I N A L"

echo %LINE%
echo %TITLE%
echo %LINE%

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
python --version 2>nul
rustup --version 2>nul
echo %LINE%

REM --- Auto build nucleus ---
if exist nucleus.cpp (
    echo Building ShaelvienOS nucleus...
    call "%VS_BUILD_TOOLS%" >nul 2>&1
    cl /LD /EHsc /MD ^
       /I "%PYTHON_HOME%\Include" ^
       /I "%PYTHON_HOME%\Lib\site-packages\pybind11\include" ^
       nucleus.cpp "%PYTHON_HOME%\libs\python313.lib" ^
       /Fe:shaelvien_nucleus.pyd >nul 2>&1
    echo [OK] nucleus built.
) else (
    echo [WARN] nucleus.cpp not found.
)
echo %LINE%

REM --- Launch VS Developer Prompt (correct quoting) ---
if defined found_vsdev (
    echo Launching Visual Studio Developer Prompt...
    start "Shaelvien VSDev" cmd /k call ^"%VS_BUILD_TOOLS%^" ^&^& cd /d "%CD%"
)

REM --- Optional shells ---
if defined found_cmd (
    echo Launching CMD...
    start "Shaelvien CMD" cmd /k "cd /d %CD%"
)
if defined found_powershell (
    echo Launching PowerShell...
    start "Shaelvien PowerShell" powershell -NoExit -Command "cd '%CD%'"
)
if defined found_gitbash (
    echo Launching Git Bash...
    start "Shaelvien Git Bash" "C:\Program Files\Git\bin\bash.exe" --login -i -c "cd '%CD%'; exec bash"
)
if defined found_wsl (
    echo Launching WSL...
    start "Shaelvien WSL" wsl
)

echo %LINE%
echo ShaelvienOS multi-terminal session launched successfully.
echo Close this window if you wish; all shells are live.
echo %LINE%
pause
endlocal
exit /b
