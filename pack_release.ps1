# Package a distributable zip containing the bot exe and QuickStart
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\pack_release.ps1

$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot"

# Ensure exe exists; build if needed
$exePath = Join-Path $PSScriptRoot "dist\AscensionismBot.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "Executable not found. Building via build_exe.ps1..."
    powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
    if (-not (Test-Path $exePath)) {
        throw "Build failed: dist\\AscensionismBot.exe not found."
    }
}

# Prepare release folder
$releaseDir = Join-Path $PSScriptRoot "release"
$payloadDir = Join-Path $releaseDir "payload"
New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null

# Copy files
Copy-Item -Force $exePath $payloadDir
if (Test-Path (Join-Path $PSScriptRoot "config.example.json")) {
    Copy-Item -Force (Join-Path $PSScriptRoot "config.example.json") $payloadDir
}

# Create QuickStart
$qs = @"
AscensionismBot Quick Start (Windows)
------------------------------------
1) Copy 'payload' folder to a location you control (e.g., C:\Bots\AscensionismBot)
2) In that folder, make a copy of 'config.example.json' named 'config.json'.
3) Edit 'config.json' with your server, channels, and credentials.
4) Double-click 'AscensionismBot.exe' to run the bot.

Notes:
- Keep 'config.json' next to the exe.
- Profiles will be written to 'profiles.json' in the same folder.
- TLS: set tls=true and port=6697 on most modern networks.
- Stop the bot by closing the window or using Task Manager.
"@
Set-Content -Path (Join-Path $payloadDir "QuickStart.txt") -Value $qs -Encoding UTF8

# Zip it
$zipPath = Join-Path $releaseDir "AscensionismBot-win64.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($payloadDir, $zipPath)

Write-Host "Packaged: $zipPath"

Pop-Location
