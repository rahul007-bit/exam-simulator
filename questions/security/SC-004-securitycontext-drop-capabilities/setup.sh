#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="net-tools"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete pod net-monitor -n "$NS" --ignore-not-found 2>/dev/null || true
kubectl --context "$CTX" delete pod net-tool -n "$NS" --ignore-not-found 2>/dev/null || true
