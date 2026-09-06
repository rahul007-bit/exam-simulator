#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="web-cluster"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Label the worker node with zone-1 and disk=ssd so the pod can schedule
WORKER_NODE=$(kubectl --context "$CTX" get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$WORKER_NODE" ]; then
    kubectl --context "$CTX" label node "$WORKER_NODE" topology.kubernetes.io/zone=zone-1 disk=ssd --overwrite 2>/dev/null || true
fi

# Clean up previous pod
kubectl --context "$CTX" delete pod affinity-pod -n "$NS" --ignore-not-found 2>/dev/null || true
