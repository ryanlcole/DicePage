# =============================================================
# SHAELVIEN SELF-SIGNING SCRIPT  (Phase 8.6)
# Creates a local trusted certificate and signs all EXEs
# =============================================================

$certName = "CN=ShaelvienOS_LocalSigner"
$certPath = "Cert:\CurrentUser\My"
$cert = Get-ChildItem $certPath | Where-Object { $_.Subject -eq $certName }

if (-not $cert) {
    Write-Host "[INFO] Creating local signing certificate..."
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $certName `
        -CertStoreLocation "Cert:\CurrentUser\My" -KeyExportPolicy Exportable `
        -KeyLength 2048 -NotAfter (Get-Date).AddYears(3)
    Write-Host "[INFO] Certificate created: $($cert.Thumbprint)"
}

# Register certificate to Trusted Root
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store "Root","CurrentUser"
$rootStore.Open("ReadWrite")
$rootStore.Add($cert)
$rootStore.Close()

# Sign every EXE in dist\
$dist = "D:\ShaelvienOS_Portable\portable\dist"
$exeList = Get-ChildItem -Path $dist -Filter "*.exe"
foreach ($exe in $exeList) {
    Write-Host "[SIGN] $($exe.Name)"
    & signtool.exe sign /fd SHA256 /a /tr http://timestamp.digicert.com `
        /td SHA256 /n "ShaelvienOS_LocalSigner" $exe.FullName
}
Write-Host "[SUCCESS] All executables signed and trusted locally."
