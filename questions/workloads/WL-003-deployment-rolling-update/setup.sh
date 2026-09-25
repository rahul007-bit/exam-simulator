#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="order-services"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete deployment payment-api -n "$NS" --ignore-not-found 2>/dev/null || true
