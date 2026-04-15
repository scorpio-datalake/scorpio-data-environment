#!/usr/bin/env bash
# Run Scorpio engine tests with Cargo incremental builds (reuse target/; only rebuilds what changed).
# Default package is ballista-core. Use --workspace for the full suite.
#
# Examples:
#   ./scripts/run-engine-tests.sh
#   ./scripts/run-engine-tests.sh --build-binary --filter object_store
#   ./scripts/run-engine-tests.sh -p scorpio --filter client
#   ./scripts/run-engine-tests.sh --workspace
#   ./scripts/run-engine-tests.sh --run-only --filter object_store
#
# Avoid several Cargo processes on the same engine/target (they contend on a lock). Prefer one command
# or this script. Optional separate CARGO_TARGET_DIR forces a cold rebuild.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENGINE_ROOT="${SCORPIO_ENGINE_ROOT:-$REPO_ROOT/engine}"

PACKAGE="ballista-core"
WORKSPACE=0
FILTER=""
NO_RUN=0
RUN_ONLY=0
RELEASE=0
OFFLINE=0
NOCAPTURE=0
BUILD_BINARY=0

usage() {
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
    echo "Options:"
    echo "  -p, --package NAME   Crate name (default: ballista-core)"
    echo "  -w, --workspace      cargo test --workspace"
    echo "  -t, --filter PAT     Test name filter"
    echo "      --no-run         Compile tests only"
    echo "      --run-only       Skip Cargo; run last-built test binaries under target"
    echo "      --release        Release profile"
    echo "      --offline        cargo --offline"
    echo "      --nocapture      Pass --nocapture to test harness"
    echo "      --build-binary   With single package: --features build-binary (ballista-core object_store)"
    echo "  -h, --help           Show this help"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--package)
            PACKAGE="$2"
            shift 2
            ;;
        -w|--workspace)
            WORKSPACE=1
            shift
            ;;
        -t|--filter)
            FILTER="$2"
            shift 2
            ;;
        --no-run)
            NO_RUN=1
            shift
            ;;
        --run-only)
            RUN_ONLY=1
            shift
            ;;
        --release)
            RELEASE=1
            shift
            ;;
        --offline)
            OFFLINE=1
            shift
            ;;
        --nocapture)
            NOCAPTURE=1
            shift
            ;;
        --build-binary)
            BUILD_BINARY=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ ! -f "$ENGINE_ROOT/Cargo.toml" ]]; then
    echo "No Cargo.toml at $ENGINE_ROOT; set SCORPIO_ENGINE_ROOT" >&2
    exit 1
fi

if [[ "$RUN_ONLY" -eq 1 && "$WORKSPACE" -eq 1 ]]; then
    echo "--run-only cannot be combined with --workspace" >&2
    exit 1
fi
if [[ "$RUN_ONLY" -eq 1 && "$NO_RUN" -eq 1 ]]; then
    echo "--run-only cannot be combined with --no-run" >&2
    exit 1
fi
if [[ "$BUILD_BINARY" -eq 1 && "$WORKSPACE" -eq 1 ]]; then
    echo "warning: --build-binary ignored with --workspace (each crate uses its own features)" >&2
fi

target_root="${CARGO_TARGET_DIR:-$ENGINE_ROOT/target}"
profile_dir="$([[ "$RELEASE" -eq 1 ]] && echo release || echo debug)"

snake_pkg() {
    echo "${1//-/_}"
}

run_only() {
    local snake deps exe
    snake="$(snake_pkg "$PACKAGE")"
    deps="$target_root/$profile_dir/deps"
    if [[ ! -d "$deps" ]]; then
        echo "No deps directory at $deps. Run without --run-only once after a successful build." >&2
        exit 1
    fi
    shopt -s nullglob
    local found=0
    local failed=0
    for exe in "$deps/$snake"-*; do
        [[ -f "$exe" && -x "$exe" ]] || continue
        [[ "$exe" == *.d ]] && continue
        found=1
        echo "Running $(basename "$exe")"
        local args=()
        [[ -n "$FILTER" ]] && args+=("$FILTER")
        [[ "$NOCAPTURE" -eq 1 ]] && args+=("--nocapture")
        if [[ ${#args[@]} -gt 0 ]]; then
            "$exe" "${args[@]}" || failed=1
        else
            "$exe" || failed=1
        fi
    done
    shopt -u nullglob
    if [[ "$found" -eq 0 ]]; then
        echo "No test executable matching $snake-* under $deps. Run without --run-only first." >&2
        exit 1
    fi
    [[ "$failed" -eq 0 ]] || exit 1
}

cd "$ENGINE_ROOT"

if [[ "$RUN_ONLY" -eq 1 ]]; then
    run_only
    exit 0
fi

cargo_args=(test --locked)
if [[ "$WORKSPACE" -eq 1 ]]; then
    cargo_args+=(--workspace)
else
    cargo_args+=(-p "$PACKAGE")
    [[ "$BUILD_BINARY" -eq 1 ]] && cargo_args+=(--features build-binary)
fi
[[ "$RELEASE" -eq 1 ]] && cargo_args+=(--release)
[[ "$NO_RUN" -eq 1 ]] && cargo_args+=(--no-run)
[[ "$OFFLINE" -eq 1 ]] && cargo_args+=(--offline)

echo "cargo ${cargo_args[*]}${FILTER:+ $FILTER}${NOCAPTURE:+ -- --nocapture}" >&2

if [[ -n "$FILTER" ]]; then
    cargo_args+=("$FILTER")
fi
if [[ "$NOCAPTURE" -eq 1 ]]; then
    cargo_args+=(--)
    cargo_args+=(--nocapture)
fi

exec cargo "${cargo_args[@]}"
