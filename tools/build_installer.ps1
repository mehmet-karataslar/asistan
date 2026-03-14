$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Iss = Join-Path $Root 'installer\asistan.iss'

$Candidates = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
)

$Iscc = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    throw 'Inno Setup bulunamadi. Lutfen Inno Setup 6 kurun: https://jrsoftware.org/isinfo.php'
}

Set-Location $Root
& $Iscc $Iss
Write-Host "Installer tamamlandi. Cikti: $Root\dist_installer\Asistan-Setup.exe" -ForegroundColor Green
