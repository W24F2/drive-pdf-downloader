<#
.SYNOPSIS
    Sets up drive-pdf-downloader on Windows: creates .venv, installs Python
    dependencies and the Playwright Chromium build.

.EXAMPLE
    .\scripts\setup_windows.ps1

.EXAMPLE
    .\scripts\setup_windows.ps1 -SkipBrowser   # reuse an already-installed Chrome
#>
[CmdletBinding()]
param(
    [string]$Python = "",
    [switch]$SkipBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "drive-pdf-downloader setup (Windows)" -ForegroundColor Cyan
Write-Host "project: $Root"

if (-not $Python) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $Python = "py"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $Python = "python"
    } else {
        throw "Python 3.9+ was not found. Install it from https://www.python.org/downloads/ and tick 'Add python.exe to PATH'."
    }
}
Write-Host "using python launcher: $Python"

$Venv = Join-Path $Root ".venv"
if (-not (Test-Path $Venv)) {
    Write-Host "creating virtual environment in .venv ..."
    & $Python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "failed to create the virtual environment" }
} else {
    Write-Host "reusing existing .venv"
}

$Py = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $Py)) { throw "venv python not found at $Py" }

& $Py -m pip install --upgrade pip
& $Py -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

if (-not $SkipBrowser) {
    Write-Host "installing Playwright Chromium (used for headless runs) ..."
    & $Py -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Playwright Chromium install failed - the tool will fall back to your system Chrome/Edge."
    }
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Run it with:  .\scripts\run_windows.ps1"
Write-Host "Or double-click: scripts\run_windows.bat"
