#!/usr/bin/env bash
set -e

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[Error] .env file not found. Copy .env.example to .env and configure VM IPs and SSH key."
    exit 1
fi

source "$ENV_FILE"

echo "=== Checking SSH connectivity to kubeadm nodes ==="
SSH_USER=${SSH_USER:-root}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

for node in "$NODE_1" "$NODE_2"; do
    if [ -n "$node" ]; then
        echo -n "Connecting to $node ($SSH_USER)... "
        if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$node" "uname -n" >/dev/null 2>&1; then
            echo "✔ Connected ($(ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i "$SSH_KEY" "$SSH_USER@$node" "uname -n"))"
        else
            echo "✖ Failed to connect to $node"
        fi
    fi
done
