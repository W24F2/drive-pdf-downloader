<#
.SYNOPSIS
    Runs drive-pdf-downloader on Windows using the local .venv.

.EXAMPLE
    .\scripts\run_windows.ps1
    .\scripts\run_windows.ps1 --list
    .\scripts\run_windows.ps1 --workers 4 --out D:\pdfs

.EXAMPLE
    .\scripts\run_windows.ps1 -Quiet          # for Task Scheduler / cron
#>
[CmdletBinding()]
param(
    [switch]$Quiet,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Not set up yet." -ForegroundColor Yellow
    Write-Host "Run:  .\scripts\setup_windows.ps1"
    exit 1
}

$Script = Join-Path $Root "drive_pdf_downloader.py"
$Pass = @()
if ($Quiet) { $Pass += "--quiet" }
if ($Args) { $Pass += $Args }

& $Py $Script @Pass
exit $LASTEXITCODE
