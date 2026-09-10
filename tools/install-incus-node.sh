#!/bin/bash
set -e

NODE_IP="$1"
if [ -z "$NODE_IP" ]; then
    echo "Usage: $0 <node-ip>"
    exit 1
fi

echo "=== Installing Incus on $NODE_IP ==="
ssh -o StrictHostKeyChecking=no root@$NODE_IP << 'REMOTESH'
set -e
echo "[1/4] Installing EPEL repository..."
rpm -Uvh --replacepkgs https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm 2>/dev/null || true

echo "[2/4] Adding NeelC Incus COPR repository..."
curl -sLo /etc/yum.repos.d/incus.repo https://copr.fedorainfracloud.org/coprs/neelc/incus/repo/epel-9/neelc-incus-epel-9.repo

echo "[3/4] Installing Incus package..."
yum install -y incus

echo "[4/4] Starting and enabling Incus service..."
systemctl enable --now incus
incus --version
echo "Incus successfully installed on $(hostname)!"
REMOTESH
