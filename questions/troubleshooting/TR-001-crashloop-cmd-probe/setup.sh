#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" create namespace checkout-prod --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f "$SCRIPT_DIR/manifests/app.yaml"
