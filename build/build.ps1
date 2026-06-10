#Requires -Version 5.1
<#
.SYNOPSIS
    Erstellt PyInstaller-Bundle und NSIS-Setup (wie Hermes Desktop / electron-builder).
.EXAMPLE
    .\build\build.ps1 -Installer
#>
param(
    [switch]$Installer,
    [switch]$SkipPip,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> SurepriseAi Build (Root: $Root)" -ForegroundColor Cyan

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Error "Virtuelle Umgebung fehlt. Bitte: python -m venv venv && pip install -r requirements.txt"
}

$py = ".\venv\Scripts\python.exe"
$pip = ".\venv\Scripts\pip.exe"

if (-not $Version) {
    $Version = & $py -c "from src.version import __version__; print(__version__)"
}
Write-Host "==> Version: $Version" -ForegroundColor Cyan

if (-not $SkipPip) {
    Write-Host "==> Installiere Build-Abhängigkeiten..." -ForegroundColor Yellow
    & $pip install -r requirements-build.txt -q
    & $pip install -r requirements.txt -q
}

Write-Host "==> Installer-Grafiken..." -ForegroundColor Yellow
& $py build\generate_installer_assets.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> PyInstaller..." -ForegroundColor Yellow
& $py -m PyInstaller build\sureprise.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dist = Join-Path $Root "dist\SurepriseAi"
Copy-Item -Force "config.example.json" $dist
New-Item -ItemType Directory -Force -Path (Join-Path $dist "models") | Out-Null
Write-Host "==> Bundle fertig: $dist" -ForegroundColor Green

if ($Installer) {
    $makensis = @(
        (Join-Path $Root ".tools\NSIS\makensis.exe"),
        (Join-Path $Root ".tools\NSIS\Bin\makensis.exe"),
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "$env:ProgramFiles\NSIS\makensis.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $makensis) {
        Write-Host "==> NSIS wird installiert (ZIP portable)..." -ForegroundColor Yellow
        & (Join-Path $Root "build\install_nsis.ps1") -Root $Root
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $makensis = @(
            (Join-Path $Root ".tools\NSIS\makensis.exe"),
            (Join-Path $Root ".tools\NSIS\Bin\makensis.exe")
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    }

    if (-not $makensis) {
        Write-Error "NSIS (makensis) nicht gefunden. NSIS 3.x erforderlich."
    }

    Write-Host "==> NSIS Setup.exe (Wizard, wie Hermes Desktop)..." -ForegroundColor Yellow
    & $makensis @("/DAPP_VERSION=$Version", "build\installer.nsi")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "==> Fertig: dist\SurepriseAi-Setup.exe" -ForegroundColor Green
}
