# AscensionismBot installer: clone/pull, setup, build, and run
# Usage examples:
#   powershell -ExecutionPolicy Bypass -File .\installer.ps1 -RepoUrl "https://github.com/owner/repo.git" -Branch main
#   powershell -ExecutionPolicy Bypass -File .\installer.ps1  # auto-detect RepoUrl from current folder's git remote

param(
    [string]$RepoUrl,
    [string]$Branch = "main",
    [string]$InstallDir = "$env:LOCALAPPDATA\AscensionismBot"
)

$ErrorActionPreference = "Stop"

function Require-Tool($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Required tool '$name' not found in PATH. Please install $name and retry."
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
    throw "RepoUrl not provided and could not be auto-detected. Provide -RepoUrl (e.g., https://github.com/owner/repo.git)."
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

# Build executable
Write-Host "Building executable with PyInstaller..."
Push-Location $InstallDir
$exeName = "AscensionismBot"
$spec = Join-Path $InstallDir "AscensionismBot.spec"
if (Test-Path $spec) {
    pyinstaller $spec
} else {
    pyinstaller --onefile --name $exeName "irc_bot\\bot.py"
}
Pop-Location

$distExe = Join-Path $InstallDir "dist\\$exeName.exe"
if (-not (Test-Path $distExe)) {
    throw "Build failed: $distExe not found."
}

# Config setup
$configPath = Join-Path $InstallDir "config.json"
if (-not (Test-Path $configPath)) {
    $example = Join-Path $InstallDir "config.example.json"
    if (Test-Path $example) {
        Copy-Item -Force $example $configPath
        Write-Host "Created config.json from example. Please edit your settings."
        try { Start-Process notepad.exe $configPath } catch {}
        Write-Host "Press Enter to continue after editing config.json..."
        [void][System.Console]::ReadLine()
    } else {
        Write-Warning "No config.json found and config.example.json is missing. The bot may fail to start."
    }
}

# Launch the bot
Write-Host "Launching $distExe ..."
Start-Process -NoNewWindow $distExe -WorkingDirectory (Split-Path $distExe)
Write-Host "Installer finished. The bot should now be running."
