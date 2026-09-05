#!/usr/bin/env bash
set -e
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then source "$ENV_FILE"; fi
NODE_1=${NODE_1:-192.168.50.169}
NODE_2=${NODE_2:-192.168.50.188}
SSH_USER=${SSH_USER:-root}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

# Ensure node2 is running an older version (1.36.3) than control plane (1.36.4)
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$NODE_2" "
  if ! kubelet --version 2>/dev/null | grep -q '1.36.3'; then
    dnf downgrade -y kubeadm-1.36.3-150500.1.1.x86_64 kubelet-1.36.3-150500.1.1.x86_64 kubectl-1.36.3-150500.1.1.x86_64 --disableexcludes=kubernetes 2>/dev/null || true
    systemctl daemon-reload && systemctl restart kubelet 2>/dev/null || true
  fi
" 2>/dev/null || true

# Pre-cordon node2
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$NODE_1" "
  kubectl --kubeconfig=/etc/kubernetes/admin.conf cordon node2 2>/dev/null || true
" 2>/dev/null || true
