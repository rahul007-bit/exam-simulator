#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

PORT="${1:-3000}"
HOST="${2:-0.0.0.0}"

echo "Starting CKA Exam Web Simulator..."
echo "Binding on http://${HOST}:${PORT}"

if [ -f "$DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$DIR/.venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

# Build the Vue SPA into web/dist on deploy (FE-003). Since the FE-040 cutover
# the built SPA is the only UI: if the build is absent (npm/bun missing) the
# server returns 503 until web/dist exists.
"$DIR/tools/build-frontend.sh"

exec "$PYTHON_BIN" -m uvicorn web.server:app --host "$HOST" --port "$PORT"
