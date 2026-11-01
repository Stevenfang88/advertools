#!/usr/bin/env bash
# Start Chinese demo shell on 127.0.0.1:8765
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export DEMO_SHELL_PASSWORD="${DEMO_SHELL_PASSWORD:-demo2026}"
export DEMO_SHELL_HOST="${DEMO_SHELL_HOST:-127.0.0.1}"
export DEMO_SHELL_PORT="${DEMO_SHELL_PORT:-8765}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
echo "Starting demo_shell → http://${DEMO_SHELL_HOST}:${DEMO_SHELL_PORT}/"
echo "Basic Auth: any user / password=\$DEMO_SHELL_PASSWORD"
exec python -m demo_shell
