#requires -Version 5.1
<#
.SYNOPSIS
  Runs scoped tests for scorpio-core (matches Phase 1 R5 check).

.DESCRIPTION
  From engine/: `cargo test -p scorpio-core --locked` with optional Release, --offline, and
  -BuildBinary for object-store integration tests (`--features build-binary`).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline,
    [switch]$BuildBinary
)

$ErrorActionPreference = 'Stop'
$engineRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'engine')
Set-Location $engineRoot
# sccache (RUSTC_WRAPPER) does not support Cargo incremental compilation
if ($env:RUSTC_WRAPPER) {
    $env:CARGO_INCREMENTAL = '0'
}

$cargoArgs = @('test', '-p', 'scorpio-core', '--locked')
if ($BuildBinary) { $cargoArgs += @('--features', 'build-binary') }
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
