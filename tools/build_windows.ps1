$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = "$Root\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python virtual environment bulunamadi: $Python"
}

& $Python tools/generate_icon.py

if (Test-Path "$Root\build") {
    Remove-Item -Recurse -Force "$Root\build"
}
if (Test-Path "$Root\dist\Asistan") {
    Remove-Item -Recurse -Force "$Root\dist\Asistan"
}

& $Python -m PyInstaller --noconfirm asistan.spec

Write-Host "Build tamamlandi. Cikti: $Root\dist\Asistan" -ForegroundColor Green
Write-Host "Installer icin Inno Setup ile derleyin: installer\asistan.iss" -ForegroundColor Yellow
