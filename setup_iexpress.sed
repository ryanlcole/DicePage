[Version]
Class=IEXPRESS
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=1
CAB_FixedSize=0
RebootMode=I
InstallPrompt="Welcome to ShaelvienOS Setup Wizard."
DisplayLicense=D:\ShaelvienOS_Portable\portable\\license.txt
FinishMessage="ShaelvienOS has been successfully installed!"
TargetName=D:\ShaelvienOS_Portable\portable\\ShaelvienOS_Setup.exe
FriendlyName=ShaelvienOS Setup
AppLaunched="create_shortcuts.bat"
PostInstallCmd="ShaelvienOS.exe"
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0=D:\ShaelvienOS_Portable\portable\\dist
[SourceFiles0]
D:\ShaelvienOS_Portable\portable\\dist=
[Setup]
File0="ShaelvienOS.exe"
File1="shaelvien_daemon.exe"
File2="shaelvien_tray.exe"
File3="create_shortcuts.bat"
File4="assets"
File5="logs"
[Strings]
InstallPrompt="Welcome to ShaelvienOS!"
