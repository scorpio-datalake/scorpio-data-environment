#requires -Version 5.1
<#
.SYNOPSIS
  Incremental build of the Scorpio client library only (workspace package name: scorpio).

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

$cargoArgs = @('build', '-p', 'scorpio')
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
