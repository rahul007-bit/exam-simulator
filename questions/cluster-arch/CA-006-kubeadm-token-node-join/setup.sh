#!/usr/bin/env bash
set -e
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then source "$ENV_FILE"; fi
NODE_1=${NODE_1:-192.168.50.169}
NODE_3=${NODE_3:-192.168.50.170}
SSH_USER=${SSH_USER:-root}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

# Reset node3 so it is in an unjoined state ready for candidate to join
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$NODE_3" "
  kubeadm reset -f 2>/dev/null || true
  systemctl stop kubelet 2>/dev/null || true
  rm -rf /etc/kubernetes/kubelet.conf /etc/kubernetes/pki/ca.crt
" 2>/dev/null || true

# Remove node3 from cluster node list on node1
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$SSH_KEY" "$SSH_USER@$NODE_1" "
  kubectl --kubeconfig=/etc/kubernetes/admin.conf delete node node3 --ignore-not-found 2>/dev/null || true
" 2>/dev/null || true
