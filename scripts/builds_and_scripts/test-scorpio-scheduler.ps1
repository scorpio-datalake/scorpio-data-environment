#requires -Version 5.1
<#
.SYNOPSIS
  Runs scoped tests for scorpio-scheduler (matches Phase 1 R4 check).

.DESCRIPTION
  From engine/: `cargo test -p scorpio-scheduler --locked` with optional Release and --offline.
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$engineRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'engine')
Set-Location $engineRoot

$cargoArgs = @('test', '-p', 'scorpio-scheduler', '--locked')
if ($Release) { $cargoArgs += '--release' }
if ($Offline) { $cargoArgs += '--offline' }

& cargo @cargoArgs
