#requires -Version 5.1
<#
.SYNOPSIS
  Start the minimal Scorpio engine Docker Compose stack (scheduler + executor).

.DESCRIPTION
  Same SCORPIO_ENGINE_ROOT contract as build-ballista-docker.ps1 (defaults to <repo>/engine).

.EXAMPLE
  .\scripts\docker-compose-up.ps1
  .\scripts\docker-compose-up.ps1 -d
#>
[CmdletBinding()]
param(
    [string] $EngineRoot = $env:SCORPIO_ENGINE_ROOT
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$engine = if ($EngineRoot) { $EngineRoot } else { Join-Path $RepoRoot 'engine' }
$env:SCORPIO_ENGINE_ROOT = $engine

$cargoToml = Join-Path $engine 'Cargo.toml'
if (-not (Test-Path -LiteralPath $cargoToml)) {
    Write-Error "SCORPIO_ENGINE_ROOT must be the engine workspace (Cargo.toml not found): $engine"
}

$composeFile = Join-Path $RepoRoot 'deploy\docker-compose\docker-compose.scorpio-engine.yml'
$env:DOCKER_BUILDKIT = '1'
docker compose -f $composeFile up @args
