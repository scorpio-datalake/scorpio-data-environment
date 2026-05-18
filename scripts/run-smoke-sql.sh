#!/usr/bin/env bash
# Run in-process SQL smoke tests (smoke_*) in scorpio-core when that crate is a workspace member.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_ENGINE="${REPO_ROOT}/engine"
ENGINE_ROOT="${SCORPIO_ENGINE_ROOT:-${DEFAULT_ENGINE}}"

if [[ ! -f "${ENGINE_ROOT}/Cargo.toml" ]]; then
  echo "error: no Cargo.toml at ${ENGINE_ROOT}; set SCORPIO_ENGINE_ROOT" >&2
  exit 1
fi

cd "${ENGINE_ROOT}"
if ! cargo metadata --no-deps --format-version 1 2>/dev/null | grep -q '"name":"scorpio-core"'; then
  echo "run-smoke-sql: no package 'scorpio-core' in workspace at ${ENGINE_ROOT}" >&2
  echo "Add crates/scorpio-core to [workspace].members (and restore the crate), or run: cd engine && cargo test --workspace --locked" >&2
  exit 1
fi

exec cargo test -p scorpio-core smoke_ --locked -- --nocapture
