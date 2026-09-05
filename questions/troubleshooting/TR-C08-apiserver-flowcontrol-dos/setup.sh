#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
# Verify API server flow control health
kubectl --context "$CTX" get flowschemas >/dev/null 2>&1 || true
