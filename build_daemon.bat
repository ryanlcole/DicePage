@echo off
cd /d "%~dp0"
pyinstaller --noconfirm --onefile --noconsole ^
 --add-data "hud;hud" ^
 --add-data "glyph_core.py;." ^
 --add-data "relic_core.py;." ^
 --add-data "shaelvien_tray.py;." ^
 --icon "assets\\favicon.png" ^
 --name "ShaelvienOS_Portable" shaelvien_daemon.py
pause
