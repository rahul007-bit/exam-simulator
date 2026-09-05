#!/usr/bin/env bash
# ==============================================================================
# Link Simulator Platform Host & Candidate User to Kubeadm Cluster Nodes
# ==============================================================================
# Automates the complete SSH trust, sudo rights, and kubeconfig distribution:
#   1. Generates SSH key pairs for 'root' and 'exam' on the platform VM.
#   2. Configures /home/exam/.ssh/config and /root/.ssh/config (ssh node1, node2).
#   3. Authorizes platform keys on remote kubeadm nodes (NODE_1 and NODE_2).
#   4. Replicates sudo permissions (/etc/sudoers.d/exam).
#   5. Exports admin kubeconfig from NODE_1 to /home/exam/.kube/config (context: kubeadm-vms).
#   6. Verifies passwordless SSH access for candidate user 'exam'.
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

log_info "Target Control Plane (node1): ${SSH_USER}@${NODE_1}"
log_info "Target Worker Node   (node2): ${SSH_USER}@${NODE_2}"

# 1. Ensure candidate user 'exam' exists with restricted permissions (matching reference 10.8.0.15)
log_info "Ensuring candidate user 'exam' exists with restricted privileges..."
if ! id -u exam >/dev/null 2>&1; then
    useradd -m -s /bin/bash -u 1000 exam 2>/dev/null || useradd -m -s /bin/bash exam
fi
usermod -aG docker exam 2>/dev/null || true
gpasswd -d exam sudo 2>/dev/null || true

# Strictly whitelisted sudo for candidate examctl commands only (prevents host tampering)
cat << 'EOF' > /etc/sudoers.d/examctl
exam ALL=(root) NOPASSWD: /root/cka-labs/labctl tasks, /root/cka-labs/labctl status, /root/cka-labs/labctl next, /root/cka-labs/labctl prev, /root/cka-labs/labctl jump *, /root/cka-labs/labctl flag, /root/cka-labs/labctl flag *, /root/cka-labs/labctl unflag, /root/cka-labs/labctl unflag *
EOF
chmod 0440 /etc/sudoers.d/examctl
rm -f /etc/sudoers.d/exam

# 2. Ensure SSH Key Pairs Exist for root and exam
log_info "Generating SSH keys if missing..."
install -d -m 0700 -o root -g root /root/.ssh
if [ ! -f /root/.ssh/id_ed25519 ] && [ ! -f /root/.ssh/id_rsa ]; then
    ssh-keygen -t ed25519 -N '' -f /root/.ssh/id_ed25519 -q
fi

install -d -m 0700 -o exam -g exam /home/exam/.ssh
if [ ! -f /home/exam/.ssh/id_ed25519 ]; then
    su - exam -c "ssh-keygen -t ed25519 -N '' -f /home/exam/.ssh/id_ed25519 -q"
fi

# 3. Configure ~/.ssh/config for both root and exam
log_info "Writing node aliases (ssh node1, node2) into ~/.ssh/config..."
SSH_CONFIG_CONTENT="Host node1
    HostName ${NODE_1}
    User ${SSH_USER}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR

Host node2
    HostName ${NODE_2}
    User ${SSH_USER}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
"

EXAM_USER="${EXAM_USER:-exam}"
ADMIN_USER="${ADMIN_USER:-${SUDO_USER:-}}"

echo "$SSH_CONFIG_CONTENT" > /root/.ssh/config
chmod 0600 /root/.ssh/config

if id -u "${EXAM_USER}" >/dev/null 2>&1; then
    install -d -m 0700 -o "${EXAM_USER}" -g "${EXAM_USER}" "/home/${EXAM_USER}/.ssh"
    echo "$SSH_CONFIG_CONTENT" > "/home/${EXAM_USER}/.ssh/config"
    chmod 0600 "/home/${EXAM_USER}/.ssh/config"
    chown -R "${EXAM_USER}:${EXAM_USER}" "/home/${EXAM_USER}/.ssh"
fi

# Collect public keys to distribute
ROOT_PUB=$(cat /root/.ssh/id_ed25519.pub 2>/dev/null || cat /root/.ssh/id_rsa.pub 2>/dev/null || true)
EXAM_PUB=$(cat "/home/${EXAM_USER}/.ssh/id_ed25519.pub" 2>/dev/null || cat "/home/${EXAM_USER}/.ssh/id_rsa.pub" 2>/dev/null || true)
ADMIN_PUB=""
if [ -n "${ADMIN_USER}" ] && [ -d "/home/${ADMIN_USER}/.ssh" ]; then
    ADMIN_PUB=$(cat "/home/${ADMIN_USER}/.ssh/id_ed25519.pub" 2>/dev/null || cat "/home/${ADMIN_USER}/.ssh/id_rsa.pub" 2>/dev/null || true)
fi

# 4. Distribute Public Keys to Remote Nodes
log_info "Distributing public keys to ${NODE_1} and ${NODE_2}..."
SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=8"
CANDIDATE_KEYS=("$SSH_KEY" "/root/.ssh/id_rsa" "/root/.ssh/id_ed25519")
if [ -n "${ADMIN_USER}" ]; then
    CANDIDATE_KEYS+=("/home/${ADMIN_USER}/.ssh/id_ed25519" "/home/${ADMIN_USER}/.ssh/id_rsa")
fi

for test_key in "" "${CANDIDATE_KEYS[@]}"; do
    [ -n "$test_key" ] && [ ! -f "$test_key" ] && continue
    KEY_ARG=""
    [ -n "$test_key" ] && KEY_ARG="-i $test_key"
    
    if ssh $SSH_OPTS $KEY_ARG "${SSH_USER}@${NODE_1}" "uname -n" >/dev/null 2>&1; then
        ssh $SSH_OPTS $KEY_ARG "${SSH_USER}@${NODE_1}" "
            mkdir -p /root/.ssh
            chmod 700 /root/.ssh
            [ -n '${ROOT_PUB}' ] && echo '${ROOT_PUB}' >> /root/.ssh/authorized_keys
            [ -n '${EXAM_PUB}' ] && echo '${EXAM_PUB}' >> /root/.ssh/authorized_keys
            [ -n '${ADMIN_PUB}' ] && echo '${ADMIN_PUB}' >> /root/.ssh/authorized_keys
            sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
            chmod 600 /root/.ssh/authorized_keys

            # Propagate trust directly to node2 from node1
            ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@${NODE_2} '
                mkdir -p /root/.ssh
                [ -n \"${ROOT_PUB}\" ] && echo \"${ROOT_PUB}\" >> /root/.ssh/authorized_keys
                [ -n \"${EXAM_PUB}\" ] && echo \"${EXAM_PUB}\" >> /root/.ssh/authorized_keys
                [ -n \"${ADMIN_PUB}\" ] && echo \"${ADMIN_PUB}\" >> /root/.ssh/authorized_keys
                sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
                chmod 600 /root/.ssh/authorized_keys
            ' 2>/dev/null || true
        "
        log_success "Successfully authorized platform keys on ${NODE_1} and ${NODE_2}."
        break
    fi
done

# 5. Fetch kubeconfig from node1 and set up context for candidate
log_info "Pulling cluster kubeconfig from node1..."
if ssh $SSH_OPTS "${SSH_USER}@${NODE_1}" "test -f /etc/kubernetes/admin.conf" >/dev/null 2>&1; then
    install -d -m 0700 -o exam -g exam /home/exam/.kube
    install -d -m 0700 -o root -g root /root/.kube

    RAW_CONF=$(ssh $SSH_OPTS "${SSH_USER}@${NODE_1}" "cat /etc/kubernetes/admin.conf")
    
    # Update server IP to NODE_1 in case it is bound to 127.0.0.1
    EDITED_CONF=$(echo "$RAW_CONF" | sed -e "s|server: https://127.0.0.1:6443|server: https://${NODE_1}:6443|g" \
                                         -e "s|server: https://localhost:6443|server: https://${NODE_1}:6443|g" \
                                         -e "s|kubernetes-admin@kubernetes|kubeadm-vms|g")

    echo "$EDITED_CONF" > /root/.kube/config
    echo "$EDITED_CONF" > /home/exam/.kube/config
    chown exam:exam /home/exam/.kube/config
    log_success "Installed kubeconfig to /home/exam/.kube/config (context: kubeadm-vms)."
fi

# 6. Verify passwordless access as user 'exam'
log_info "Verifying passwordless SSH access as candidate user 'exam'..."
NODE1_RES=$(su - exam -c "ssh -o ConnectTimeout=5 node1 'uname -n; whoami'" 2>/dev/null || echo "FAILED")
NODE2_RES=$(su - exam -c "ssh -o ConnectTimeout=5 node2 'uname -n; whoami'" 2>/dev/null || echo "FAILED")

echo ""
echo "=========================================================================="
log_success "Node Linking and Candidate Access Check:"
echo "  • Candidate 'exam' -> ssh node1: [${NODE1_RES}]"
echo "  • Candidate 'exam' -> ssh node2: [${NODE2_RES}]"
echo "=========================================================================="
