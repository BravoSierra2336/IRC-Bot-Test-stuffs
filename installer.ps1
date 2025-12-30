# AscensionismBot installer: clone/pull, setup, build, and run
# Usage examples:
#   powershell -ExecutionPolicy Bypass -File .\installer.ps1 -RepoUrl "https://github.com/owner/repo.git" -Branch main
#   powershell -ExecutionPolicy Bypass -File .\installer.ps1  # auto-detect RepoUrl from current folder's git remote

param(
    [string]$RepoUrl,
    [string]$Branch = "main",
    [string]$InstallDir = "$env:LOCALAPPDATA\AscensionismBot",
    [switch]$NoInteract
)

$ErrorActionPreference = "Stop"

function Pause-IfInteractive {
    param([string]$Message = "Press Enter to exit...")
    if (-not $NoInteract) {
        Write-Host $Message
        [void][System.Console]::ReadLine()
    }
}

function Require-Tool($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Warning "Required tool '$name' not found in PATH. Please install $name and retry."
        Pause-IfInteractive "Missing prerequisite. Press Enter to exit..."
        exit 1
    }
}

Write-Host "Starting AscensionismBot installer..."
Require-Tool 'python'
Require-Tool 'git'

# Resolve RepoUrl: try auto-detect from current workspace if not provided
if (-not $RepoUrl) {
    try {
        Push-Location "$PSScriptRoot"
        $RepoUrl = git config --get remote.origin.url
    } catch {}
    finally { Pop-Location }
}
if (-not $RepoUrl) {
    if (-not $NoInteract) {
        $prompt = "Enter Git repo URL (default: https://github.com/BravoSierra2336/IRC-Bot-Test-stuffs.git)"
        $RepoUrl = Read-Host $prompt
        if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
            $RepoUrl = "https://github.com/BravoSierra2336/IRC-Bot-Test-stuffs.git"
        }
    } else {
        Write-Warning "RepoUrl not provided and could not be auto-detected. Provide -RepoUrl (e.g., https://github.com/owner/repo.git)."
        Pause-IfInteractive "Press Enter to exit..."
        exit 1
    }
}

# Prepare install directory
Write-Host "Using install directory: $InstallDir"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

# Clone or update the repository
if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Existing repo found. Updating..."
    Push-Location $InstallDir
    git fetch --all
    git checkout $Branch
    git pull --ff-only origin $Branch
    Pop-Location
} else {
    # If non-empty dir without git, back it up
    if ((Get-ChildItem $InstallDir -Force | Where-Object { $_.Name -ne '.git' } | Measure-Object).Count -gt 0) {
        $backup = "$InstallDir-backup-" + (Get-Date -Format "yyyyMMddHHmmss")
        Write-Host "Install dir has files. Moving to $backup"
        Move-Item -Force $InstallDir $backup
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    }
    Write-Host "Cloning $RepoUrl (branch $Branch)..."
    git clone --branch $Branch --depth 1 $RepoUrl $InstallDir
}

# Create and activate venv
$venvPath = Join-Path $InstallDir ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
}
$activate = Join-Path $venvPath "Scripts\\Activate.ps1"
. $activate

# Dependencies
Write-Host "Upgrading pip and installing dependencies..."
python -m pip install --upgrade pip
$req = Join-Path $InstallDir "requirements.txt"
if (Test-Path $req) {
    pip install -r $req
}

# Ensure PyInstaller
pip install pyinstaller

# Build executable using a wrapper entry to preserve package-relative imports
Write-Host "Building executable with PyInstaller..."
Push-Location $InstallDir
$exeName = "AscensionismBot"
$entry = Join-Path $InstallDir "_pyi_entry.py"
@"
import asyncio
from irc_bot.bot import main

if __name__ == "__main__":
    asyncio.run(main())
"@ | Set-Content -Path $entry -Encoding UTF8

python -m PyInstaller --onefile --name $exeName $entry
Pop-Location

$distExe = Join-Path $InstallDir "dist\\$exeName.exe"
if (-not (Test-Path $distExe)) {
    Write-Warning "Build failed: $distExe not found."
    Pause-IfInteractive "Build failed. Press Enter to exit..."
    exit 1
}

# Config setup
$configPath = Join-Path $InstallDir "config.json"
if (-not (Test-Path $configPath)) {
    $example = Join-Path $InstallDir "config.example.json"
    if (Test-Path $example) {
        Copy-Item -Force $example $configPath
        Write-Host "Created config.json from example. Please edit your settings."
        if (-not $NoInteract) {
            try { Start-Process notepad.exe $configPath } catch {}
            Write-Host "Press Enter to continue after editing config.json..."
            [void][System.Console]::ReadLine()
        }
    } else {
        Write-Warning "No config.json found and config.example.json is missing. The bot may fail to start."
    }
}

# Launch the bot
Write-Host "Launching $distExe ..."
Start-Process $distExe -WorkingDirectory (Split-Path $distExe) -WindowStyle Normal
Write-Host "Installer finished. A separate bot window should open."
Pause-IfInteractive
