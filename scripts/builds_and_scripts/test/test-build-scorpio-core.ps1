#requires -Version 5.1
<#
.SYNOPSIS
  Runs unit and integration tests for scorpio-core (delegates to test-scorpio-core.ps1).
#>
[CmdletBinding()]
param (
    [switch]$Release,
    [switch]$Offline,
    [switch]$BuildBinary
)

$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $moduleRoot 'test-scorpio-core.ps1'
if (-not (Test-Path -LiteralPath $runner)) {
    throw "Missing script: $runner"
}

& $runner @PSBoundParameters
exit $LASTEXITCODE
