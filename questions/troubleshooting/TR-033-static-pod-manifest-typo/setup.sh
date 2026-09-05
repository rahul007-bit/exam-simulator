#!/usr/bin/env bash
set -e
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then source "$ENV_FILE"; fi
NODE_1=${NODE_1:-192.168.50.169}
SSH_USER=${SSH_USER:-root}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

# Verify manifests directory exists on control-plane
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$NODE_1" "test -d /etc/kubernetes/manifests" 2>/dev/null || true
