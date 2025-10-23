@echo off
set APP_PATH="%~dp0ShaelvienOS.exe"
set SHORTCUT_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\ShaelvienOS
mkdir "%SHORTCUT_DIR%" 2>nul
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('C:\Users\Local User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\ShaelvienOS\ShaelvienOS.lnk');$s.TargetPath='';$s.IconLocation='';$s.Save()"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('C:\Users\Local User\Desktop\ShaelvienOS.lnk');$s.TargetPath='';$s.IconLocation='';$s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell;$sc = $ws.CreateShortcut('C:\Users\Local User\AppData\Roaming\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\ShaelvienOS.lnk');$sc.TargetPath='';$sc.IconLocation='';$sc.Save()"
echo [INFO] Shortcuts created successfully!
