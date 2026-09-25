#!/usr/bin/env bash
# Idempotent setup for the Traefik reverse proxy.
#
#   - generates a self-signed TLS cert (SAN IP:10.8.0.15) if missing
#   - generates users.txt (admin + bcrypt/apr1 hash) if missing
#   - starts/refreshes the Traefik container
#
# Usage:
#   DASH_PASS='choose-one' ./setup.sh     # non-interactive, known password
#   ./setup.sh                            # random password, printed once
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST_IP="${HOST_IP:-10.8.0.15}"
DASH_USER="${DASH_USER:-admin}"
CERT_DIR="$SCRIPT_DIR/certs"
CERT="$CERT_DIR/server.crt"
KEY="$CERT_DIR/server.key"
USERS="$SCRIPT_DIR/users.txt"

mkdir -p "$CERT_DIR"

# --- TLS certificate ---------------------------------------------------------
if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
  echo "[+] Generating self-signed certificate for IP:${HOST_IP}"
  openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
    -keyout "$KEY" -out "$CERT" \
    -subj "/CN=${HOST_IP}" \
    -addext "subjectAltName=IP:${HOST_IP},IP:127.0.0.1,DNS:localhost"
  chmod 600 "$KEY"
  echo "[+] Wrote $CERT and $KEY"
else
  echo "[=] Certificate already present, skipping generation"
fi

# --- Basic auth users --------------------------------------------------------
if [ ! -f "$USERS" ]; then
  GENERATED=0
  if [ -n "${DASH_PASS:-}" ]; then
    PASS="$DASH_PASS"
  else
    PASS="$(openssl rand -hex 16)"
    GENERATED=1
  fi
  HASH="$(printf '%s' "$PASS" | openssl passwd -apr1 -stdin)"
  printf '%s:%s\n' "$DASH_USER" "$HASH" > "$USERS"
  chmod 600 "$USERS"
  if [ "$GENERATED" = "1" ]; then
    echo "=================================================================="
    echo "[!] Generated dashboard credentials (shown once - save them now):"
    echo "    URL:      https://${HOST_IP}/dashboard/"
    echo "    username: ${DASH_USER}"
    echo "    password: ${PASS}"
    echo "=================================================================="
  else
    echo "[+] Created $USERS from DASH_PASS"
  fi
else
  echo "[=] users.txt already present, skipping (password unchanged)"
fi

# --- Start / refresh ---------------------------------------------------------
if docker compose version >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
  echo "[+] Starting stack with 'docker compose'"
  docker compose up -d --force-recreate
else
  echo "[+] 'docker compose' unavailable - using 'docker run'"
  docker rm -f traefik >/dev/null 2>&1 || true
  docker run -d \
    --name traefik \
    --restart unless-stopped \
    --network host \
    -v "$SCRIPT_DIR/traefik.yml:/etc/traefik/traefik.yml:ro" \
    -v "$SCRIPT_DIR/dynamic.yml:/etc/traefik/dynamic.yml:ro" \
    -v "$CERT_DIR:/etc/traefik/certs:ro" \
    -v "$USERS:/etc/traefik/users.txt:ro" \
    traefik:v3.1
fi

echo "[+] Traefik is up: https://${HOST_IP}/  (dashboard: https://${HOST_IP}/dashboard/)"
