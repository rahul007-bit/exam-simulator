#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
# CoreDNS verification scenario; candidate must ensure Corefile uses forward . /etc/resolv.conf
kubectl --context "$CTX" get cm -n kube-system coredns >/dev/null 2>&1 || true
