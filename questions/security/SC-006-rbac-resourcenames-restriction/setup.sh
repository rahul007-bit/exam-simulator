#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="rbac-fine-grained"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create secrets in the namespace
kubectl --context "$CTX" create secret generic allowed-creds -n "$NS" --from-literal=api-key=secret123 --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" create secret generic internal-creds -n "$NS" --from-literal=token=tok998877 --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Clean up previous role
kubectl --context "$CTX" delete role vault-restricted -n "$NS" --ignore-not-found 2>/dev/null || true
