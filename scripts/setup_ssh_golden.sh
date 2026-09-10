#!/usr/bin/env bash
set -euo pipefail

echo "Configuring SSH inside test-ssh..."
incus exec test-ssh -- bash -s << 'EOF'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y openssh-server openssh-client

# Host keys
ssh-keygen -A

# Candidate root SSH keypair (passwordless inter-node ssh)
mkdir -p -m 700 /root/.ssh
if [ ! -f /root/.ssh/id_ed25519 ]; then
  ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519
fi
cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# SSH daemon settings
mkdir -p /etc/ssh/sshd_config.d
cat << 'SSHEOF' > /etc/ssh/sshd_config.d/exam.conf
PermitRootLogin yes
PermitEmptyPasswords yes
PasswordAuthentication yes
SSHEOF

# SSH client defaults
mkdir -p /etc/ssh/ssh_config.d
cat << 'CLIEOF' > /etc/ssh/ssh_config.d/exam.conf
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
CLIEOF


# Empty root password for instant access
passwd -d root

# Restart and enable ssh
systemctl restart ssh
systemctl enable ssh
EOF

echo "Testing SSH locally inside test-ssh..."
incus exec test-ssh -- ssh -o StrictHostKeyChecking=no root@127.0.0.1 "echo SSH_SUCCESS"

echo "Re-publishing k8s-golden image..."
incus stop test-ssh
incus image delete k8s-golden
incus publish test-ssh --alias k8s-golden
incus delete -f test-ssh

echo "SUCCESS: k8s-golden re-published with OpenSSH enabled!"
