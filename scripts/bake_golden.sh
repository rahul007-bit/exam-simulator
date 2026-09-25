#!/bin/bash
# One-time golden image bake for the CKA kubeadm fleet — run on the mgmt node (10.8.0.15)
set -euo pipefail

echo "===> [1/7] Reset old artifacts"
incus delete -f k8s-base 2>/dev/null || true
incus image delete k8s-golden 2>/dev/null || true
incus network set incusbr0 ipv6.address none 2>/dev/null || true

echo "===> [2/7] Launch template container (image is cached, ~5s)"
incus launch images:debian/12 k8s-base \
  -c limits.cpu=2 -c limits.memory=2GiB -c limits.processes=1500 -c security.nesting=true

echo "===> [3/7] Wait for network"
OK=0
for i in $(seq 1 30); do
  if incus exec k8s-base -- bash -c "ping -c1 -W2 deb.debian.org >/dev/null 2>&1"; then OK=1; break; fi
  sleep 2
done
[ "$OK" = 1 ] || { echo "FATAL: no internet inside container"; exit 1; }

echo "===> [4/7] Install containerd + Kubernetes v1.30 packages"
incus exec k8s-base -- bash -s <<'EOF'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release containerd bash-completion vim git jq net-tools iproute2 ethtool
mkdir -p /etc/containerd
containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' > /etc/containerd/config.toml
systemctl restart containerd && systemctl enable containerd
mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
apt-get update -y
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
systemctl enable kubelet
echo "source <(kubectl completion bash)" >> /root/.bashrc
echo "alias k=kubectl" >> /root/.bashrc
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

echo "===> [5/7] Pre-pull official control-plane images"
incus exec k8s-base -- bash -s <<'EOF'
set -euo pipefail
SOCK="-r unix:///var/run/containerd/containerd.sock"
for ref in \
  registry.k8s.io/kube-apiserver:v1.30.0 \
  registry.k8s.io/kube-controller-manager:v1.30.0 \
  registry.k8s.io/kube-scheduler:v1.30.0 \
  registry.k8s.io/kube-proxy:v1.30.0 \
  registry.k8s.io/etcd:3.5.12-0 \
  registry.k8s.io/coredns/coredns:v1.11.1 \
  registry.k8s.io/pause:3.9 ; do
  echo "-- pulling $ref"
  crictl $SOCK pull "$ref" || { echo "FATAL: pull failed: $ref"; exit 1; }
done
crictl $SOCK images
EOF

echo "===> [6/7] Publish k8s-golden"
incus stop k8s-base
incus publish k8s-base --alias k8s-golden
incus delete -f k8s-base

echo "===> SUCCESS: k8s-golden baked with all control-plane images"
