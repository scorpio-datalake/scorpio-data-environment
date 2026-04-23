#!/usr/bin/env bash
# Run the minimal Scorpio engine Compose stack (scheduler + executor).
# Set SCORPIO_ENGINE_ROOT to the engine workspace, or rely on default <repo>/engine.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export SCORPIO_ENGINE_ROOT="${SCORPIO_ENGINE_ROOT:-${REPO_ROOT}/engine}"

if [[ ! -f "${SCORPIO_ENGINE_ROOT}/Cargo.toml" ]]; then
  echo "error: SCORPIO_ENGINE_ROOT must point at the engine workspace (Cargo.toml not found): ${SCORPIO_ENGINE_ROOT}" >&2
  exit 1
fi

COMPOSE_FILE="${REPO_ROOT}/deploy/docker-compose/docker-compose.scorpio-engine.yml"

export DOCKER_BUILDKIT=1
docker compose -f "${COMPOSE_FILE}" up "$@"
