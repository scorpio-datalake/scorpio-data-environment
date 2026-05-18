#requires -Version 5.1
# Sets $env:PROTOC and prepends protoc's directory to $env:Path for this shell.
# Must be DOT-SOURCED or changes do not persist:
#   . .\scripts\set-protoc-for-cargo.ps1
$ErrorActionPreference = "Stop"

if ($MyInvocation.InvocationName -ne ".") {
    Write-Warning @"
Run with a leading dot so PROTOC and PATH apply to this PowerShell window:
  . $($MyInvocation.PSCommandPath)
(Executing with .\script.ps1 uses a child process; your session never gets the variables.)
"@
}

$candidates = @(
    (Get-Command protoc -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
    "${env:ProgramFiles}\Google Protobuf\bin\protoc.exe",
    "${env:ProgramFiles(x86)}\Google Protobuf\bin\protoc.exe"
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $candidates) {
    $found = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "protoc.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    if ($found) { $candidates = @($found) }
}

if (-not $candidates) {
    Write-Error "protoc.exe not found. Install with: winget install Google.Protobuf"
}

# Single path from the pipeline is a [string]; [0] would be the first character ("C" from "C:\...").
$candidates = @($candidates)
$exe = $candidates[0]
$binDir = Split-Path -Parent $exe
$env:PROTOC = $exe
if ($env:Path -notlike "*${binDir}*") {
    $env:Path = "${binDir};${env:Path}"
}

Write-Host "PROTOC=$exe"
Write-Host "Prepended to PATH for this session: $binDir"
& $exe --version
