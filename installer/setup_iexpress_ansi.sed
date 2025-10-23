[Version]
Class=IEXPRESS
SEDVersion=3

[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=ShaelvienOS installed successfully.
TargetName=ShaelvienOS_Setup.exe
FriendlyName=ShaelvienOS Installer
AppLaunched=ShaelvienOS.exe
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=SourceFiles

[Strings]
InstallPath=%ProgramFiles%\ShaelvienOS

[SourceFiles]
SourceFiles0=payload

[SourceFiles0]
payload\ShaelvienOS.exe=$InstallPath$
payload\assets\*=$InstallPath$\assets\
payload\logs\*=$InstallPath$\logs\
