#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" create namespace cluster-admissions --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" create namespace webhook-system --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f "$SCRIPT_DIR/manifests/broken-webhook.yaml"
