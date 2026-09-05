#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="redis-cluster"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete statefulset redis-cluster -n "$NS" --ignore-not-found 2>/dev/null || true
kubectl --context "$CTX" delete pvc -n "$NS" --all 2>/dev/null || true
