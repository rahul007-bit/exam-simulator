#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CTX="${KUBECTL_CONTEXT:-k3d-cka}"

# Remove label if present from previous runs
kubectl --context "$CTX" label nodes --all disk- 2>/dev/null || true

kubectl --context "$CTX" create namespace analytics --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete pod analytics-worker -n analytics --ignore-not-found 2>/dev/null || true
kubectl --context "$CTX" apply -f "$SCRIPT_DIR/manifests/pod.yaml"
