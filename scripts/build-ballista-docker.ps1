#requires -Version 5.1
<#
.SYNOPSIS
  Build Scorpio scheduler and executor Docker images (Ballista-derived; name kept for planning).

.DESCRIPTION
  Uses deploy/docker-compose/docker-compose.scorpio-engine.yml with build context SCORPIO_ENGINE_ROOT
  (the directory that contains engine Cargo.toml). Defaults SCORPIO_ENGINE_ROOT to <repo>/engine.

  Prerequisites: Docker Desktop (or Docker Engine) with Compose v2, first-build network access to crates.io.

.PARAMETER EngineRoot
  Override engine workspace path (same as env SCORPIO_ENGINE_ROOT).

.EXAMPLE
  .\scripts\build-ballista-docker.ps1
  $env:SCORPIO_ENGINE_ROOT = 'C:/src/scorpio-data-environment/engine'; .\scripts\build-ballista-docker.ps1
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
if (-not (Test-Path -LiteralPath $composeFile)) {
    Write-Error "Compose file missing: $composeFile"
}

$env:DOCKER_BUILDKIT = '1'
docker compose -f $composeFile build @args
