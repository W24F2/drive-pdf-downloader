<#
.SYNOPSIS
    Publish wiki\*.md to this repository's GitHub wiki (Windows).

.DESCRIPTION
    The wiki's git storage does not exist until the *first* page is saved
    through the web UI - a GitHub limitation with no API behind it. This script
    detects that case, prints the exact link, and waits for you to click it
    once, then publishes every page. After that it just syncs.

.EXAMPLE
    .\scripts\publish_wiki.ps1
    .\scripts\publish_wiki.ps1 -Repo W24F2/drive-pdf-downloader
#>
[CmdletBinding()]
param(
    [string]$Repo = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not $Repo) {
    $origin = (git -C $Root remote get-url origin 2>$null)
    if ($origin) {
        $Repo = $origin -replace '^(git@|https://)github\.com[:/]', '' -replace '\.git$', ''
    }
}
if (-not $Repo) { throw "No remote found. Pass -Repo owner/repo." }

$WikiDir = Join-Path $Root "wiki"
if (-not (Test-Path $WikiDir)) { throw "No wiki\ directory in $Root" }

$WikiUrl = "https://github.com/$Repo.wiki.git"
$PageUrl = "https://github.com/$Repo/wiki"
$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("dpdwiki_" + [Guid]::NewGuid().ToString("N"))

try {
    Write-Host "cloning $WikiUrl ..."

    git clone --depth 1 $WikiUrl $Tmp 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  GitHub has not created the wiki storage yet." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  A wiki's $Repo.wiki.git repository is only born when its first page is"
        Write-Host "  saved through the web UI - there is no API for it, so no script can do"
        Write-Host "  this part. You only ever have to do it once."
        Write-Host ""
        Write-Host "    1. open  $PageUrl"
        Write-Host "    2. click  `"Create the first page`""
        Write-Host "    3. type anything (it gets overwritten) and press  Save Page"
        Write-Host ""

        $ready = $false
        for ($i = 1; $i -le 12; $i++) {
            $reply = Read-Host '  press Enter once the page is saved (or type q to give up)'
            if ($reply -match '^\s*q\s*$') {
                Write-Host "  giving up - re-run this script when you are ready" -ForegroundColor Yellow
                exit 3
            }
            git clone --depth 1 $WikiUrl $Tmp 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  wiki initialised - publishing all pages" -ForegroundColor Green
                $ready = $true
                break
            }
            Write-Host "  still not there, give GitHub a moment and press Enter again"
        }
        if (-not $ready) {
            Write-Host "  still unavailable - re-run this script later" -ForegroundColor Yellow
            exit 3
        }
    }

    Copy-Item (Join-Path $WikiDir "*.md") $Tmp -Force
    Push-Location $Tmp
    git add -A
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "wiki already up to date"
    } else {
        git commit -m "docs: sync wiki from repo"
        git push
        Write-Host "Wiki published: $PageUrl" -ForegroundColor Green
    }
} finally {
    Pop-Location -ErrorAction SilentlyContinue
    Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}
