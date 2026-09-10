#!/usr/bin/env bash
# Build the Vue 3 SPA (web/frontend) into web/dist (FE-003, D-005).
#
# The output is NOT committed; this runs on deploy so web/server.py can serve
# the built app with an SPA fallback. Guarded so a host without Node tooling
# still boots: it exits 0 (a no-op) when the scaffold or npm/bun is absent,
# leaving web/server.py to fall back to the legacy web/static UI.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$DIR/web/frontend"
DIST_DIR="$DIR/web/dist"

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo "[build-frontend] No frontend scaffold at $FRONTEND_DIR; skipping (legacy web/static will be served)."
    exit 0
fi

if command -v npm >/dev/null 2>&1; then
    echo "[build-frontend] Building SPA with npm -> web/dist"
    ( cd "$FRONTEND_DIR" && npm ci && npm run build ) || { echo "[build-frontend] ERROR: npm build failed." >&2; exit 1; }
elif command -v bun >/dev/null 2>&1; then
    echo "[build-frontend] Building SPA with bun -> web/dist"
    ( cd "$FRONTEND_DIR" && bun install && bun run build ) || { echo "[build-frontend] ERROR: bun build failed." >&2; exit 1; }
else
    echo "[build-frontend] WARNING: neither npm nor bun found; skipping frontend build." >&2
    if [ ! -f "$DIST_DIR/index.html" ]; then
        echo "[build-frontend] WARNING: web/dist/index.html absent; server will serve legacy web/static." >&2
    fi
    exit 0
fi

if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "[build-frontend] ERROR: build completed but $DIST_DIR/index.html is missing." >&2
    exit 1
fi

echo "[build-frontend] Build OK -> $DIST_DIR/index.html"
