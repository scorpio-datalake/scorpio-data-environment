#requires -Version 5.1
<#
.SYNOPSIS
  Runs the full Rust workspace test suite (cargo test --workspace), from engine/.

.DESCRIPTION
  Mirrors full_build.ps1 scope: optional cargo metadata preflight, then cargo test --workspace.
  Does not compile-only; use scripts/builds_and_scripts/full_build.ps1 for builds.

  When RUSTC_WRAPPER is set (e.g. sccache), the dot-sourced session sets CARGO_INCREMENTAL=0 so Cargo
  does not enable incremental with sccache. On Windows, sccache can still crash with STATUS_STACK_BUFFER_OVERRUN
  on large test crates; use -NoSccache to unset RUSTC_WRAPPER for this run only (restored afterward).

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

.PARAMETER NoSccache
  Temporarily unset RUSTC_WRAPPER for this script run (restores previous value on exit). Use if
  sccache fails compiling workspace tests on Windows.
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$NoLocked,
    [switch]$Offline,
    [switch]$SkipPreflight,
    [switch]$VerboseCargo,
    [switch]$NoSccache
)

$ErrorActionPreference = 'Stop'

$previousRustcWrapper = $null
$clearSccacheWrapper = $false
if ($NoSccache -and $env:RUSTC_WRAPPER) {
    $previousRustcWrapper = $env:RUSTC_WRAPPER
    Remove-Item Env:RUSTC_WRAPPER -ErrorAction SilentlyContinue
    $clearSccacheWrapper = $true
    Write-Host "NoSccache: cleared RUSTC_WRAPPER for this run (was: $previousRustcWrapper)"
}

try {
    . (Join-Path $PSScriptRoot '_ScorpioEngineTestSession.ps1')

    # Match full_build.ps1: prefer incremental dev tests when not using a rustc wrapper.
    if (-not $env:RUSTC_WRAPPER -and -not $Release) {
        if ([string]::IsNullOrEmpty($env:CARGO_INCREMENTAL)) {
            $env:CARGO_INCREMENTAL = '1'
        }
    }

    if ($VerboseCargo) {
        $env:CARGO_TERM_PROGRESS = 'verbose'
    }

    Write-Host "Engine root: $ScorpioEngineRoot"
    Write-Host "Target dir: $(if ($env:CARGO_TARGET_DIR) { $env:CARGO_TARGET_DIR } else { Join-Path $ScorpioEngineRoot 'target' })"
    if ($env:RUSTC_WRAPPER) {
        Write-Host "RUSTC_WRAPPER: $($env:RUSTC_WRAPPER) (CARGO_INCREMENTAL=$($env:CARGO_INCREMENTAL))"
    } else {
        Write-Host "RUSTC_WRAPPER: (unset)  CARGO_INCREMENTAL=$($env:CARGO_INCREMENTAL)"
    }
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
}
finally {
    if ($clearSccacheWrapper) {
        if ($null -ne $previousRustcWrapper -and $previousRustcWrapper.Length -gt 0) {
            $env:RUSTC_WRAPPER = $previousRustcWrapper
            Write-Host "Restored RUSTC_WRAPPER=$($env:RUSTC_WRAPPER)"
        }
    }
}
