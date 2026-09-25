#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" create namespace production-apps --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
AGENT_NODE=$(kubectl --context "$CTX" get nodes -l '!node-role.kubernetes.io/master,!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || kubectl --context "$CTX" get nodes -o jsonpath='{.items[0].metadata.name}')
if [ -n "$AGENT_NODE" ]; then
    kubectl --context "$CTX" cordon "$AGENT_NODE" 2>/dev/null || true
    kubectl --context "$CTX" taint nodes "$AGENT_NODE" maintenance=true:NoSchedule --overwrite 2>/dev/null || true
fi
kubectl --context "$CTX" apply -f "$SCRIPT_DIR/manifests/deploy.yaml"
