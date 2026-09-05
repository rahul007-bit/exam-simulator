#!/usr/bin/env bash
set -e
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then source "$ENV_FILE"; fi
NODE_1=${NODE_1:-192.168.50.169}
SSH_USER=${SSH_USER:-root}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5"
if [ -f "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

# Ensure PKI exists and re-sign apiserver.crt to expire in 7 days to simulate expiring certificates
ssh $SSH_OPTS "$SSH_USER@$NODE_1" bash << 'REMOTE_SCRIPT'
set -e
PKI="/etc/kubernetes/pki"
if [ ! -d "$PKI" ] || [ ! -f "$PKI/apiserver.crt" ] || [ ! -f "$PKI/apiserver.key" ] || [ ! -f "$PKI/ca.crt" ] || [ ! -f "$PKI/ca.key" ]; then
    echo "Error: PKI directory or required keys not found on node1" >&2
    exit 1
fi

if [ ! -f "$PKI/apiserver.crt.orig" ]; then
    cp "$PKI/apiserver.crt" "$PKI/apiserver.crt.orig"
fi

SAN=$(openssl x509 -in "$PKI/apiserver.crt" -text -noout | grep -A 1 "Subject Alternative Name" | tail -n 1 | sed -e 's/^[ \t]*//' -e 's/IP Address:/IP:/g')

TMP_EXT=$(mktemp)
cat << EXT > "$TMP_EXT"
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = $SAN
EXT

TMP_CSR=$(mktemp)
openssl x509 -x509toreq -in "$PKI/apiserver.crt" -signkey "$PKI/apiserver.key" -out "$TMP_CSR" 2>/dev/null
openssl x509 -req -in "$TMP_CSR" -CA "$PKI/ca.crt" -CAkey "$PKI/ca.key" -out "$PKI/apiserver.crt" -days 7 -extfile "$TMP_EXT" 2>/dev/null
rm -f "$TMP_CSR" "$TMP_EXT"
REMOTE_SCRIPT

