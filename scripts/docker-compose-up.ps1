#requires -Version 5.1
<#
.SYNOPSIS
  Start the Scorpio Compose stack (default: full MVP stack file).

.DESCRIPTION
  Same SCORPIO_ENGINE_ROOT and COMPOSE_FILE defaults as build-ballista-docker.ps1.

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

$stackFile = Join-Path $RepoRoot 'deploy\docker-compose\docker-compose.scorpio-stack.yml'
$engineFile = Join-Path $RepoRoot 'deploy\docker-compose\docker-compose.scorpio-engine.yml'
$composeFile = if ($env:COMPOSE_FILE) { $env:COMPOSE_FILE } else { $stackFile }
if (-not (Test-Path -LiteralPath $composeFile)) {
    Write-Error "Compose file missing: $composeFile"
}
if (($composeFile -eq $stackFile) -and -not (Test-Path -LiteralPath $engineFile)) {
    Write-Error "Stack includes missing file: $engineFile"
}

$env:DOCKER_BUILDKIT = '1'
docker compose -f $composeFile up @args
