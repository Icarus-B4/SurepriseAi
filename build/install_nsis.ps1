#Requires -Version 5.1
<#
.SYNOPSIS
    Installiert NSIS 3.11 nach .tools\NSIS (System, winget oder ZIP-Download).
#>
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$nsisDir = Join-Path $Root ".tools\NSIS"

function Get-MakensisPath {
    @(
        (Join-Path $nsisDir "makensis.exe"),
        (Join-Path $nsisDir "Bin\makensis.exe"),
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "$env:ProgramFiles\NSIS\makensis.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Copy-NsisTree([string]$SourceDir) {
    if (Test-Path $nsisDir) { Remove-Item $nsisDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $nsisDir | Out-Null
    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $nsisDir -Recurse -Force
}

$existing = Get-MakensisPath
if ($existing -and $existing -like "$nsisDir*") {
    Write-Host "NSIS bereits vorhanden: $existing"
    exit 0
}

$systemDir = @(
    "${env:ProgramFiles(x86)}\NSIS",
    "$env:ProgramFiles\NSIS"
) | Where-Object { Test-Path (Join-Path $_ "makensis.exe") } | Select-Object -First 1

if ($systemDir) {
    Write-Host "System-NSIS kopieren von $systemDir"
    Copy-NsisTree $systemDir
    Write-Host "NSIS installiert: $(Get-MakensisPath)"
    exit 0
}

function Try-WingetInstall {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    Write-Host "Versuche NSIS via winget..."
    try {
        $proc = Start-Process -FilePath "winget" -ArgumentList @(
            "install", "-e", "--id", "NSIS.NSIS",
            "--accept-package-agreements", "--accept-source-agreements",
            "--disable-interactivity", "--silent"
        ) -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0) { return $false }
        $dir = @(
            "${env:ProgramFiles(x86)}\NSIS",
            "$env:ProgramFiles\NSIS"
        ) | Where-Object { Test-Path (Join-Path $_ "makensis.exe") } | Select-Object -First 1
        if ($dir) {
            Copy-NsisTree $dir
            return $true
        }
    } catch {
        Write-Host "winget fehlgeschlagen: $_"
    }
    return $false
}

if (Try-WingetInstall) {
    Write-Host "NSIS installiert: $(Get-MakensisPath)"
    exit 0
}

$toolsDir = Join-Path $Root ".tools"
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
$zipPath = Join-Path $toolsDir "nsis-3.11.zip"
$extractDir = Join-Path $toolsDir "nsis-extract"

$mirrors = @(
    "https://downloads.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip",
    "https://fossies.org/windows/misc/nsis-3.11.zip"
)

function Test-ZipFile([string]$Path) {
    if (-not (Test-Path $Path)) { return $false }
    $len = (Get-Item $Path).Length
    if ($len -lt 500000) {
        Write-Host "Datei zu klein ($len Bytes)"
        return $false
    }
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 2) { return $false }
    return ($bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4B)
}

function Download-File([string]$Url, [string]$OutPath) {
    $request = [System.Net.HttpWebRequest]::Create($Url)
    $request.UserAgent = "SurepriseAi-CI/1.0"
    $request.AllowAutoRedirect = $true
    $request.Timeout = 180000
    $response = $request.GetResponse()
    try {
        $input = $response.GetResponseStream()
        $output = [System.IO.File]::Create($OutPath)
        try {
            $input.CopyTo($output)
        } finally {
            $output.Close()
        }
    } finally {
        $response.Close()
    }
}

$downloaded = $false
foreach ($url in $mirrors) {
    if ($downloaded) { break }
    1..2 | ForEach-Object {
        if ($downloaded) { return }
        Write-Host "NSIS-ZIP Download ($url) Versuch $_/2..."
        try {
            if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
            Download-File -Url $url -OutPath $zipPath
            if (Test-ZipFile $zipPath) {
                $downloaded = $true
            } else {
                Write-Host "Ungueltige ZIP, naechster Versuch..."
            }
        } catch {
            Write-Host "Fehler: $_"
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $downloaded) {
    throw "NSIS konnte weder per winget noch per ZIP-Mirror installiert werden"
}

if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

$inner = Join-Path $extractDir "nsis-3.11"
if (-not (Test-Path $inner)) { $inner = $extractDir }

Copy-NsisTree $inner
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

$makensis = Get-MakensisPath
if (-not $makensis) {
    throw "NSIS entpackt, aber makensis.exe fehlt unter $nsisDir"
}

Write-Host "NSIS installiert: $makensis"
