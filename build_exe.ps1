# Build a standalone Windows .exe for the IRC bot using PyInstaller
# Usage:
#   pwsh ./build_exe.ps1

$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot"

# Ensure venv exists
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

# Activate venv
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
. $activate

# Upgrade pip and install PyInstaller
python -m pip install --upgrade pip
pip install pyinstaller

# Build executable
$exeName = "AscensionismBot"
pyinstaller --onefile --name $exeName irc_bot\bot.py

Write-Host "Build complete. See dist/$exeName.exe"

Pop-Location
