#Requires -Version 5.1
<#
.SYNOPSIS
    Erstellt das SurepriseAi PyInstaller-Bundle und optional den Inno-Setup-Installer.
.EXAMPLE
    .\build\build.ps1
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

Write-Host "==> PyInstaller..." -ForegroundColor Yellow
& $py -m PyInstaller build\sureprise.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dist = Join-Path $Root "dist\SurepriseAi"
Copy-Item -Force "config.example.json" $dist
New-Item -ItemType Directory -Force -Path (Join-Path $dist "models") | Out-Null

Write-Host "==> Bundle fertig: $dist" -ForegroundColor Green

if ($Installer) {
    $iscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $iscc) {
        Write-Warning "Inno Setup 6 nicht gefunden. Installer übersprungen."
        Write-Host "Download: https://jrsoftware.org/isinfo.php"
        exit 0
    }

    Write-Host "==> Inno Setup Installer..." -ForegroundColor Yellow
    & $iscc "/DMyAppVersion=$Version" "build\installer.iss"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "==> Installer: dist\SurepriseAi-Setup.exe" -ForegroundColor Green
}
