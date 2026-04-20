#requires -Version 5.1
<#
.SYNOPSIS
  Incremental build of scorpio-core only (cargo -p).

.DESCRIPTION
  Runs from engine/ so artifacts land in engine/target and Cargo reuses them on full workspace builds.

  Phase 1 R5 scoped validation: run [test-scorpio-core.ps1](test-scorpio-core.ps1) or
  `cargo test -p scorpio-core --locked` from engine/ (see Planning/Phase1.md).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$engineRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'engine')
Set-Location $engineRoot

$cargoArgs = @('build', '-p', 'scorpio-core')
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
