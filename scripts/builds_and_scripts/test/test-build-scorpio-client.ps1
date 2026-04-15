#requires -Version 5.1
<#
.SYNOPSIS
  Validates build-scorpio-client.ps1 (parse + expected cargo package).
#>
[CmdletBinding()]
param ()

$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $moduleRoot 'build-scorpio-client.ps1'

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing script: $scriptPath"
}

$tokens = $null
$parseErrors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    ($scriptPath | Resolve-Path),
    [ref]$tokens,
    [ref]$parseErrors
)
if ($parseErrors -and $parseErrors.Count -gt 0) {
    throw (($parseErrors | ForEach-Object { $_.Message }) -join '; ')
}

$content = Get-Content -LiteralPath $scriptPath -Raw
if ($content -notmatch "-p',\s*'scorpio'") {
    throw "Expected cargo -p 'scorpio' in $scriptPath"
}

Write-Host "OK: build-scorpio-client.ps1"
