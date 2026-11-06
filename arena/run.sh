#!/usr/bin/env bash
# Start the local gateway. Foreground by default; use systemd for a daemon.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

export ARENA_GW_TOKEN="${ARENA_GW_TOKEN:-}"
export ARENA_HEADLESS="${ARENA_HEADLESS:-1}"
exec python3 -m uvicorn arena.gateway:app \
  --host 127.0.0.1 --port "${ARENA_PORT:-8787}" --workers 1 --log-level info
