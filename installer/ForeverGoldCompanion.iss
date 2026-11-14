#define MyAppName "Forever Gold Companion"
#define MyAppVersion "0.5.0"
#define MyAppExeName "ForeverGoldCompanion.exe"
[Setup]
AppId={{9E49791C-4D7F-46EA-9759-80B61F8E1A7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Forever Gold Companion Community Project
DefaultDirName={localappdata}\Programs\Forever Gold Companion
DefaultGroupName=Forever Gold Companion
OutputDir=output
OutputBaseFilename=ForeverGoldCompanion_Setup_0.5.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
[Files]
Source: "..\dist\ForeverGoldCompanion.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Forever Gold Companion"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Forever Gold Companion"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Forever Gold Companion"; Flags: nowait postinstall skipifsilent
