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

# Revert apiserver.crt back to original 1-year certificate or renew if original not available
ssh $SSH_OPTS "$SSH_USER@$NODE_1" bash << 'REMOTE_SCRIPT'
PKI="/etc/kubernetes/pki"
if [ -f "$PKI/apiserver.crt.orig" ]; then
    cp "$PKI/apiserver.crt.orig" "$PKI/apiserver.crt"
    rm -f "$PKI/apiserver.crt.orig"
else
    kubeadm certs renew apiserver 2>/dev/null || true
fi
REMOTE_SCRIPT
