#requires -Version 5.1
<#
.SYNOPSIS
  Validates build-scorpio-scheduler.ps1 and test-scorpio-scheduler.ps1 (parse + expected cargo package).
#>
[CmdletBinding()]
param ()

$ErrorActionPreference = 'Stop'
$moduleRoot = Split-Path -Parent $PSScriptRoot

function Test-ScriptParsesAndMatches {
    param (
        [string]$RelativePath,
        [string[]]$MatchPatterns
    )
    $scriptPath = Join-Path $moduleRoot $RelativePath
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
    foreach ($pattern in $MatchPatterns) {
        if ($content -notmatch $pattern) {
            throw "Pattern not found in ${RelativePath}: $pattern"
        }
    }
}

Test-ScriptParsesAndMatches -RelativePath 'build-scorpio-scheduler.ps1' -MatchPatterns @(
    "-p',\s*'scorpio-scheduler'"
)
Test-ScriptParsesAndMatches -RelativePath 'test-scorpio-scheduler.ps1' -MatchPatterns @(
    "'test',\s*'-p',\s*'scorpio-scheduler'",
    "'--locked'"
)

Write-Host "OK: build-scorpio-scheduler.ps1, test-scorpio-scheduler.ps1"
