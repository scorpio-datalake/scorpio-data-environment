#requires -Version 5.1
<#
.SYNOPSIS
  Fail if SCORPIO_ENGINE_ROOT (or default engine/) is a git repo whose origin still points at Apache Ballista.
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$DefaultEngine = Join-Path $RepoRoot "engine"
$EngineRoot = if ($env:SCORPIO_ENGINE_ROOT) { $env:SCORPIO_ENGINE_ROOT } else { $DefaultEngine }

$null = git -C $EngineRoot rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "verify-engine-git-remotes: skip (not a git work tree): $EngineRoot"
    exit 0
}

$originUrl = git -C $EngineRoot remote get-url origin 2>$null
if (-not $originUrl) {
    Write-Host "verify-engine-git-remotes: error: no remote named 'origin' in $EngineRoot" -ForegroundColor Red
    exit 1
}

$lower = $originUrl.ToLowerInvariant()
if ($lower -like "*apache/datafusion-ballista*") {
    Write-Host "verify-engine-git-remotes: error: origin must not be Apache Ballista:" -ForegroundColor Red
    Write-Host "  $originUrl"
    Write-Host "Rename to upstream and add your org as origin - see engine/REPOSITORY_SETUP.md"
    exit 1
}

Write-Host ('verify-engine-git-remotes: ok origin={0}' -f $originUrl)
