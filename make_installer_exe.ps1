# Build a standalone installer .exe from installer.ps1 using PS2EXE
# Requires the 'ps2exe' PowerShell module.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\make_installer_exe.ps1

$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot"

# Install ps2exe if not present
if (-not (Get-Module -ListAvailable -Name ps2exe)) {
    Write-Host "Installing ps2exe module for current user..."
    Install-Module ps2exe -Scope CurrentUser -Force
}
Import-Module ps2exe

$inputFile = Join-Path $PSScriptRoot "installer.ps1"
$outputFile = Join-Path $PSScriptRoot "AscensionismBot-Installer.exe"

Write-Host "Building $outputFile from $inputFile ..."
Invoke-PS2EXE -InputFile $inputFile -OutputFile $outputFile -Title "Ascensionism Bot Installer" -Version "1.0.0.0" -NoConsole:$false

Write-Host "Done. Run: $outputFile"

Pop-Location
