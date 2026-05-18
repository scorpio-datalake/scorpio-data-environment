#!/usr/bin/env bash
# Fail if SCORPIO_ENGINE_ROOT (or default engine/) is a git repo whose origin still points at Apache Ballista.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_ENGINE="${REPO_ROOT}/engine"
ENGINE_ROOT="${SCORPIO_ENGINE_ROOT:-${DEFAULT_ENGINE}}"

if ! git -C "${ENGINE_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "verify-engine-git-remotes: skip (not a git work tree): ${ENGINE_ROOT}"
  exit 0
fi

ORIGIN_URL="$(git -C "${ENGINE_ROOT}" remote get-url origin 2>/dev/null || true)"
if [[ -z "${ORIGIN_URL}" ]]; then
  echo "verify-engine-git-remotes: error: no remote named 'origin' in ${ENGINE_ROOT}" >&2
  exit 1
fi

LOWER="$(printf '%s' "${ORIGIN_URL}" | tr '[:upper:]' '[:lower:]')"
if [[ "${LOWER}" == *"apache/datafusion-ballista"* ]]; then
  echo "verify-engine-git-remotes: error: origin must not be Apache Ballista:" >&2
  echo "  ${ORIGIN_URL}" >&2
  echo "Rename to upstream and add your org as origin - see engine/REPOSITORY_SETUP.md" >&2
  exit 1
fi

echo "verify-engine-git-remotes: ok origin=${ORIGIN_URL}"
