#!/usr/bin/env bash
set -euo pipefail

echo "===> [1/6] Launching template container k8s-base on node1..."
incus delete -f k8s-base 2>/dev/null || true
incus launch debian-12-c k8s-base \
  -c limits.cpu=2 \
  -c limits.memory=2GiB \
  -c limits.processes=1500 \
  -c security.nesting=true < /dev/null

echo "===> [2/6] Waiting for network in k8s-base..."
for i in {1..15}; do
  if incus exec k8s-base -- ping -c 1 1.1.1.1 &>/dev/null; then
    echo "Network online."
    break
  fi
  sleep 1
done

echo "===> [3/6] Installing prerequisites, containerd, and Kubernetes packages inside k8s-base..."
incus exec k8s-base -- bash -s << 'EOF'
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Essential packages
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release containerd

# Configure containerd
mkdir -p /etc/containerd
containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' > /etc/containerd/config.toml
systemctl restart containerd
systemctl enable containerd

# Kubernetes repo setup (v1.30)
K8S_VERSION="v1.30"
mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL "https://pkgs.k8s.io/core:/stable:/${K8S_VERSION}/deb/Release.key" | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${K8S_VERSION}/deb/ /" > /etc/apt/sources.list.d/kubernetes.list

apt-get update -y
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

# Enable kubelet service
systemctl enable kubelet

# Pre-pull control plane images for instant cluster initialization
echo "Pre-pulling Kubernetes images..."
kubeadm config images pull --kubernetes-version "${K8S_VERSION}.0" || true

# Pre-install common tools for CKA candidates
apt-get install -y bash-completion vim git jq net-tools iproute2 ethtool

# Setup bash completion for kubectl and crictl
echo "source <(kubectl completion bash)" >> /root/.bashrc
echo "alias k=kubectl" >> /root/.bashrc
echo "complete -o default -F __start_kubectl k" >> /root/.bashrc

# Clean package caches to keep image slim
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

echo "===> [4/6] Stopping k8s-base..."
incus stop k8s-base

echo "===> [5/6] Publishing k8s-base as local image 'k8s-golden'..."
incus image delete k8s-golden 2>/dev/null || true
incus publish k8s-base --alias k8s-golden

echo "===> [6/6] Cleanup template container..."
incus delete -f k8s-base

echo "===> SUCCESS! k8s-golden image baked successfully on node1."
