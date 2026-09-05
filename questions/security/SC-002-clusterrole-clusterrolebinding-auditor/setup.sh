#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"

# Clean up any previous test artifacts
kubectl --context "$CTX" delete clusterrolebinding cluster-auditor-binding --ignore-not-found 2>/dev/null || true
kubectl --context "$CTX" delete clusterrole cluster-auditor --ignore-not-found 2>/dev/null || true
