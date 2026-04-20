#requires -Version 5.1
<#
.SYNOPSIS
  Runs the full Rust workspace test suite (cargo test --workspace), from engine/.

.DESCRIPTION
  Mirrors full_build.ps1 scope: optional cargo metadata preflight, then cargo test --workspace.
  Does not compile-only; use scripts/builds_and_scripts/full_build.ps1 for builds.

.PARAMETER Release
  Pass --release to Cargo.

.PARAMETER NoLocked
  Omit --locked from metadata and test.

.PARAMETER Offline
  Pass --offline to Cargo.

.PARAMETER SkipPreflight
  Skip cargo metadata.

.PARAMETER VerboseCargo
  Set CARGO_TERM_PROGRESS=verbose.
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$NoLocked,
    [switch]$Offline,
    [switch]$SkipPreflight,
    [switch]$VerboseCargo
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_ScorpioEngineTestSession.ps1')

if ($VerboseCargo) {
    $env:CARGO_TERM_PROGRESS = 'verbose'
}

Write-Host "Engine root: $ScorpioEngineRoot"
Write-Host "Target dir: $(if ($env:CARGO_TARGET_DIR) { $env:CARGO_TARGET_DIR } else { Join-Path $ScorpioEngineRoot 'target' })"
& rustc -V
& cargo -V

if (-not $SkipPreflight) {
    $metaArgs = @('metadata', '--format-version', '1')
    if (-not $NoLocked) {
        $metaArgs += '--locked'
    }
    Write-Host "Preflight: cargo $($metaArgs -join ' ') ..."
    & cargo @metaArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$cargoArgs = @('test', '--workspace')
if ($Release) {
    $cargoArgs += '--release'
}
if (-not $NoLocked) {
    $cargoArgs += '--locked'
}
if ($Offline) {
    $cargoArgs += '--offline'
}

Write-Host "Testing: cargo $($cargoArgs -join ' ') ..."
& cargo @cargoArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
