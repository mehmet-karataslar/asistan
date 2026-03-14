; Inno Setup script for Asistan
#define MyAppName "Asistan"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Asistan"
#define MyAppExeName "Asistan.exe"
#define BuildDir "..\\dist\\Asistan"

[Setup]
AppId={{7D849B65-CF14-4BD1-9C96-9FDE6C9D6B4F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\\dist_installer
OutputBaseFilename=Asistan-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UsedUserAreasWarning=no

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustu kisayolu olustur"; GroupDescription: "Ek gorevler:"; Flags: unchecked
Name: "startup"; Description: "Windows baslangicinda otomatik calistir"; GroupDescription: "Ek gorevler:"; Flags: unchecked

[Files]
Source: "{#BuildDir}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup
[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{#MyAppName} uygulamasini baslat"; Flags: nowait postinstall skipifsilent
