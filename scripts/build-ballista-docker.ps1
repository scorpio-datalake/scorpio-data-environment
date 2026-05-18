#requires -Version 5.1
<#
.SYNOPSIS
  Build Scorpio scheduler and executor Docker images (Ballista-derived; name kept for planning).

.DESCRIPTION
  Defaults to deploy/docker-compose/docker-compose.scorpio-stack.yml (override with env COMPOSE_FILE).
  Engine build uses SCORPIO_ENGINE_ROOT (directory with Cargo.toml); default <repo>/engine.

  Prerequisites: Docker Compose v2.20+ (include:), BuildKit, network for first Rust build.

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
docker compose -f $composeFile build @args
