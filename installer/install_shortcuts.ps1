param(
  [string]$InstallerPath
)

$Target = "$env:ProgramFiles\ShaelvienOS\ShaelvienOS.exe"
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ShaelvienOS"
$DesktopLink = [IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'ShaelvienOS.lnk')

New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null

$WshShell = New-Object -ComObject WScript.Shell

# Start Menu shortcut
$L1 = $WshShell.CreateShortcut([IO.Path]::Combine($StartMenuDir, 'ShaelvienOS.lnk'))
$L1.TargetPath = $Target
$L1.WorkingDirectory = Split-Path $Target
$L1.WindowStyle = 1
$L1.Save()

# Desktop shortcut
$L2 = $WshShell.CreateShortcut($DesktopLink)
$L2.TargetPath = $Target
$L2.WorkingDirectory = Split-Path $Target
$L2.WindowStyle = 1
$L2.Save()

Write-Host "✅ Shortcuts created."
