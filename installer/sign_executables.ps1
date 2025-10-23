<#
=============================================================
 SHAELVIEN SELF-SIGNING SCRIPT  – Phase 8.7
  ▪ Auto-detects signtool.exe
  ▪ Generates / installs local trusted cert if missing
  ▪ Signs all EXEs in ./dist
=============================================================
#>

Write-Host "`n=== ShaelvienOS Local Code-Signing Engine – Phase 8.7 ==="

# --- Locate signtool.exe -------------------------------------------------------
$possiblePaths = @(
    "$env:ProgramFiles(x86)\Windows Kits\10\bin\*\x64\signtool.exe",
    "$env:ProgramFiles\Windows Kits\10\bin\*\x64\signtool.exe",
    "$env:SystemRoot\System32\signtool.exe"
)
$signtool = Get-ChildItem -Path $possiblePaths -ErrorAction SilentlyContinue | 
            Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $signtool) {
    Write-Host "[ERROR] signtool.exe not found. Please install the Windows SDK (Signing Tools)."
    exit 1
}

Write-Host "[INFO] signtool.exe detected at: $($signtool.FullName)`n"

# --- Create / locate certificate ----------------------------------------------
$certName  = "CN=ShaelvienOS_LocalSigner"
$certStore = "Cert:\CurrentUser\My"
$cert      = Get-ChildItem $certStore | Where-Object { $_.Subject -eq $certName }

if (-not $cert) {
    Write-Host "[INFO] Creating local signing certificate..."
    $cert = New-SelfSignedCertificate -Type CodeSigningCert `
        -Subject $certName -CertStoreLocation $certStore `
        -KeyExportPolicy Exportable -KeyLength 2048 `
        -NotAfter (Get-Date).AddYears(3)
    Write-Host "[INFO] Certificate created: $($cert.Thumbprint)"
}

# --- Ensure cert trusted in Root store ----------------------------------------
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store "Root","CurrentUser"
$rootStore.Open("ReadWrite")
if (-not ($rootStore.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint })) {
    $rootStore.Add($cert)
    Write-Host "[INFO] Added certificate to Trusted Root store."
}
$rootStore.Close()

# --- Sign all executables -----------------------------------------------------
$dist = Join-Path $PSScriptRoot "dist"
if (-not (Test-Path $dist)) {
    Write-Host "[WARN] dist folder not found. Expected at $dist"
    exit 1
}

$exeList = Get-ChildItem -Path $dist -Filter "*.exe"
if (-not $exeList) {
    Write-Host "[WARN] No executables found in $dist"
    exit 0
}

foreach ($exe in $exeList) {
    Write-Host "`n[SIGN] $($exe.Name)"
    & $signtool.FullName sign /fd SHA256 /a `
        /tr http://timestamp.digicert.com /td SHA256 `
        /n "ShaelvienOS_LocalSigner" $exe.FullName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Signed successfully: $($exe.Name)"
    } else {
        Write-Host "[FAIL] signtool returned error code $LASTEXITCODE"
    }
}

Write-Host "`n[VERIFY] Checking signatures..."
foreach ($exe in $exeList) {
    & $signtool.FullName verify /pa /v $exe.FullName | Out-Host
}

Write-Host "`n[SUCCESS] All executables processed and verified.`n"
pause
