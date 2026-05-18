#requires -Version 5.1
<#
.SYNOPSIS
  Incremental build of scorpio-scheduler only (cargo -p).

.DESCRIPTION
  Runs from engine/ so artifacts land in engine/target and Cargo reuses them on full workspace builds.

  Phase 1 R4 scoped validation: run `cargo test -p scorpio-scheduler --locked` from engine/ (see Planning/Phase1.md).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$engineRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'engine')
Set-Location $engineRoot

$cargoArgs = @('build', '-p', 'scorpio-scheduler')
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
