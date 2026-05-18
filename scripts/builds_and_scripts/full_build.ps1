#requires -Version 5.1
<#
.SYNOPSIS
  Full Cargo workspace build for the Scorpio engine with preflight checks.

.DESCRIPTION
  Before compiling, runs a fast workspace check (cargo metadata) so manifests and Cargo.lock agree.
  Then runs "cargo build --workspace". Cargo reuses incrementally compiled artifacts in target/ when
  sources are unchanged; engine/Cargo.toml [profile.dev] sets incremental = true and codegen-units = 256.

  By default passes --locked (same spirit as CI). Use -NoLocked to resolve or change deps without
  updating Cargo.lock first.

  Override target directory with environment variable CARGO_TARGET_DIR (shared by all cargo commands).
  Optional sccache: set RUSTC_WRAPPER to your sccache binary. When RUSTC_WRAPPER is set, this script sets
  CARGO_INCREMENTAL=0 because sccache does not support Cargo incremental compilation.

.PARAMETER Release
  Use release profile (cargo build --release).

.PARAMETER Profile
  Use an explicit workspace profile (e.g. ci, release-lto, release-nonlto). Mutually exclusive with -Release.

.PARAMETER NoLocked
  Omit --locked from metadata and build.

.PARAMETER Offline
  Pass --offline to Cargo.

.PARAMETER SkipPreflight
  Skip cargo metadata (use only if you already validated the workspace).

.PARAMETER VerboseCargo
  Set CARGO_TERM_PROGRESS=verbose for more detailed Cargo progress output.

.EXAMPLE
  .\scripts\builds_and_scripts\full_build.ps1

.EXAMPLE
  .\scripts\builds_and_scripts\full_build.ps1 -Release

.EXAMPLE
  .\scripts\builds_and_scripts\full_build.ps1 -Profile ci
#>
[CmdletBinding()]
param (
    [switch]$Release,

    [ValidateNotNullOrEmpty()]
    [string]$Profile,

    [switch]$NoLocked,

    [switch]$Offline,

    [switch]$SkipPreflight,

    [switch]$VerboseCargo
)

$ErrorActionPreference = 'Stop'

if ($Release -and $Profile) {
    Write-Error 'Use either -Release or -Profile, not both.'
}

Get-Command cargo -ErrorAction Stop | Out-Null

# full_build.ps1 -> scripts/builds_and_scripts -> .. -> .. -> repo root
$repoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot '..') '..')
$defaultEngine = Join-Path $repoRoot 'engine'
$engineRoot = if ($env:SCORPIO_ENGINE_ROOT) { $env:SCORPIO_ENGINE_ROOT } else { $defaultEngine }

$cargoToml = Join-Path $engineRoot 'Cargo.toml'
if (-not (Test-Path -LiteralPath $cargoToml)) {
    Write-Error "No Cargo.toml at engine root: $engineRoot (set SCORPIO_ENGINE_ROOT if using a non-default layout)."
}

if ($VerboseCargo) {
    $env:CARGO_TERM_PROGRESS = 'verbose'
}

# Default dev build: ensure incremental compilation unless using sccache (RUSTC_WRAPPER).
# sccache rejects builds when CARGO_INCREMENTAL is enabled; see https://github.com/mozilla/sccache
if ($env:RUSTC_WRAPPER) {
    $env:CARGO_INCREMENTAL = '0'
} elseif (-not $Release -and -not $Profile) {
    if ([string]::IsNullOrEmpty($env:CARGO_INCREMENTAL)) {
        $env:CARGO_INCREMENTAL = '1'
    }
}

Set-Location -LiteralPath $engineRoot

Write-Host "Engine root: $engineRoot"
Write-Host "Target dir: $(if ($env:CARGO_TARGET_DIR) { $env:CARGO_TARGET_DIR } else { Join-Path $engineRoot 'target' })"
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

$cargoArgs = @('build', '--workspace')
if ($Profile) {
    $cargoArgs += @('--profile', $Profile)
} elseif ($Release) {
    $cargoArgs += '--release'
}

if (-not $NoLocked) {
    $cargoArgs += '--locked'
}

if ($Offline) {
    $cargoArgs += '--offline'
}

Write-Host "Building: cargo $($cargoArgs -join ' ') ..."
& cargo @cargoArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
