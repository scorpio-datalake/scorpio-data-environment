#requires -Version 5.1
<#
.SYNOPSIS
  Run Scorpio engine tests using Cargo incremental builds (reuse target/; only rebuilds what changed).

.DESCRIPTION
  Defaults to the ballista-core package so a small change does not compile the whole workspace.
  Cargo always reuses previous artifacts when sources are unchanged; a second run is typically link + run only.

  Use -RunOnly to skip Cargo entirely and execute the last-built test binary(ies) under target/*/deps/
  (build once with: .\scripts\run-engine-tests.ps1, then iterate with -RunOnly).

  Avoid running several Cargo commands at once against the same engine/target: they block on a file lock
  and look like repeated full builds. Prefer this script (or one Cargo at a time).

.PARAMETER BuildBinary
  With a single package (not -Workspace), pass --features build-binary. Required for ballista-core tests
  in the object_store module (S3/GCS/Azure registry). Ignored when -Workspace is set.

.PARAMETER Package
  Crate name (-p), default ballista-core. Ignored when -Workspace is set.

.PARAMETER Workspace
  Run cargo test --workspace (full engine suite).

.PARAMETER Filter
  Test name filter (passed to the test harness before --).

.PARAMETER NoRun
  cargo test --no-run — compile tests only, do not execute.

.PARAMETER RunOnly
  Do not invoke Cargo; run existing test executables for -Package from the target directory.

.PARAMETER Release
  Use the release profile (target/release).

.PARAMETER Offline
  Pass --offline to Cargo (ignored with -RunOnly).

.PARAMETER NoCapture
  Pass --nocapture to the test binary.

.EXAMPLE
  .\scripts\run-engine-tests.ps1
  .\scripts\run-engine-tests.ps1 -BuildBinary -Filter object_store
  .\scripts\run-engine-tests.ps1 -p ballista -Filter client
  .\scripts\run-engine-tests.ps1 -Workspace
  .\scripts\run-engine-tests.ps1 -RunOnly -Filter object_store
#>
param(
    [Alias("p")]
    [string]$Package = "ballista-core",

    [switch]$Workspace,

    [Alias("t")]
    [string]$Filter,

    [switch]$NoRun,

    [switch]$RunOnly,

    [switch]$Release,

    [switch]$Offline,

    [switch]$NoCapture,

    [switch]$BuildBinary
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$DefaultEngine = Join-Path $RepoRoot "engine"
$EngineRoot = if ($env:SCORPIO_ENGINE_ROOT) { $env:SCORPIO_ENGINE_ROOT } else { $DefaultEngine }

if (-not (Test-Path (Join-Path $EngineRoot "Cargo.toml"))) {
    Write-Error "No Cargo.toml at $EngineRoot; set SCORPIO_ENGINE_ROOT"
}

if ($RunOnly -and $Workspace) {
    Write-Error "-RunOnly cannot be combined with -Workspace"
}
if ($RunOnly -and $NoRun) {
    Write-Error "-RunOnly cannot be combined with -NoRun"
}
if ($BuildBinary -and $Workspace) {
    Write-Warning "-BuildBinary is ignored with -Workspace (each crate uses its own features)."
}

function Get-EngineTargetRoot {
    if ($env:CARGO_TARGET_DIR) {
        return $env:CARGO_TARGET_DIR
    }
    return (Join-Path $EngineRoot "target")
}

function Get-CrateExePrefix {
    param([string]$Pkg)
    return $Pkg.Replace("-", "_")
}

function Invoke-RunOnlyTests {
    $snake = Get-CrateExePrefix $Package
    $profileDir = if ($Release) { "release" } else { "debug" }
    $deps = Join-Path (Get-EngineTargetRoot) "$profileDir\deps"
    if (-not (Test-Path $deps)) {
        Write-Error "No deps directory at $deps. Run without -RunOnly once after a successful build."
    }

    $exes = @(
        Get-ChildItem -LiteralPath $deps -Filter "$snake-*.exe" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '\.d\.exe$' } |
            Sort-Object Name
    )

    if ($exes.Count -eq 0) {
        Write-Error "No test executable matching ${snake}-*.exe under $deps. Run without -RunOnly first."
    }

    $testArgs = @()
    if ($Filter) { $testArgs += $Filter }
    if ($NoCapture) { $testArgs += "--nocapture" }

    $failed = $false
    foreach ($exe in $exes) {
        Write-Host "Running $($exe.Name)" -ForegroundColor Cyan
        & $exe.FullName @testArgs
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    }
    if ($failed) { exit 1 }
}

Push-Location $EngineRoot
try {
    if ($RunOnly) {
        Invoke-RunOnlyTests
        return
    }

    # Build scripts (e.g. prost) need PROTOC on Windows when not already set.
    if (-not $env:PROTOC) {
        $protocScript = Join-Path $ScriptDir "set-protoc-for-cargo.ps1"
        if (Test-Path $protocScript) {
            . $protocScript
        }
    }

    $cargoArgs = @("test", "--locked")
    if ($Workspace) {
        $cargoArgs += "--workspace"
    }
    else {
        $cargoArgs += "-p", $Package
        if ($BuildBinary) {
            $cargoArgs += "--features", "build-binary"
        }
    }
    if ($Release) { $cargoArgs += "--release" }
    if ($NoRun) { $cargoArgs += "--no-run" }
    if ($Offline) { $cargoArgs += "--offline" }

    $testBinArgs = @()
    if ($NoCapture) { $testBinArgs += "--nocapture" }

    if ($Filter) { $cargoArgs += $Filter }
    if ($testBinArgs.Count -gt 0) {
        $cargoArgs += "--"
        $cargoArgs += $testBinArgs
    }

    Write-Host "cargo $($cargoArgs -join ' ')" -ForegroundColor DarkGray
    & cargo @cargoArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
