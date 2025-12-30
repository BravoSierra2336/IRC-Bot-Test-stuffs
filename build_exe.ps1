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

# Upgrade pip and install PyInstaller (use module to avoid shim issues)
python -m pip install --upgrade pip
python -m pip install pyinstaller

# Build executable using a wrapper entry to preserve package-relative imports
$exeName = "AscensionismBot"
$entry = "_pyi_entry.py"
@"
import asyncio
from irc_bot.bot import main

if __name__ == "__main__":
    asyncio.run(main())
"@ | Set-Content -Path $entry -Encoding UTF8

python -m PyInstaller --onefile --name $exeName $entry

Write-Host "Build complete. See dist/$exeName.exe"

Pop-Location
