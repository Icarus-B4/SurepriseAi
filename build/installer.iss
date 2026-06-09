; SurepriseAi – Inno Setup Installer (Windows)
; Voraussetzung: build.ps1 -Installer (PyInstaller-Bundle in dist\SurepriseAi)

#define MyAppName "SurepriseAi"
#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "SurepriseAi"
#define MyAppURL "https://github.com/Icarus-B4/SurepriseAi"
#define MyAppExeName "SurepriseAi.exe"

[Setup]
AppId={{A7B3C9D1-4E2F-5A6B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=SurepriseAi-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"; Flags: unchecked
Name: "autostart"; Description: "Mit Windows starten"; GroupDescription: "Autostart:"; Flags: unchecked

[Files]
Source: "..\dist\SurepriseAi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SurepriseAi"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Config liegt in %APPDATA%\SurepriseAi – wird beim ersten Start angelegt }
  end;
end;
