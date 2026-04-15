#requires -Version 5.1
<#
.SYNOPSIS
  Validates full_build.ps1 (parse + expected cargo workspace build behavior).
#>
[CmdletBinding()]
param ()

$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $moduleRoot 'full_build.ps1'

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
if ($content -notmatch "('build',\s*'--workspace'|@\('build',\s*'--workspace'\))") {
    throw "Expected cargo build --workspace in $scriptPath"
}
if ($content -notmatch "metadata") {
    throw "Expected cargo metadata preflight in $scriptPath"
}

Write-Host "OK: full_build.ps1"
