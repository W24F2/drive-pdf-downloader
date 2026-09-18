<#
.SYNOPSIS
    Publish wiki\*.md to this repository's GitHub wiki (Windows).

.DESCRIPTION
    The wiki repository only exists after you enable Wikis once:
    repo -> Settings -> Features -> tick "Wikis", then create a first page.

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

$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("dpdwiki_" + [Guid]::NewGuid().ToString("N"))
try {
    Write-Host "cloning https://github.com/$Repo.wiki.git ..."
    git clone --depth 1 "https://github.com/$Repo.wiki.git" $Tmp
    if ($LASTEXITCODE -ne 0) {
        throw "Could not clone the wiki repo. Enable Wikis in repo Settings -> Features, create a first page, then retry."
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
        Write-Host "Wiki published: https://github.com/$Repo/wiki" -ForegroundColor Green
    }
} finally {
    Pop-Location -ErrorAction SilentlyContinue
    Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}
