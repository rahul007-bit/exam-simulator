#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="resilient-app"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Untaint control-plane node so multiple nodes are available to satisfy anti-affinity spread
kubectl --context "$CTX" taint node k3d-dev-server-0 node-role.kubernetes.io/control-plane:NoSchedule- 2>/dev/null || true

# Clean up previous deployment
kubectl --context "$CTX" delete deployment spread-web -n "$NS" --ignore-not-found 2>/dev/null || true
