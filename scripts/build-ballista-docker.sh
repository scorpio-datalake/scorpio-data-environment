#!/usr/bin/env bash
# Build Scorpio scheduler + executor images (Ballista-derived stack; script name kept for Phase 1 checklist).
# Requires: Docker (BuildKit), network for crates.io on first build.
#
# SCORPIO_ENGINE_ROOT — absolute path to the engine workspace (directory containing Cargo.toml).
# Default: <repo>/engine when unset (repo = parent of scripts/).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export SCORPIO_ENGINE_ROOT="${SCORPIO_ENGINE_ROOT:-${REPO_ROOT}/engine}"

if [[ ! -f "${SCORPIO_ENGINE_ROOT}/Cargo.toml" ]]; then
  echo "error: SCORPIO_ENGINE_ROOT must point at the engine workspace (Cargo.toml not found): ${SCORPIO_ENGINE_ROOT}" >&2
  exit 1
fi

COMPOSE_FILE="${REPO_ROOT}/deploy/docker-compose/docker-compose.scorpio-engine.yml"
if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "error: compose file missing: ${COMPOSE_FILE}" >&2
  exit 1
fi

export DOCKER_BUILDKIT=1
docker compose -f "${COMPOSE_FILE}" build "$@"
