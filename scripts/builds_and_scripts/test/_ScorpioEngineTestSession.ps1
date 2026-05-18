# Dot-source from scripts/builds_and_scripts/test/*.ps1 only.
# Sets location to the Cargo workspace root (engine/) and applies the same CARGO_INCREMENTAL rule
# as full_build.ps1 when RUSTC_WRAPPER (e.g. sccache) is set.
$ErrorActionPreference = 'Stop'
Get-Command cargo -ErrorAction Stop | Out-Null
$repoRoot = Resolve-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') '..')
$defaultEngine = Join-Path $repoRoot 'engine'
$ScorpioEngineRoot = if ($env:SCORPIO_ENGINE_ROOT) { $env:SCORPIO_ENGINE_ROOT } else { $defaultEngine }
$cargoToml = Join-Path $ScorpioEngineRoot 'Cargo.toml'
if (-not (Test-Path -LiteralPath $cargoToml)) {
    throw "No Cargo.toml at engine root: $ScorpioEngineRoot (set SCORPIO_ENGINE_ROOT if needed)."
}
if ($env:RUSTC_WRAPPER) {
    $env:CARGO_INCREMENTAL = '0'
}
Set-Location -LiteralPath $ScorpioEngineRoot
