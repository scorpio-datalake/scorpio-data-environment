#requires -Version 5.1
<#
.SYNOPSIS
  Run in-process SQL smoke tests (smoke_*) in scorpio-core when that crate is a workspace member.
  If the workspace is Ballista-only, prints what to do instead.
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$DefaultEngine = Join-Path $RepoRoot "engine"
$EngineRoot = if ($env:SCORPIO_ENGINE_ROOT) { $env:SCORPIO_ENGINE_ROOT } else { $DefaultEngine }

if (-not (Test-Path (Join-Path $EngineRoot "Cargo.toml"))) {
    Write-Error "No Cargo.toml at $EngineRoot; set SCORPIO_ENGINE_ROOT"
}

Push-Location $EngineRoot
try {
    $metaJson = cargo metadata --no-deps --format-version 1 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "cargo metadata failed: $metaJson"
    }
    $meta = $metaJson | ConvertFrom-Json
    $hasCore = $meta.packages | Where-Object { $_.name -eq "scorpio-core" }
    if (-not $hasCore) {
        Write-Host "run-smoke-sql: no package 'scorpio-core' in workspace at $EngineRoot" -ForegroundColor Yellow
        Write-Host "This script only runs DataFusion in-process smokes in scorpio-core." -ForegroundColor Yellow
        Write-Host "Add `"crates/scorpio-core`" to [workspace].members in engine/Cargo.toml (and restore the crate), or run Ballista tests:" -ForegroundColor Yellow
        Write-Host "  cd engine" -ForegroundColor Cyan
        Write-Host "  cargo test --workspace --locked" -ForegroundColor Cyan
        exit 1
    }

    cargo test -p scorpio-core smoke_ --locked -- --nocapture
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
