@echo off
setlocal
set "target=%~dp0shaelvien_universal_terminal_final.bat"
set "icon=%~dp0portable\assets\shael_term.ico"
set "shortcut=%~dp0ShaelvienOS Terminal.lnk"

echo Creating shortcut...
powershell -NoProfile -ExecutionPolicy Bypass ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%shortcut%');" ^
  "$s.TargetPath='%target%';$s.IconLocation='%icon%';$s.WorkingDirectory='%~dp0';$s.Save()"
echo [OK] Shortcut created: %shortcut%
pause
endlocal
