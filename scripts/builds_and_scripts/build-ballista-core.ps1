#requires -Version 5.1
<#
.SYNOPSIS
  Incremental build of ballista-core only (cargo -p).

.DESCRIPTION
  Runs from engine/ so artifacts land in engine/target and Cargo reuses them on full workspace builds.
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$engineRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'engine')
Set-Location $engineRoot

$cargoArgs = @('build', '-p', 'ballista-core')
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
