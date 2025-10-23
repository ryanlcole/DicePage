@echo off
setlocal
set OUTPUT=ShaelvienOS_Setup.exe
set PAYLOAD=%~dp0payload
set INSTALLDIR=%ProgramFiles%\ShaelvienOS

echo [1/3] Packaging payload...
powershell -Command "Compress-Archive -Force '%PAYLOAD%\*' '%~dp0\ShaelvienOS_Payload.zip'"

echo [2/3] Creating self-extractor...
(
echo @echo off
echo echo Installing ShaelvienOS to "%INSTALLDIR%"...
echo powershell -Command "Expand-Archive -Force '%~dp0ShaelvienOS_Payload.zip' '%INSTALLDIR%'"
echo start "" "%INSTALLDIR%\ShaelvienOS.exe"
) > "%~dp0\stub.bat"

copy /b "%~dp0\stub.bat"+"%~dp0\ShaelvienOS_Payload.zip" "%~dp0%OUTPUT%"
del "%~dp0\stub.bat"
echo [3/3] Done.  Output: %OUTPUT%
pause
