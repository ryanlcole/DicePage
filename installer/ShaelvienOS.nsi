; =============================================
; SHAELVIEN INSTALLER HEADER CONFIG – CLEAN
; =============================================
!define MUI_ICON "assets\favicon.ico"
!define MUI_UNICON "assets\favicon.ico"
!define MUI_ABORTWARNING
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\favicon.ico"
!define MUI_HEADERIMAGE_RIGHT
!define MUI_BRANDINGTEXT "ShaelvienOS Setup"

!include "MUI2.nsh"

;----------------------------------------
; GENERAL CONFIG
;----------------------------------------
Name "ShaelvienOS"
OutFile "..\${OUTFILE}"
InstallDir "$PROGRAMFILES\ShaelvienOS"
InstallDirRegKey HKLM "Software\ShaelvienOS" "Install_Dir"

BrandingText "ShaelvienOS — Helleaven Technologies"

;----------------------------------------
; INTERFACE SETTINGS (silences warnings)
;----------------------------------------
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\favicon.ico"
!define MUI_ABORTWARNING

!define MUI_HEADER_TEXT "Welcome to ShaelvienOS Installer"
!define MUI_HEADER_SUBTEXT "The Modular Fantasy-Driven System Core"
!define MUI_BRANDINGTEXT "Helleaven / Shaelvien Initiative"
!define MUI_HEADER_TEXT_FONT "Segoe UI"
!define MUI_HEADER_TEXT_COLOR "FFFFFF"

;----------------------------------------
; PAGES
;----------------------------------------
Page license
Page directory
Page instfiles
UninstPage instfiles

LicenseData "license.txt"

;----------------------------------------
; SECTIONS
;----------------------------------------
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File /r "..\dist\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\ShaelvienOS.lnk" "$INSTDIR\ShaelvienOS.exe"
  CreateShortCut "$SMPROGRAMS\ShaelvienOS\Uninstall ShaelvienOS.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\ShaelvienOS.exe"
  Delete "$DESKTOP\ShaelvienOS.lnk"
  Delete "$SMPROGRAMS\ShaelvienOS\Uninstall ShaelvienOS.lnk"
  RMDir /r "$INSTDIR"
SectionEnd
