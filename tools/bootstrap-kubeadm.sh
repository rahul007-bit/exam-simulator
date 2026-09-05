#!/usr/bin/env bash
# ==============================================================================
# Automated Kubeadm Multi-Node Cluster Provisioning / Reset Script
# ==============================================================================
# Sets up a native, multi-node Kubeadm cluster for CKA cluster-architecture
# and node troubleshooting drills (pure CRI-O / containerd, zero KIND / k3d).
#
# Usage:
#   ./tools/bootstrap-kubeadm.sh
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${APP_DIR}/.env"

if [ -f "$ENV_FILE" ]; then
    log_info "Loading configuration from ${ENV_FILE}..."
    # shellcheck disable=SC1090
    source "$ENV_FILE"
fi

NODE_1=${NODE_1:-"192.168.1.57"}
NODE_2=${NODE_2:-"192.168.1.56"}
SSH_USER=${SSH_USER:-"root"}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}
POD_CIDR=${POD_CIDR:-"10.244.0.0/16"}
CRI_SOCKET=${CRI_SOCKET:-"unix:///var/run/crio/crio.sock"}
CNI_URL=${CNI_URL:-"https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml"}

SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10"
if [ -f "$SSH_KEY" ]; then
    SSH_CMD="ssh $SSH_OPTS -i $SSH_KEY"
else
    SSH_CMD="ssh $SSH_OPTS"
fi

log_info "Target Control Plane (node1): ${SSH_USER}@${NODE_1}"
log_info "Target Worker Node   (node2): ${SSH_USER}@${NODE_2}"

# 1. Verify Connectivity
log_info "Verifying SSH connectivity to nodes..."
$SSH_CMD "${SSH_USER}@${NODE_1}" "uname -n" >/dev/null || { log_error "Failed to reach ${NODE_1}"; exit 1; }
$SSH_CMD "${SSH_USER}@${NODE_2}" "uname -n" >/dev/null || { log_error "Failed to reach ${NODE_2}"; exit 1; }
log_success "SSH connectivity confirmed to both nodes."

# 2. Prepare Kernel & Container Runtime on both nodes
log_info "Configuring kernel modules, sysctl, and stopping conflicting firewalld/docker..."
for node in "$NODE_1" "$NODE_2"; do
    $SSH_CMD "${SSH_USER}@${node}" "
        systemctl stop firewalld 2>/dev/null || true
        systemctl disable firewalld 2>/dev/null || true
        systemctl stop docker 2>/dev/null || true
        systemctl disable docker 2>/dev/null || true
        systemctl stop docker.socket 2>/dev/null || true
        modprobe br_netfilter 2>/dev/null || true
        modprobe overlay 2>/dev/null || true
        sysctl -w net.bridge.bridge-nf-call-iptables=1 net.ipv4.ip_forward=1 >/dev/null
        systemctl restart crio 2>/dev/null || systemctl restart containerd 2>/dev/null || true
    "
done

# 3. Clean / Reset previous cluster state
log_info "Resetting existing kubeadm state on nodes..."
for node in "$NODE_1" "$NODE_2"; do
    $SSH_CMD "${SSH_USER}@${node}" "
        kubeadm reset -f --cri-socket=${CRI_SOCKET} >/dev/null 2>&1 || true
        rm -rf /etc/cni/net.d/* /etc/kubernetes/manifests/* /var/lib/etcd
    "
done
log_success "Nodes reset and cleaned."

# 4. Initialize Control Plane on node1
log_info "Initializing Control Plane on ${NODE_1}..."
INIT_OUT=$($SSH_CMD "${SSH_USER}@${NODE_1}" "
    kubeadm init \
        --apiserver-advertise-address=${NODE_1} \
        --pod-network-cidr=${POD_CIDR} \
        --cri-socket=${CRI_SOCKET} \
        --node-name=node1
")

# Extract join command
JOIN_CMD=$(echo "$INIT_OUT" | grep -A 2 "kubeadm join" | tr -d '\\\r\n' | sed -e 's/[[:space:]]\+/ /g')
if [ -z "$JOIN_CMD" ]; then
    log_error "Failed to extract kubeadm join command. Full output:\n$INIT_OUT"
    exit 1
fi
log_success "Control plane initialized successfully!"

# 5. Configure Kubeconfig & Deploy CNI on node1
log_info "Applying Flannel CNI network overlay..."
$SSH_CMD "${SSH_USER}@${NODE_1}" "
    mkdir -p /root/.kube
    cp -f /etc/kubernetes/admin.conf /root/.kube/config
    kubectl apply -f ${CNI_URL} >/dev/null
"
log_success "Flannel CNI deployed."

# 6. Join Worker Node (node2)
log_info "Joining worker node (${NODE_2}) to the cluster..."
$SSH_CMD "${SSH_USER}@${NODE_2}" "
    ${JOIN_CMD} --cri-socket=${CRI_SOCKET} --node-name=node2
"
log_success "Worker node joined."

# 7. Verification
log_info "Waiting for nodes to become Ready..."
sleep 8
$SSH_CMD "${SSH_USER}@${NODE_1}" "kubectl get nodes -o wide"

# 8. Copy admin kubeconfig locally if requested
LOCAL_KUBEDIR="${HOME}/.kube"
mkdir -p "$LOCAL_KUBEDIR"
$SSH_CMD "${SSH_USER}@${NODE_1}" "cat /etc/kubernetes/admin.conf" > "${LOCAL_KUBEDIR}/kubeadm-config"
log_success "Saved control-plane kubeconfig to ${LOCAL_KUBEDIR}/kubeadm-config"

echo ""
log_success "================================================================"
log_success " Kubeadm Multi-Node Cluster Bootstrapped Successfully!"
log_success " Control Plane: node1 (${NODE_1})"
log_success " Worker Node:   node2 (${NODE_2})"
log_success "================================================================"
