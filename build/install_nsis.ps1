#Requires -Version 5.1
<#
.SYNOPSIS
    Installiert NSIS 3.11 portable nach .tools\NSIS (ZIP, kein Setup-EXE).
#>
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$nsisDir = Join-Path $Root ".tools\NSIS"
$candidates = @(
    (Join-Path $nsisDir "makensis.exe"),
    (Join-Path $nsisDir "Bin\makensis.exe")
)
$existing = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($existing) {
    Write-Host "NSIS bereits vorhanden: $existing"
    exit 0
}

$toolsDir = Join-Path $Root ".tools"
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

$zipUrl = "https://downloads.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip"
$zipPath = Join-Path $toolsDir "nsis-3.11.zip"
$extractDir = Join-Path $toolsDir "nsis-extract"

function Test-ZipFile([string]$Path) {
    if (-not (Test-Path $Path)) { return $false }
    $len = (Get-Item $Path).Length
    if ($len -lt 500000) {
        Write-Host "Datei zu klein ($len Bytes) – vermutlich HTML-Fehlerseite"
        return $false
    }
    $b = Get-Content $Path -AsByteStream -TotalCount 2
    return ($b[0] -eq 0x50 -and $b[1] -eq 0x4B)
}

$downloaded = $false
1..3 | ForEach-Object {
    if ($downloaded) { return }
    Write-Host "NSIS-ZIP Download Versuch $_/3..."
    try {
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing `
            -UserAgent "SurepriseAi-CI/1.0" -MaximumRedirection 10
        if (Test-ZipFile $zipPath) {
            $downloaded = $true
        } else {
            Write-Host "Ungültige ZIP-Datei, erneuter Versuch..."
        }
    } catch {
        Write-Host "Fehler: $_"
        Start-Sleep -Seconds 5
    }
}

if (-not $downloaded) {
    throw "NSIS-ZIP konnte nicht von SourceForge geladen werden"
}

if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

$inner = Join-Path $extractDir "nsis-3.11"
if (-not (Test-Path $inner)) {
    $inner = $extractDir
}

if (Test-Path $nsisDir) { Remove-Item $nsisDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $nsisDir | Out-Null
Copy-Item -Path (Join-Path $inner "*") -Destination $nsisDir -Recurse -Force
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

$makensis = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $makensis) {
    throw "NSIS entpackt, aber makensis.exe fehlt unter $nsisDir"
}

Write-Host "NSIS installiert: $makensis"
