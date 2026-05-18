#requires -Version 5.1
<#
.SYNOPSIS
  Runs unit and integration tests for scorpio-scheduler (delegates to test-scorpio-scheduler.ps1).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $moduleRoot 'test-scorpio-scheduler.ps1'
if (-not (Test-Path -LiteralPath $runner)) {
    throw "Missing script: $runner"
}

& $runner @PSBoundParameters
exit $LASTEXITCODE
