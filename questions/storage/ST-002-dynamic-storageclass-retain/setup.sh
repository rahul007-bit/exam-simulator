#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" delete sc fast-retain --ignore-not-found 2>/dev/null || true
