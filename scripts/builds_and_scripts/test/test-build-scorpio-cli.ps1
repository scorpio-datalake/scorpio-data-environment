#requires -Version 5.1
<#
.SYNOPSIS
  Runs unit tests for scorpio-cli.
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_ScorpioEngineTestSession.ps1')

$cargoArgs = @('test', '-p', 'scorpio-cli', '--locked')
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
