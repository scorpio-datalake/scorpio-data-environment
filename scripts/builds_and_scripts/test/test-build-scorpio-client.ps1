#requires -Version 5.1
<#
.SYNOPSIS
  Runs unit tests for the scorpio client package (cargo name: scorpio).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_ScorpioEngineTestSession.ps1')

$cargoArgs = @('test', '-p', 'scorpio', '--locked')
if ($Release) {
    $cargoArgs += '--release'
}
if ($Offline) {
    $cargoArgs += '--offline'
}

Write-Host "Testing: cargo $($cargoArgs -join ' ') ..."
& cargo @cargoArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
